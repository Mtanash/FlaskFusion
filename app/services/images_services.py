from app.repositories.images_repository import ImagesRepository
from app.config import config
from app.errors import DatabaseError, ValidationError, NotFoundError


ALLOWED_EXTENSIONS = config.get("allowed_images_extensions", {"png", "jpg", "jpeg"})


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class ImagesService:
    def __init__(self, images_repository: ImagesRepository):
        if images_repository is None:
            raise ValueError("images_repository cannot be None")
        self.images_repository = images_repository

    def upload_images(self, files):
        if not files:
            raise ValidationError("No files found")

        if len(files) == 0:
            raise ValidationError("No files found")

        for file in files:
            if not allowed_file(file.filename):
                raise ValidationError("Invalid file type")

        return self.images_repository.upload_images(files)

    def get_image(self, image_id):
        if not image_id:
            raise NotFoundError("Image not found")

        return self.images_repository.get_image_by_id(image_id)

    def delete_image(self, image_id):
        if not image_id:
            raise NotFoundError("Image not found")

        return self.images_repository.delete_image(image_id)

    def generate_image_histogram(self, image_id):
        if not image_id:
            raise NotFoundError("Image not found")

        return self.images_repository.generate_image_histogram(image_id)

    def generate_segmentation_mask(self, image_id):
        if not image_id:
            raise NotFoundError("Image not found")

        return self.images_repository.generate_segmentation_mask(image_id)

    def resize_image(self, image_id, width, height):
        if not image_id:
            raise NotFoundError("Image not found")

        if not width or not height:
            raise ValidationError("Width and height are required")

        if width < 0 or height < 0:
            raise ValidationError("Width and height must be greater than 0")

        return self.images_repository.resize_image(image_id, width, height)

    def crop_image(self, image_id, left, top, right, bottom):
        if not image_id:
            raise NotFoundError("Image not found")

        if not left or not top or not right or not bottom:
            raise ValidationError(
                "Left, top, right, and bottom coordinates are required"
            )

        return self.images_repository.crop_image(image_id, left, top, right, bottom)

    def convert_image(self, image_id, format):
        if not image_id:
            raise NotFoundError("Image not found")

        if not format:
            raise ValidationError("Format is required")

        if format not in {"png", "jpg", "jpeg"}:
            raise ValidationError("Invalid format")

        return self.images_repository.convert_image(image_id, format)
