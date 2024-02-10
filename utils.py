import time
from oceanaudit import OceanAuditLogger
from logs import Critical, Debug, Error, Info, Warning  # noqa: F401
from better_profanity import profanity
import requests
from dotenv import load_dotenv
import os

load_dotenv()
HF_TOKEN: str = os.getenv("HF_TOKEN")

# Instantiate the OceanAuditLogger object
audit = OceanAuditLogger()


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


async def isAuthenticated(server, client, authenticated_clients):
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
                "User tried to do something while not authenticated",
            )
        except Exception as e:
            Error(f"Error sending message to client {str(client)}: " + str(e))
            audit.log_action(
                "send_to_client_fail",
                client.username,
                f"Tried to post to client with error {e}",
            )
        finally:
            return False
    else:
        return True


class Moderator:
    def __init__(self, ml_enabled: bool = True):
        self.ml_enabled = ml_enabled

    async def moderate(self, text: str) -> bool | str | None:
        if self.ml_enabled:
            API_URL = "https://api-inference.huggingface.co/models/s-nlp/roberta_toxicity_classifier"
            headers = {"Authorization": "Bearer " + HF_TOKEN}

            payload = {
                "inputs": text,
            }

            response = requests.post(API_URL, headers=headers, json=payload)
            data = response.json()

            if data and isinstance(data, list) and len(data) > 0:
                result = data[0]
                if isinstance(result, list) and len(result) > 0:
                    toxicity_score = result[0].get("score", 0)
                    return toxicity_score <= 0.6
        else:
            profanity.load_censor_words()
            return profanity.censor(text)
