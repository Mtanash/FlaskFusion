import os

config = {
    "csv_upload_folder": os.path.join(os.getcwd(), "uploads/csv"),
    "images_upload_folder": os.path.join(os.getcwd(), "uploads/images"),
    "allowed_images_extensions": {"png", "jpg", "jpeg"},
}
