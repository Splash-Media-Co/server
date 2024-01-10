from main import server
from multiprocessing import Process

from logs import Info, Debug, Warning, Error, Critical

from dotenv import load_dotenv
import os

from MeowerBot import Bot, cbids
server = initserver()
load_dotenv()

bot = Bot()


@bot.listen(cbids.message)
async def message(message):
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
                },
            },
        },
    )


# Start the server in a separate process
def run_server():
    server.run(ip="127.0.0.1", port=3000)


if __name__ == "__main__":
    server_process = Process(target=run_server)
    server_process.start()

    try:
        bot.run(os.getenv("username"), os.getenv("pswd"))
    except Exception:
        pass
    finally:
        server_process.terminate()
        os._exit(0)
