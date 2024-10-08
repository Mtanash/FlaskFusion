from bson import ObjectId
import pandas as pd
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from pymongo.database import Database
from app.errors import DatabaseError, ValidationError, NotFoundError


class CsvRepository:
    def __init__(self, db: Database) -> None:
        if db is None:
            raise ValueError("db cannot be None")
        self.db = db

    def upload_csv(self, file: object, upload_folder: str) -> dict:
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        csv_metadata_id = ObjectId()
        csv_metadata = {
            "_id": csv_metadata_id,
            "filename": filename,
            "filepath": filepath,
            "uploaded_at": datetime.now(),
        }

        self.db.csvmetadata.insert_one(csv_metadata)

        csv_data = pd.read_csv(filepath)
        rows = csv_data.to_dict(orient="records")

        # insert the csv id into the csv data
        for row in rows:
            row["csv_id"] = csv_metadata_id

        self.db.csv.insert_many(rows)

        return {"message": "CSV data uploaded successfully"}

    def get_csv(self, page: int = 1, page_size: int = 10):
        skip = (page - 1) * page_size
        limit = page_size

        csv_data = self.db.csvmetadata.aggregate(
            [
                {"$skip": skip},
                {"$limit": limit},
                {"$addFields": {"_id": {"$toString": "$_id"}}},
            ]
        )

        total = self.db.csvmetadata.count_documents({})

        return {"data": list(csv_data), "total": total}

    def get_csv_by_id(self, csv_id: str) -> dict:
        csv_data = self.db.csvmetadata.aggregate(
            [
                {"$match": {"_id": ObjectId(csv_id)}},
                {"$addFields": {"_id": {"$toString": "$_id"}}},
            ],
        )

        if not csv_data:
            raise NotFoundError("CSV data not found")

        return {"data": list(csv_data)[0]}

    def get_csv_data_by_id(
        self, csv_id: str, page: int = 1, page_size: int = 10
    ) -> dict:
        skip = (page - 1) * page_size
        limit = page_size

        csv_data = self.db.csv.aggregate(
            [
                {
                    "$match": {"csv_id": ObjectId(csv_id)},
                },
                {
                    "$addFields": {"_id": {"$toString": "$_id"}},
                },
                {"$project": {"csv_id": 0}},
                {
                    "$skip": skip,
                },
                {
                    "$limit": limit,
                },
            ]
        )

        total = self.db.csv.count_documents({"csv_id": ObjectId(csv_id)})

        return {"data": list(csv_data), "total": total}

    def retrieve_csv_data_as_dataframe(self, csv_id: str) -> pd.DataFrame:
        csv_data = self.db.csv.aggregate(
            [
                {
                    "$match": {"csv_id": ObjectId(csv_id)},
                },
                {
                    "$addFields": {"_id": {"$toString": "$_id"}},
                },
                {"$project": {"csv_id": 0}},
            ]
        )

        if not csv_data:
            return None

        data = pd.DataFrame(list(csv_data)).drop(columns=["_id"])
        return data if not data.empty else None

    def calculate_statstics(self, data: pd.DataFrame) -> dict:
        statistics = {
            "mean": {},
            "median": {},
            "mode": {},
            "quartiles": {},
            "outliers": {},
        }

        for column in data.select_dtypes(include=["float64", "int"]).columns:
            if pd.api.types.is_numeric_dtype(data[column]):
                statistics["mean"][column] = float(data[column].mean())
                statistics["median"][column] = float(data[column].median())
                statistics["mode"][column] = float(data[column].mode().iloc[0])
                statistics["quartiles"][column] = {
                    k: float(v)
                    for k, v in data[column].quantile([0.25, 0.5, 0.75]).items()
                }
                statistics["outliers"][column] = self.find_outliers(data[column])

        return statistics

    def find_outliers(self, series: pd.Series) -> list:
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        return outliers.astype(object).to_dict()

    def get_csv_statistics(self, csv_id: str) -> dict:
        data = self.retrieve_csv_data_as_dataframe(csv_id)
        if data is None:
            return {"message": "CSV data not found"}, 404

        statistics = self.calculate_statstics(data)

        return statistics

    def delete_csv_file(self, csv_id: str) -> dict:
        self.db.csvmetadata.delete_one({"_id": ObjectId(csv_id)})
        self.db.csv.delete_many({"csv_id": ObjectId(csv_id)})
        return {"message": "CSV data deleted successfully"}

    def delete_csv_record(self, record_id: str) -> dict:
        self.db.csv.delete_one(
            {
                "_id": ObjectId(record_id),
            }
        )
        return {"message": "Record deleted successfully"}
