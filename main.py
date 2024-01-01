# Import the server
from cloudlink import server

# Import logging helpers
from logs import Info, Warning, Debug, Error, Critical  # noqa: F401

# Import time handlers
import time  # noqa: F401
import datetime  # noqa: F401

# Import DB handler
from local_simple_database import LocalDictDatabase

# Import UUID helpers
import uuid

# Import protocols
from cloudlink.server.protocols import clpv4, scratch

# Import signal handling and sys
import signal
import sys

# Instantiate the server object
server = server()

# Instantiate the LDD object
db = LocalDictDatabase(str_path_database_dir="./Documents/Github/server/db")
# Set logging level
server.logging.basicConfig(
    level=server.logging.DEBUG  # See python's logging library for details on logging levels.
)

# Load protocols
clpv4 = clpv4(server)
scratch = scratch(server)


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
async def direct(
    client,
    message,
):
    match str(message["val"]["cmd"]):
        case "post":
            match str(message["val"]["val"]["type"]):
                case "send":
                    Info(
                        f"Client {str(client.id)} sent message: Post: {str(message["val"]["val"]["p"])}, mode: {str(message["val"]["val"]["type"])}, timestamp: {str(message["val"]["val"]["t"])}, chat_id = {str(message["val"]["val"]["c"])}"
                    )
                    uid = str(uuid.uuid4())
                    print(uid)
                    # auth stuff goes here i guess
                    chatid = message["val"]["val"]["c"]
                    user = message["val"]["val"]["u"]
                    post = message["val"]["val"]["p"]
                    timestamp = message["val"]["val"]["t"]
                    try:
                        db[f"dict_posts_{chatid}"]
                    except KeyError:
                        print(f"new chat created somehow: {chatid}")
                        db[f"dict_posts_{chatid}"] = {}
                    print(
                        {
                            "sender": user,
                            "post": post,
                            "timestamp": timestamp,
                            "uid": uid,
                        }
                    )
                    db[f"dict_posts_{chatid}"][uid] = {
                        "sender": user,
                        "post": post,
                        "timestamp": timestamp,
                        "message_uid": uid,
                    }  # needs uid param because it will generally be accessed with db[chat_id][-1] (or whatever position)
                    print(db[f"dict_posts_{chatid}"])
                    print(f'db: {db[f"dict_posts_{chatid}"][uid]}')
                    # db.insert_data(
                    # "posts",
                    # (
                    #    str(client.username),
                    #    float(time.time()),
                    #    uid,
                    #    str(message["val"]["val"]["p"]),
                    #    False,
                    #    "home",
                    #    str(message["val"]["val"]["type"]),
                    # ),
                    # )
                    server.send_packet_multicast(
                        server.clients_manager.clients,
                        {
                            "cmd": "gmsg",
                            "val": {
                                "cmd": "rpost",
                                "val": {
                                    "author": message["val"]["val"]["u"],
                                    "post_content": str(message["val"]["val"]["p"]),
                                    "uid": uid,
                                    "timestamp": message["val"]["val"]["t"],
                                    "chat_id": message["val"]["val"]["c"],
                                },
                            },
                        },
                    )
                case "delete":
                    Info(
                        f"Client {str(client.id)} sent message: UID: {str(message["val"]["val"]["uid"])}, mode: {str(message["val"]["val"]["type"])}, timestamp: {str(message["val"]["val"]["t"])}, chat_id = {str(message["val"]["val"]["c"])}"
                    )
                    # auth stuff here so you cant just delete other people's messages
                    del db[message["val"]["val"]["c"]][message["val"]["val"]["uid"]]
                    # db.update_data(
                    #    "posts",
                    #    {"isDeleted": True},
                    #    {"uid": str(message["val"]["val"]["uid"])},
                    # )
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
                case "getposts":
                    Info(f"Client {str(client.id)} requested somethin i dont know")


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
server.run(ip="localhost", port=8080)
