from flask import Flask
from app.routes.csv_routes import csv_routes
from app.routes.images_routes import images_routes
from app.routes.text_routes import text_routes
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

# config
app.config["UPLOAD_FOLDER"] = "uploads"

app.register_blueprint(csv_routes)
app.register_blueprint(images_routes)
app.register_blueprint(text_routes)


@app.route("/")
def index():
    return "<h1>Hello, World!</h1>"


if __name__ == "__main__":
    app.run(debug=True)
