# Import the server
from cloudlink import server

# Import logging helpers
from logs import Info

# Import protocols
from cloudlink.server.protocols import clpv4, scratch

# Instantiate the server object
server = server()

# Set logging level
server.logging.basicConfig(
    level=server.logging.DEBUG
)  # See python's logging library for details on logging levels.

# Load protocols
clpv4 = clpv4(server)
scratch = scratch(server)

Info("Started server!")

# Start the server!
server.run(ip="127.0.0.1", port=3000)
