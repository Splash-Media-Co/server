# Import the server
from cloudlink import server

# Import multiprocessing
from multiprocessing import Process, Queue  # noqa: F401

# Import meowerbot
from MeowerBot import Bot, cbids

# Import logging helpers
from logs import Info, Warning, Debug, Error, Critical  # noqa: F401

# Import time handlers
import time  # noqa: F401
import datetime  # noqa: F401

# Import DB handler
from oceandb import OceanDB

# Import requests and json libraries
import requests  # noqa: F401
import json  # noqa: F401

# Import UUID helpers
import uuid

# Import protocols
from cloudlink.server.protocols import clpv4, scratch

# Import signal handling, sys, and os
import signal
import sys
import os

# Import dotenv
from dotenv import load_dotenv

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

# Load protocols and dotenv
clpv4 = clpv4(server)
scratch = scratch(server)
load_dotenv()

SETTINGS = {"bridge_enabled": True}


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
                    try:
                        attachment = str(message["val"]["val"]["attachment"])
                    except KeyError:
                        attachment = ""
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
                            attachment,
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
                                    "attachment": attachment,
                                },
                            },
                        },
                    )
                    if SETTINGS["bridge_enabled"]:
                        await bot.api.send_post(
                            "home",
                            client.username + ": " + str(message["val"]["val"]["p"]),
                        )

                case "delete":
                    Info(
                        f"Client {str(client.id)} sent message: UID: {str(message["val"]["val"]["uid"])}, mode: {str(message["val"]["val"]["type"])}, timestamp: {float(time.time())}"
                    )
                    db.delete_data(
                        "posts",
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


@server.on_message
async def msg(client, message):
    Info(str(message))


"""@server.on_message
async def msg(client, message):
    Info(str(message))
"""


def signal_handler(sig, frame):
    print("\n")
    Error(f"Received signal {sig}. Script is terminating.")
    db.close()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

bot = Bot()


@bot.listen(cbids.message)
async def message(message):
    global server
    Info("Message received from " + message.user.username)
    print(message.data)
    server.send_packet_multicast(
        server.clients_manager.clients,
        {
            "cmd": "gmsg",
            "val": {
                "cmd": "bridged",
                "val": {
                    "author": message.user.username,
                    "post_content": str(message.data),
                    "attachment": "",
                    "uid": message.post_id,
                },
            },
        },
    )


# Start the server in a separate process
def run_bot():
    Info("Started MeowerBot")
    bot.run(os.getenv("username"), os.getenv("pswd"))


if __name__ == "__main__":
    server_process = Process(target=run_bot)
    server_process.start()

    try:
        server.run()
    except Exception:
        pass
    finally:
        server_process.terminate()
        os._exit(0)
