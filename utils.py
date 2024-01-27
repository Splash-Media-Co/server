import time
import audit

class WebSocketRateLimiter:
    def __init__(self, rate_limit, time_interval):
        self.rate_limit = rate_limit
        self.time_interval = time_interval
        self.client_buckets = {}

    async def acquire(self, client_id):
        if client_id not in self.client_buckets:
            self.client_buckets[client_id] = {
                "tokens": self.rate_limit,
                "last_update": time.time(),
            }

        client_bucket = self.client_buckets[client_id]
        now = time.time()
        elapsed_time = now - client_bucket["last_update"]

        # Refill tokens based on the elapsed time
        client_bucket["tokens"] += elapsed_time * (self.rate_limit / self.time_interval)
        client_bucket["tokens"] = min(client_bucket["tokens"], self.rate_limit)
        client_bucket["last_update"] = now

        # Check if there are enough tokens
        if client_bucket["tokens"] >= 1:
            client_bucket["tokens"] -= 1
            return True
        else:
            return False

async def isAuthenticated(server, client_id, authenticated_clients):
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
            audit.log_action(
                "not_authenticated",
                client.username,
                f"User tried to do something {str(message["val"]["val"]["p"])} while not authenticated",
            )
            return False
        except Exception as e:
            Error(
                f"Error sending message to client {str(client)}: "
                + str(e)
            )
            audit.log_action(
                "send_to_client_fail",
                client.username,
                f"Tried to post to client with error {e}",
            )
    else:
        return True