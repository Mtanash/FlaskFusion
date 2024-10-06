from flask import Flask, send_from_directory
from app.routes.csv_routes import csv_routes
from app.routes.images_routes import images_routes
from app.routes.text_routes import text_routes
from dotenv import load_dotenv
from flask_cors import CORS
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")

app.register_blueprint(csv_routes)
app.register_blueprint(images_routes)
app.register_blueprint(text_routes)


# serve the uploaded files
@app.route("/uploads/<path:name>", methods=["GET"])
def serve_file(name):
    return send_from_directory(UPLOAD_FOLDER, name)


@app.route("/")
def index():
    return "<h1>Hello, World!</h1>"


if __name__ == "__main__":
    app.run(debug=True)
