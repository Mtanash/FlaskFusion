from flask import Flask
from app.routes.csv_routes import csv_routes
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# config
app.config["UPLOAD_FOLDER"] = "uploads"

app.register_blueprint(csv_routes)


@app.route("/")
def index():
    return "<h1>Hello, World!</h1>"


if __name__ == "__main__":
    app.run(debug=True)
