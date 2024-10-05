from flask import Blueprint, request, jsonify
import os
from bson import ObjectId
from werkzeug.utils import secure_filename
from datetime import datetime
from app.db.db import db
from PIL import Image
import numpy as np
import cv2
from skimage.segmentation import felzenszwalb
from skimage import io

images_routes = Blueprint("images", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads/images")

# create the uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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
    if "files" not in request.files:
        return jsonify({"message": "No files found"}), 400

    files = request.files.getlist("files")

    if len(files) == 0:
        return jsonify({"message": "No files found"}), 400

    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            image_id = ObjectId()
            file_ext = secure_filename(file.filename).split(".")[-1].lower()
            filepath = os.path.join(UPLOAD_FOLDER, f"{str(image_id)}.{file_ext}")

            file.save(filepath)

            image_metadata = {
                "_id": image_id,
                "original_name": file.filename,
                "file_path": filepath,
                "uploaded_at": datetime.now(),
                "color_histogram": None,
                "segmentation_mask": None,
            }

            db.images.insert_one(image_metadata)

            saved_files.append({**image_metadata, "_id": str(image_id)})
        else:
            return (
                jsonify({"message": f"File {file.filename} has an invalid format"}),
                400,
            )

    return (
        jsonify(
            {
                "message": f"Uploaded {len(saved_files)} files successfully",
                "files": saved_files,
            }
        ),
        200,
    )


@images_routes.route("/images/<image_id>/histogram", methods=["POST"])
def generate_color_histogram(image_id):
    try:
        image = db.images.find_one({"_id": ObjectId(image_id)})
        if not image:
            return jsonify({"message": "Image not found"}), 404

        image_path = image["file_path"]
        with Image.open(image_path) as img:

            img = img.convert("RGB")

            histogram = img.histogram()

            # The histogram will be a list of 768 values (256 bins for each of the R, G, B channels)
            r_histogram = histogram[0:256]
            g_histogram = histogram[256:512]
            b_histogram = histogram[512:768]

            histogram_data = {"R": r_histogram, "G": g_histogram, "B": b_histogram}

            # update the image with the new histogram
            db.images.update_one(
                {"_id": ObjectId(image_id)},
                {"$set": {"color_histogram": histogram_data}},
            )

            return (
                jsonify(
                    {
                        "message": "Color histogram generated successfully",
                        "histogram": histogram_data,
                    }
                ),
                200,
            )

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@images_routes.route("/images/<image_id>/segmentation", methods=["POST"])
def generate_segmentation_mask(image_id):
    try:
        image = db.images.find_one({"_id": ObjectId(image_id)})
        if not image:
            return jsonify({"message": "Image not found"}), 404

        image_path = image["file_path"]

        img = cv2.imread(image_path)
        if img is None:
            return jsonify({"message": "Error loading image"}), 500

        # Apply Felzenszwalb segmentation

        # Convert image to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        segments = felzenszwalb(img_rgb, scale=100, sigma=0.5, min_size=50)

        # Convert the segmentation result to an 8-bit image
        mask = (segments * (255 / segments.max())).astype(np.uint8)

        mask_filename = f"{image_id}_segmentation_mask.png"
        mask_path = os.path.join(UPLOAD_FOLDER, mask_filename)
        io.imsave(mask_path, mask)

        db.images.update_one(
            {"_id": ObjectId(image_id)},
            {"$set": {"segmentation_mask": mask_filename}},
        )

        return (
            jsonify(
                {
                    "message": "Segmentation mask generated successfully",
                    "mask": mask_filename,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@images_routes.route("/images/<image_id>/resize", methods=["POST"])
def resize_image(image_id):
    width = request.json.get("width")
    height = request.json.get("height")

    if not width or not height:
        return jsonify({"message": "Width and height are required"}), 400

    try:
        image = db.images.find_one({"_id": ObjectId(image_id)})
        if not image:
            return jsonify({"message": "Image not found"}), 404

        image_path = image["file_path"]
        img = Image.open(image_path)

        # resize the image
        resized_img = img.resize((width, height), Image.ANTIALIAS)

        # save the resized image
        resized_img.save(image_path)

        return jsonify({"message": "Image resized successfully"}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@images_routes.route("/images/<image_id>/crop", methods=["POST"])
def crop_image(image_id):
    left = request.json.get("left")
    top = request.json.get("top")
    right = request.json.get("right")
    bottom = request.json.get("bottom")

    if not left or not top or not right or not bottom:
        return (
            jsonify(
                {"message": "Left, top, right, and bottom coordinates are required"}
            ),
            400,
        )

    try:
        image = db.images.find_one({"_id": ObjectId(image_id)})
        if not image:
            return jsonify({"message": "Image not found"}), 404

        image_path = image["file_path"]
        img = Image.open(image_path)

        # crop the image
        cropped_img = img.crop((left, top, right, bottom))

        # save the cropped image
        cropped_img.save(image_path)

        return jsonify({"message": "Image cropped successfully"}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@images_routes.route("/images/<image_id>/convert", methods=["POST"])
def convert_image(image_id):
    format = request.json.get("format")

    if not format:
        return jsonify({"message": "Format is required"}), 400

    try:
        image = db.images.find_one({"_id": ObjectId(image_id)})
        if not image:
            return jsonify({"message": "Image not found"}), 404

        image_path = image["file_path"]
        img = Image.open(image_path)

        # convert the image
        converted_img = img.convert(format)

        # save the converted image
        converted_img.save(image_path)

        return jsonify({"message": "Image converted successfully"}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500
