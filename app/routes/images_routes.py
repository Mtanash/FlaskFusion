from flask import Blueprint, request, jsonify
import os
from app.db.db import db
from app.config import config
from app.repositories.images_repository import ImagesRepository
from app.services.images_services import ImagesService

images_routes = Blueprint("images", __name__)

UPLOAD_FOLDER = config.get("images_upload_folder")

images_repository = ImagesRepository(db, UPLOAD_FOLDER)
images_service = ImagesService(images_repository)

# create the uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@images_routes.route("/images", methods=["GET"])
def get_images():
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=10, type=int)

    if page < 1:
        return jsonify({"message": "Invalid page number"}), 400

    if page_size < 1:
        return jsonify({"message": "Invalid page size"}), 400

    skip = (page - 1) * page_size
    limit = page_size
    try:
        data_cursor = db.images.aggregate(
            [
                {"$skip": skip},
                {"$limit": limit},
                {"$addFields": {"_id": {"$toString": "$_id"}}},
            ]
        )
        data = list(data_cursor)
        total = db.images.count_documents({})
        return jsonify({"data": data, "total": total}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@images_routes.route("/images/upload", methods=["POST"])
def upload_images():
    files = request.files.getlist("files")
    return jsonify(images_service.upload_images(files)), 200


@images_routes.route("/images/<image_id>", methods=["GET"])
def get_image(image_id):
    return jsonify({"data": images_service.get_image(image_id)}), 200


@images_routes.route("/images/<image_id>", methods=["DELETE"])
def delete_image(image_id):
    return jsonify(images_service.delete_image(image_id)), 200


@images_routes.route("/images/<image_id>/histogram", methods=["POST"])
def generate_color_histogram(image_id):
    return jsonify(images_service.generate_image_histogram(image_id)), 200


@images_routes.route("/images/<image_id>/segmentation", methods=["POST"])
def generate_segmentation_mask(image_id):
    return jsonify(images_service.generate_segmentation_mask(image_id)), 200


@images_routes.route("/images/<image_id>/resize", methods=["POST"])
def resize_image(image_id):
    width = request.json.get("width")
    height = request.json.get("height")

    return jsonify(images_service.resize_image(image_id, width, height)), 200


@images_routes.route("/images/<image_id>/crop", methods=["POST"])
def crop_image(image_id):
    left = request.json.get("left")
    top = request.json.get("top")
    right = request.json.get("right")
    bottom = request.json.get("bottom")

    return jsonify(images_service.crop_image(image_id, left, top, right, bottom)), 200


@images_routes.route("/images/<image_id>/convert", methods=["POST"])
def convert_image(image_id):
    format = request.json.get("format")

    return jsonify(images_service.convert_image(image_id, format)), 200
