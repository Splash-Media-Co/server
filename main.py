# Import the server
from cloudlink import server

# Import JSON Web token handler
import jwt  # noqa: F401

# Import cryptography
import bcrypt  # noqa: F401

# Import logging helpers
from logs import Info, Warning, Debug, Error, Critical  # noqa: F401

# Import time handlers
import time  # noqa: F401
import datetime  # noqa: F401

# Import DB handler
from oceandb import OceanDB  # noqa: F401

# Import requests and json libraries
import requests
import json

# Import UUID helpers
import uuid

# Import protocols
from cloudlink.server.protocols import clpv4, scratch

# Import signal handling, sys, and os
import signal
import sys
import os

# Instantiate the server object
server = server()


# create this function
def timestampsort(e):
    return e[1]


# Instantiate the OwODB object
db = OceanDB("db")
# Set logging level
server.logging.basicConfig(
    level=server.logging.DEBUG  # See python's logging library for details on logging levels.
)

# Load protocols
clpv4 = clpv4(server)
scratch = scratch(server)

# Load secret
KEY = os.getenv("KEY")

authenticated_clients = []

SETTINGS = {"bridge_enabled": True}


@server.on_connect
async def on_connect(client):
    Info(f"Client {str(client.id)} connected")


@server.on_disconnect
async def on_disconnect(client):
    Info(f"Client {str(client.id)} disconnected")
    if client.id in authenticated_clients:
        authenticated_clients.remove(client.id)


"""
type: int containing post mode (see Notes)
p: string, content of the post
t: Object containing time details + timestamp
post_id: id of the post (made srv-side, don't send)
"""


@server.on_command(cmd="post", schema=clpv4.schema)
async def post(client, message):
    Info(
        f"Client {str(client)} sent message: Post: {str(message["val"]["p"])}, mode: {str(message["val"]["type"])}, timestamp: {str(message["val"]["t"])}"
    )


@server.on_command(cmd="direct", schema=clpv4.schema)
async def direct(client, message):
    if message["val"]["cmd"] == "Not JSON!":
        Info(
            "Ignoring \"Not JSON!\" message."
        )
        return
    match str(message["val"]["cmd"]):
        case "post":
            match str(message["val"]["val"]["type"]):
                case "send":
                    if client.id not in authenticated_clients:
                        try:
                            server.send_packet_unicast(
                                client,
                                {
                                    "cmd": "gmsg",
                                    "val": {
                                        "cmd": "status",
                                        "val": {
                                            "message": "Not authenticated",
                                            "username": client.username,
                                        },
                                    },
                                },
                            )
                        except Exception as e:
                            Error(
                                f"Error sending message to client {str(client)}: "
                                + str(e)
                            )
                    else:
                        Info(
                            f"Client {str(client.username)} sent message: Post: {str(message["val"]["val"]["p"])}, mode: {str(message["val"]["val"]["type"])}, timestamp: {float(time.time())}"
                        )
                        uid = str(uuid.uuid4())
                        db.insert_data(
                            "posts",
                            (
                                str(client.username),
                                float(time.time()),
                                uid,
                                str(message["val"]["val"]["p"]),
                                False,
                                "home",
                                str(message["val"]["val"]["type"]),
                            ),
                        )
                        server.send_packet_multicast(
                            server.clients_manager.clients,
                            {
                                "cmd": "gmsg",
                                "val": {
                                    "cmd": "rpost",
                                    "val": {
                                        "author": client.username,
                                        "post_content": str(message["val"]["val"]["p"]),
                                        "uid": uid,
                                    },
                                },
                            },
                        )
                    if SETTINGS["bridge_enabled"]:
                        url = "https://webhooks.meower.org/post/home"

                        payload = json.dumps(
                            {
                                "username": "SplashBridge_",
                                "post": client.username
                                + ": "
                                + str(message["val"]["val"]["p"]).strip(),
                            }
                        )
                        headers = {"Content-Type": "application/json"}

                        response = requests.request(
                            "POST", url, headers=headers, data=payload, timeout=5
                        )
                        Info(
                            "Response from Meower: "
                            + "No response."
                            + ", statuscode: "
                            + str(response.status_code),
                        )
                case "delete":
                    if client.id not in authenticated_clients:
                        try:
                            server.send_packet_unicast(
                                client,
                                {
                                    "cmd": "gmsg",
                                    "val": {
                                        "cmd": "status",
                                        "val": {
                                            "message": "Not authenticated",
                                            "username": client.username,
                                        },
                                    },
                                },
                            )
                        except Exception as e:
                            Error(
                                f"Error sending message to client {str(client)}: "
                                + str(e)
                            )
                    else:
                        Info(
                            f"Client {str(client.id)} sent message: UID: {str(message["val"]["val"]["uid"])}, mode: {str(message["val"]["val"]["type"])}, timestamp: {float(time.time())}"
                        )
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
                                    "val": {"uid": str(message["val"]["val"]["uid"])},
                                },
                            },
                        )
        case "auth":
            USER = message["val"]["val"]["username"]
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
                    authenticated_clients.append(client.id)
                else:
                    server.send_packet_unicast(
                        client,
                        {
                            "cmd": "gmsg",
                            "val": {
                                "cmd": "status",
                                "val": {
                                    "message": "Invalid password",
                                    "username": USER,
                                },
                            },
                        },
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
        case "retrieve":
            match str(message["val"]["val"]["type"]):
                case "latest":
                    chat_id = message["val"]["val"]["c"]
                    offset = message["val"]["val"]["o"]
                    Info(
                        f"Client {str(client.id)} retrieved latest messages: chat_id: {chat_id}, offset: {offset}"
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
            USER = message["val"]["val"]["username"]
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
                except Exception as e:
                    Error(
                        f"Error creating account for client {str(client.id)}: "
                        + str(e)
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


@server.on_message
async def msg(client, message):
    Info(str(message))


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
