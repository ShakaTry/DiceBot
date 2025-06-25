from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def handler(path):
    return jsonify({"message": "Hello from Vercel!", "status": "working"})
