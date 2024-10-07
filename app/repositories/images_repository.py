from flask import jsonify
import os
from bson import ObjectId
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
import numpy as np
import cv2
from skimage.segmentation import felzenszwalb
from skimage import io
from app.errors import DatabaseError, ValidationError, NotFoundError
from pymongo.database import Database


class ImagesRepository:
    def __init__(self, db: Database, upload_folder: str):
        if db is None:
            raise ValueError("db cannot be None")
        if upload_folder is None:
            raise ValueError("upload_folder cannot be None")
        self.db = db
        self.upload_folder = upload_folder

    def _generate_filepath(self, file, image_id) -> str:
        file_ext = secure_filename(file.filename).split(".")[-1].lower()
        return os.path.join(self.upload_folder, f"{str(image_id)}.{file_ext}")

    def _get_image_dimensions(self, filepath) -> tuple:
        with Image.open(filepath) as img:
            width, height = img.size
        file_size = os.path.getsize(filepath)
        return width, height, file_size

    def _create_image_metadata(
        self, image_id, original_name, filepath, width, height, file_size
    ) -> dict:
        return {
            "_id": image_id,
            "original_name": original_name,
            "file_path": filepath,
            "filename": os.path.basename(filepath),
            "uploaded_at": datetime.now(),
            "color_histogram": None,
            "segmentation_mask": None,
            "width": width,
            "height": height,
            "file_size": file_size,
        }

    def _save_image_file(self, file) -> dict:
        image_id = ObjectId()
        filepath = self._generate_filepath(file, image_id)

        file.save(filepath)
        width, height, file_size = self._get_image_dimensions(filepath)

        image_metadata = self._create_image_metadata(
            image_id, file.filename, filepath, width, height, file_size
        )

        self.db.images.insert_one(image_metadata)
        return {**image_metadata, "_id": str(image_id)}

    def upload_images(self, files):
        saved_files = []
        for file in files:
            saved_files.append(self._save_image_file(file))

        return saved_files

    def get_image_by_id(self, image_id):
        image = self.db.images.aggregate(
            [
                {"$match": {"_id": ObjectId(image_id)}},
                {"$addFields": {"_id": {"$toString": "$_id"}}},
            ]
        )

        if not image:
            raise NotFoundError("Image not found")

        return list(image)[0]

    def delete_image(self, image_id):
        result = self.db.images.delete_one({"_id": ObjectId(image_id)})
        if result.deleted_count == 0:
            raise NotFoundError("Image not found")
        return {"message": "Image deleted successfully"}

    def generate_image_histogram(self, image_id):
        image = self.get_image_by_id(image_id)
        histogram_data = self._calculate_histogram(image["file_path"])

        self.db.images.update_one(
            {"_id": ObjectId(image_id)},
            {"$set": {"color_histogram": histogram_data}},
        )

        return histogram_data

    def _calculate_histogram(self, image_path: str) -> dict:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            histogram = img.histogram()

            # Divide histogram into R, G, and B channels
            return {
                "R": histogram[0:256],
                "G": histogram[256:512],
                "B": histogram[512:768],
            }

    def generate_segmentation_mask(self, image_id):
        image = self.get_image_by_id(image_id)
        if not image:
            raise NotFoundError("Image not found")

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
        mask_path = os.path.join(self.upload_folder, mask_filename)
        io.imsave(mask_path, mask)

        self.db.images.update_one(
            {"_id": ObjectId(image_id)},
            {"$set": {"segmentation_mask": mask_filename}},
        )

        return {
            "message": "Segmentation mask generated successfully",
            "mask": mask_filename,
        }

    def resize_image(self, image_id, width, height):
        image = self.get_image_by_id(image_id)
        if not image:
            raise NotFoundError("Image not found")

        image_path = image["file_path"]
        img = Image.open(image_path)

        # resize the image
        resized_img = img.resize((width, height), Image.ANTIALIAS)

        # save the resized image
        resized_img.save(image_path)

        return {"message": "Image resized successfully"}

    def crop_image(self, image_id, left, top, right, bottom):
        image = self.get_image_by_id(image_id)
        if not image:
            raise NotFoundError("Image not found")

        image_path = image["file_path"]
        img = Image.open(image_path)

        # crop the image
        cropped_img = img.crop((left, top, right, bottom))

        # save the cropped image
        cropped_img.save(image_path)

        return {"message": "Image cropped successfully"}

    def convert_image(self, image_id, format):
        image = self.get_image_by_id(image_id)
        if not image:
            raise NotFoundError("Image not found")

        image_path = image["file_path"]
        img = Image.open(image_path)

        # convert the image
        converted_img = img.convert(format)

        # save the converted image
        converted_img.save(image_path)

        return {"message": "Image converted successfully"}
