# Import the server
from cloudlink import server

# Import JSON Web token handler
import jwt  # noqa: F401

# Import cryptography
from cryptography.fernet import Fernet  # noqa: F401

# Import logging helpers
from logs import Info, Warning, Debug, Error, Critical  # noqa: F401

# Import time handlers
import time  # noqa: F401
import datetime  # noqa: F401

# Import DB handler
from oceandb import OceanDB  # noqa: F401

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
    match str(message["val"]["cmd"]):
        case "post":
            match str(message["val"]["val"]["type"]):
                case "send":
                    if client.id not in authenticated_clients:
                        try:
                            await server.send_packet_unicast(
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
                        await server.send_packet_multicast(
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
                case "delete":
                    if client.id not in authenticated_clients:
                        try:
                            await server.send_packet_unicast(
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
                        await server.send_packet_multicast(
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
                if Fernet(KEY).decrypt(str(selection[0][9])) == PASSWORD:
                    Info(f"Client {str(client.username)} logged in")
                    token = jwt.encode(
                        {"username": USER, "password": selection[0][9]},
                        KEY,
                        algorithm="HS256",
                    )
                    await server.send_packet_unicast(
                        client,
                        {
                            "cmd": "auth",
                            "val": {
                                "token": token,
                                "username": USER,
                            },
                        },
                    )
                    authenticated_clients.append(client.id)
                else:
                    await server.send_packet_unicast(
                        client,
                        {
                            "cmd": "status",
                            "val": {
                                "message": "Invalid password",
                                "username": USER,
                            },
                        },
                    )
            else:
                await server.send_packet_unicast(
                    client,
                    {
                        "cmd": "status",
                        "val": {
                            "message": "User doesn't exist",
                            "username": USER,
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
server.run(ip="127.0.0.1", port=3000)
