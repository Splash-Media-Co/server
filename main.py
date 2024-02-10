# Import the server
import datetime  # noqa: F401
import json
import os

# Import signal handling, sys, and os
import signal
import sys

# Import time handlers
import time  # noqa: F401

# Import UUID helpers
import uuid

# Import cryptography
import bcrypt  # noqa: F401

# Import JSON Web token handler
import jwt  # noqa: F401

# Import paralelized tasks helper
import concurrent.futures  # noqa: F401


# Import requests and json libraries
import requests
from cloudlink import server

# Import protocols
from cloudlink.server.protocols import clpv4, scratch

# Import logging helpers, OceanAudit, and utils
from logs import Critical, Debug, Error, Info, Warning  # noqa: F401
from oceanaudit import OceanAuditLogger
from utils import WebSocketRateLimiter, isAuthenticated

# Import DB handler
from oceandb import OceanDB  # noqa: F401

# Instantiate the server object
server = server()

# Instantiate ratelimiter
ratelimiter = WebSocketRateLimiter(5, 1)


# define timestamp sorting
def timestampsort(e):
    return e[1]


# define paralelized POST request
def post(url, token=None):
    """Sends a POST request to the specified URL.

    Args:
        url (str): The URL to send the request to.
        token (str, optional): The authorization token.

    Returns:
        None
    """
    headers = {}
    if token:
        headers['Authorization'] = 'Bearer ' + token

    response = requests.post(url, headers=headers, timeout=5)


# Instantiate the OceanDB object and OceanAuditLogger object
db = OceanDB("db")
audit = OceanAuditLogger()

# Set logging level
server.logging.basicConfig(
    level=server.logging.DEBUG  # See python's logging library for details on logging levels.
)

# Load protocols
clpv4 = clpv4(server)
scratch = scratch(server)

# Load secrets
KEY = os.getenv("KEY")
TOKEN = os.getenv("TOKEN")

authenticated_clients = []
authenticated_client_usernames = []

SETTINGS = {"bridge_enabled": True}


@server.on_connect
async def on_connect(client):
    Info(f"Client {str(client.id)} connected")


@server.on_disconnect
async def on_disconnect(client):
    Info(f"Client {str(client.id)} disconnected")
    if client.id in authenticated_clients:
        authenticated_clients.remove(client.id)


