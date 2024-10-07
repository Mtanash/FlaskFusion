from app.repositories.csv_repository import CsvRepository
from app.errors import NotFoundError, ValidationError


class CsvService:
    def __init__(self, csv_repository: CsvRepository) -> None:
        if csv_repository is None:
            raise ValueError("csv_repository cannot be None")
        self.csv_repository = csv_repository

    def process_and_upload_csv(self, file: object, upload_folder: str) -> dict:
        if not file:
            raise NotFoundError("No file found")

        return self.csv_repository.upload_csv(file, upload_folder)

    def delete_csv_file(self, csv_id: str) -> dict:
        return self.csv_repository.delete_csv_file(csv_id)

    def delete_csv_record(self, record_id: str) -> dict:
        return self.csv_repository.delete_csv_record(record_id)

    def get_csv_statistics(self, csv_id: str) -> dict:
        return self.csv_repository.get_csv_statistics(csv_id)

    def get_csv_by_id(self, csv_id: str) -> dict:
        return self.csv_repository.get_csv_by_id(csv_id)

    def get_csv_data_by_id(
        self, csv_id: str, page: int = 1, page_size: int = 10
    ) -> dict:
        if page < 1:
            raise ValidationError("Invalid page number")

        if page_size < 1:
            raise ValidationError("Invalid page size")

        if not csv_id:
            raise NotFoundError("CSV not found")

        if not self.csv_repository.get_csv_by_id(csv_id):
            raise NotFoundError("CSV not found")

        return self.csv_repository.get_csv_data_by_id(csv_id, page, page_size)

    def get_csv(self, page: int = 1, page_size: int = 10) -> dict:
        if page < 1:
            raise ValidationError("Invalid page number")

        if page_size < 1:
            raise ValidationError("Invalid page size")

        return self.csv_repository.get_csv(page, page_size)
