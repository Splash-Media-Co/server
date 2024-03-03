from flask import Flask, request
import subprocess

app = Flask("app")
server_process = None

# Start the server when the script executes
print("Starting the server...")
server_process = subprocess.Popen(["python", "main.py"])


@app.route("/")
def index():
    return "Pong!", 200


@app.post("/gh-push")
def github_push():
    global server_process
    payload = request.json
    if payload["repository"]["full_name"] == "Splash-Media-Co/server":
        print("Stopping the server...")
        if server_process:
            server_process.terminate()
            server_process = None
        print("Fetching changes...")
        subprocess.run(["git", "pull"])
        print("Starting the server...")
        server_process = subprocess.Popen(["python", "main.py"])
        return "Done!", 200


if __name__ == "__main__":
    app.run(port=4000)