@server.on_command(cmd="direct", schema=clpv4.schema)
async def direct(client, message):
    if not await ratelimiter.acquire(client.id):
        Info("Ignoring rate limit")
        try:
            server.send_packet_unicast(
                client,
                {
                    "cmd": "gmsg",
                    "val": {
                        "cmd": "status",
                        "val": {
                            "message": "Ratelimited.",
                            "username": client.username,
                        },
                    },
                },
            )
            audit.log_action(
                "ratelimit",
                client.username,
                "User hitted rate limit",
            )
        except Exception as e:
            Error(f"Error sending message to client {str(client)}: " + str(e))
            audit.log_action(
                "send_to_client_fail",
                client.username,
                f"Tried to post to client with error {e}",
            )
        return
    if message["val"] == "Not JSON!":
        Info('Ignoring "Not JSON!" message.')
        return
    match str(message["val"]["cmd"]):
        case "post":
            match str(message["val"]["val"]["type"]):
                case "send":
                    if not await isAuthenticated(server, client, authenticated_clients):
                        return
                    else:
                        uid = str(uuid.uuid4())
                        try:
                            attachment = str(message["val"]["val"]["attachment"])
                        except KeyError:
                            attachment = ""
                        db.insert_data(
                            "posts",
                            (
                                str(
                                    authenticated_client_usernames[
                                        authenticated_clients.index(client.id)
                                    ]
                                ),
                                float(time.time()),
                                uid,
                                str(message["val"]["val"]["p"]),
                                False,
                                "home",
                                str(message["val"]["val"]["type"]),
                                attachment,
                                "NULL",
                            ),
                        )
                        server.send_packet_multicast(
                            server.clients_manager.clients,
                            {
                                "cmd": "gmsg",
                                "val": {
                                    "cmd": "rpost",
                                    "val": {
                                        "author": authenticated_client_usernames[
                                            authenticated_clients.index(client.id)
                                        ],
                                        "post_content": str(message["val"]["val"]["p"]),
                                        "uid": uid,
                                        "attachment": attachment,
                                    },
                                },
                            },
                        )
                        audit.log_action(
                            "post",
                            authenticated_client_usernames[
                                authenticated_clients.index(client.id)
                            ],
                            f"User posted {str(message["val"]["val"]["p"])}",
                        )
                        if SETTINGS["bridge_enabled"]:
                            url = "https://splashpost.vercel.app/home/"
                            payload = (
                                authenticated_client_usernames[
                                    authenticated_clients.index(client.id)
                                ]
                                + ": "
                                + str(message["val"]["val"]["p"]).strip()
                                + (
                                    ""
                                    if attachment == ""
                                    else str(f"[image: {attachment}]")
                                ),
                            )

                            with concurrent.futures.ProcessPoolExecutor() as executor:
                                executor.submit(post, url + str(payload[0]), TOKEN)
                case "delete":
                    if not await isAuthenticated(server, client, authenticated_clients):
                        return
                    else:
                        selection = db.select_data(
                            "posts",
                            conditions={"uid": str(message["val"]["val"]["uid"])},
                        )
                        print(selection)
                        print(selection[0][0])
                        print(
                            authenticated_client_usernames[
                                authenticated_clients.index(client.id)
                            ]
                        )
                        if selection:
                            if str(selection[0][0]) == str(
                                authenticated_client_usernames[
                                    authenticated_clients.index(client.id)
                                ]
                            ):
                                db.update_data(
                                    "posts",
                                    {"isDeleted": True},
                                    {"uid": str(message["val"]["val"]["uid"])},
                                )
                                server.send_packet_multicast(
                                    server.clients_manager.clients,
                                    {
                                        "cmd": "gmsg",
                                        "val": {
                                            "cmd": "rdel",
                                            "val": {
                                                "uid": str(message["val"]["val"]["uid"])
                                            },
                                        },
                                    },
                                )
                                audit.log_action(
                                    "delete",
                                    authenticated_client_usernames[
                                        authenticated_clients.index(client.id)
                                    ],
                                    f"User deleted post with UID {str(message["val"]["val"]["uid"])}",
                                )
                            else:
                                server.send_packet_unicast(
                                    client,
                                    {
                                        "cmd": "gmsg",
                                        "val": {
                                            "cmd": "status",
                                            "val": {
                                                "message": "Not authorized",
                                                "username": authenticated_client_usernames[
                                                    authenticated_clients.index(
                                                        client.id
                                                    )
                                                ],
                                            },
                                        },
                                    },
                                )
                                audit.log_action(
                                    "delete_fail",
                                    authenticated_client_usernames[
                                        authenticated_clients.index(client.id)
                                    ],
                                    f"User tried to delete a post with UID {str(message["val"]["val"]["uid"])} that doesn't belong to their account",
                                )
                        else:
                            server.send_packet_unicast(
                                client,
                                {
                                    "cmd": "gmsg",
                                    "val": {
                                        "cmd": "status",
                                        "val": {
                                            "message": "Post not found",
                                            "username": authenticated_client_usernames[
                                                authenticated_clients.index(client.id)
                                            ],
                                        },
                                    },
                                },
                            )
                            audit.log_action(
                                "delete_fail",
                                authenticated_client_usernames[
                                    authenticated_clients.index(client.id)
                                ],
                                f"User tried to delete a post with UID {str(message["val"]["val"]["uid"])} that didn't exist",
                            )
                case "edit":
                    if not await isAuthenticated(server, client, authenticated_clients):
                        return
                    else:
                        selection = db.select_data(
                            "posts",
                            conditions={"uid": str(message["val"]["val"]["uid"])},
                        )
                        if selection:
                            if str(selection[0][0]) != str(
                                authenticated_client_usernames[
                                    authenticated_clients.index(client.id)
                                ]
                            ):
                                server.send_packet_unicast(
                                    client,
                                    {
                                        "cmd": "gmsg",
                                        "val": {
                                            "cmd": "status",
                                            "val": {
                                                "message": "Not authorized",
                                                "username": authenticated_client_usernames[
                                                    authenticated_clients.index(
                                                        client.id
                                                    )
                                                ],
                                            },
                                        },
                                    },
                                )
                                audit.log_action(
                                    "edit_fail",
                                    authenticated_client_usernames[
                                        authenticated_clients.index(client.id)
                                    ],
                                    f"User tried to edit a post with UID {str(message["val"]["val"]["uid"])} that doesn't belong to their account",
                                )
                            else:
                                db.update_data(
                                    "posts",
                                    {
                                        "content": str(message["val"]["val"]["edit"]),
                                        "edited_at": time.time(),
                                    },
                                    {"uid": str(message["val"]["val"]["uid"])},
                                )
                                server.send_packet_multicast(
                                    server.clients_manager.clients,
                                    {
                                        "cmd": "gmsg",
                                        "val": {
                                            "cmd": "redit",
                                            "val": {
                                                "uid": str(
                                                    message["val"]["val"]["uid"]
                                                ),
                                                "edit": str(
                                                    message["val"]["val"]["edit"]
                                                ),
                                            },
                                        },
                                    },
                                )
                                audit.log_action(
                                    "edit",
                                    authenticated_client_usernames[
                                        authenticated_clients.index(client.id)
                                    ],
                                    f"User edited a post with UID {str(message["val"]["val"]["uid"])}",
                                )
                        else:
                            server.send_packet_unicast(
                                client,
                                {
                                    "cmd": "gmsg",
                                    "val": {
                                        "cmd": "status",
                                        "val": {
                                            "message": "Post not found",
                                            "username": authenticated_client_usernames[
                                                authenticated_clients.index(client.id)
                                            ],
                                        },
                                    },
                                },
                            )
                            audit.log_action(
                                "edit_fail",
                                client.username,
                                f"User tried to edit a post with UID {str(message["val"]["val"]["uid"])} that didn't exist",
                            )

        case "auth":
            USER = client.username
            PASSWORD = message["val"]["val"]["pswd"]

            selection = db.select_data("users", {"username": USER})
            print(str(selection))
            if selection:
                if bcrypt.checkpw(bytes(PASSWORD, "utf-8"), selection[0][9]):
                    Info(f"Client {str(client.username)} logged in")
                    token = jwt.encode(
                        {"username": USER},
                        str(KEY),  # type: ignore
                        algorithm="HS256",
                    )
                    server.send_packet_unicast(
                        client,
                        {
                            "cmd": "pmsg",
                            "val": {
                                "cmd": "auth",
                                "val": {
                                    "token": token,
                                    "username": USER,
                                },
                            },
                        },
                    )
                    audit.log_action(
                        "auth",
                        client.username,
                        "User authenticated!",
                    )
                    authenticated_clients.append(client.id)
                    authenticated_client_usernames.append(client.username)
                else:
                    server.send_packet_unicast(
                        client,
                        {
                            "cmd": "pmsg",
                            "val": {
                                "cmd": "status",
                                "val": {
                                    "message": "Invalid password",
                                    "username": USER,
                                },
                            },
                        },
                    )
                    audit.log_action(
                        "auth_fail",
                        client.username,
                        "User failed to auth because of invalid password",
                    )
            else:
                server.send_packet_unicast(
                    client,
                    {
                        "cmd": "direct",
                        "val": {
                            "cmd": "status",
                            "val": {
                                "message": "User doesn't exist",
                                "username": USER,
                            },
                        },
                    },
                )
                audit.log_action(
                    "auth_fail",
                    client.username,
                    f"User tried to log into {USER} but failed because it doesn't exist",
                )
        case "retrieve":
            match str(message["val"]["val"]["type"]):
                case "latest":
                    chat_id = message["val"]["val"]["c"]
                    offset = message["val"]["val"]["o"]
                    Info(
                        f"Client {str(client.id)} retrieved latest messages: chat_id: {chat_id}, offset: {offset}"
                    )
                    audit.log_action(
                        "retrieve",
                        client.username,
                        f"User retrieved posts with chat id of {chat_id} and offset of {offset}",
                    )
                    posts = db.select_data("posts", conditions={"post_origin": chat_id})
                    # print(posts)
                    returnposts = []
                    for i in range(len(posts)):
                        returnposts.append(posts[-i + 1])
                        if i == 19:
                            break
                    server.send_packet_unicast(
                        client,
                        {
                            "cmd": "pmsg",
                            "val": {
                                "cmd": "posts",
                                "val": {"posts": returnposts},
                            },
                        },
                    )
                    returnposts.sort(key=timestampsort, reverse=False)
        case "genaccount":
            USER = client.username
            PASSWORD = message["val"]["val"]["pswd"]

            selection = db.select_data("users", {"username": USER})

            if not selection:
                try:
                    pt_pswd = bytes(PASSWORD, "utf-8")

                    salt = bcrypt.gensalt()  # Generate a salt
                    hashed_password = bcrypt.hashpw(pt_pswd, salt)

                    uid = str(uuid.uuid4())
                    db.insert_data(
                        "users",
                        (
                            str(USER),
                            float(time.time()),
                            uid,
                            False,
                            "",
                            1,
                            float(time.time()),
                            json.dumps([]),
                            json.dumps([]),
                            hashed_password,
                        ),
                    )

                    server.send_packet_unicast(
                        client,
                        {
                            "cmd": "pmsg",
                            "val": {
                                "cmd": "createdaccount",
                                "val": "Welcome to Splash!",
                            },
                        },
                    )
                    audit.log_action(
                        "created_account",
                        client.username,
                        f"User created account {str(USER)}",
                    )
                except Exception as e:
                    Error(
                        f"Error creating account for client {str(client.id)}: " + str(e)
                    )
                    audit.log_action(
                        "create_account_fail",
                        client.username,
                        f"Failed to create account with username {str(USER)}: {str(e)}",
                    )
                    server.send_packet_unicast(
                        client,
                        {
                            "cmd": "pmsg",
                            "val": {
                                "cmd": "status",
                                "val": {
                                    "message": "An unexpected error occurred.",
                                    "username": USER,
                                },
                            },
                        },
                    )

            else:
                server.send_packet_unicast(
                    client,
                    {
                        "cmd": "pmsg",
                        "val": {
                            "cmd": "status",
                            "val": {
                                "message": "User already exists.",
                                "username": USER,
                            },
                        },
                    },
                )
                audit.log_action(
                    "create_account_fail",
                    client.username,
                    f"Failed to create account with username {str(USER)} because it already exists",
                )


"""@server.on_message
async def msg(client, message):
    Info(str(message))
"""

Info("Started server!")


def signal_handler(sig, frame):
    print("\n")
    Error(f"Received signal {sig}. Script is terminating.")
    db.close()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

# Start the server!
server.run()
