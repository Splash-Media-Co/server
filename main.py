# Import the server
from cloudlink import server
# Import logging helpers

from logs import Info

# Import DB handler
from owodb import OwODB  # noqa: F401

# Import protocols
from cloudlink.server.protocols import clpv4, scratch

# Instantiate the server object
server = server()

# Instantiate the OwODB object
db = OwODB("db")
db.create_table(
    "users",
    [
        "username",
        "creation_date",
        "uuid",
        "banned?",
        "quote",
        "pfpid",
        "lastseen",
        "badgeids",
        "extraflags",
    ],
)

# Set logging level
server.logging.basicConfig(
    level=server.logging.DEBUG  # See python's logging library for details on logging levels.
)

# Load protocols
clpv4 = clpv4(server)
scratch = scratch(server)

Info("Started server!")


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
    if message["val"]["cmd"] == "post":
        Info(
            f"Client {str(client)} sent message: Post: {str(message["val"]["val"]["p"])}, mode: {str(message["val"]["val"]["type"])}, timestamp: {str(message["val"]["val"]["t"])}"
        )


@server.on_message
async def msg(client, message):
    Info(str(message))


"""@server.on_message
async def msg(client, message):
    Info(str(message))
"""

Info("Started server!")
# Start the server!
server.run(ip="127.0.0.1", port=3000)
