# Import the server
from cloudlink import server

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

# Import signal handling and sys
import signal
import sys

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

SETTINGS = {
    "bridge_enabled": True
}

@server.on_connect
async def on_connect(client):
    Info(f"Client {str(client)} connected")


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
                    Info(
                        f"Client {str(client.id)} sent message: Post: {str(message["val"]["val"]["p"])}, mode: {str(message["val"]["val"]["type"])}, timestamp: {float(time.time())}"
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

                        payload = json.dumps({
                            "username": "SplashBridge",
                            "post": client.username + ": " + str(message["val"]["val"]["p"]).strip()
                        })
                        headers = {
                            'Content-Type': 'application/json'
                        }

                        response = requests.request("POST", url, headers=headers, data=payload, timeout=5)
                        Info("Response from Meower: ", str(response.json()) if response.json() else "No response.", ", statuscode: ", str(response.status_code))
                case "delete":
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
