import time


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

async def is_client_authenticated(client_id, authenticated_clients):
    return client_id in authenticated_clients
