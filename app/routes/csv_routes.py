from flask import Blueprint, request, jsonify
import os
import pandas as pd
from app.db.db import db
from bson import ObjectId
from werkzeug.utils import secure_filename
from datetime import datetime

csv_routes = Blueprint("csv", __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads/csv")

# Create the uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@csv_routes.route("/csv/upload", methods=["POST"])
def csv_upload():
    if "file" not in request.files:
        return jsonify({"message": "No file found"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No file found"}), 400

    if file and file.filename.endswith(".csv"):
        filename = secure_filename(file.filename)

        # check if file already exists
        if filename in os.listdir(UPLOAD_FOLDER):
            return jsonify({"message": "File already exists"}), 400

        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        csv_metadata_id = ObjectId()
        csv_metadata = {
            "_id": csv_metadata_id,
            "filename": filename,
            "filepath": filepath,
            "uploaded_at": datetime.now(),
        }

        db.csvmetadata.insert_one(csv_metadata)

        csv_data = pd.read_csv(filepath)
        rows = csv_data.to_dict(orient="records")

        # insert the csv id into the csv data
        for row in rows:
            row["csv_id"] = csv_metadata_id

        db.csv.insert_many(rows)

        return jsonify({"message": "CSV uploaded successfully"}), 200

    else:
        return jsonify({"message": "Invalid file type"}), 400


@csv_routes.route("/csv, methods=['POST']")
def post_csv():
    new_row = request.json

    # validate data
    if not new_row:
        return jsonify({"message": "No data found"}), 400

    for field in REQUIRED_FIELDS:
        if field not in new_row:
            return jsonify({"message": f"Missing required field: {field}"}), 400

    try:
        db.csv.insert_one(new_row)
        return jsonify({"message": "CSV data inserted successfully"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@csv_routes.route("/csv/<csv_id>", methods=["PATCH"])
def update_csv(csv_id):
    updated_row = request.json

    if not updated_row:
        return jsonify({"message": "No data found"}), 400

    try:
        db.csv.update_one({"_id": ObjectId(csv_id)}, {"$set": updated_row})
        return jsonify({"message": "CSV data updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@csv_routes.route("/csv/<csv_id>", methods=["DELETE"])
def delete_csv_file(csv_id):
    try:
        db.csvmetadata.delete_one({"_id": ObjectId(csv_id)})
        db.csv.delete_many({"csv_id": ObjectId(csv_id)})
        return jsonify({"message": "CSV data deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@csv_routes.route("/csv/delete/<csv_id>", methods=["DELETE"])
def delete_csv(csv_id):
    try:
        db.csv.delete_one({"_id": ObjectId(csv_id)})
        return jsonify({"message": "CSV data deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@csv_routes.route("/csv", methods=["GET"])
def get_csv():
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=10, type=int)

    if page < 1:
        return jsonify({"message": "Invalid page number"}), 400

    if page_size < 1:
        return jsonify({"message": "Invalid page size"}), 400

    skip = (page - 1) * page_size
    limit = page_size
    try:
        data_cursor = db.csvmetadata.aggregate(
            [
                {"$skip": skip},
                {"$limit": limit},
                {"$addFields": {"_id": {"$toString": "$_id"}}},
            ]
        )
        data = list(data_cursor)
        total = db.csvmetadata.count_documents({})
        return jsonify({"data": data, "total": total}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@csv_routes.route("/csv/<csv_id>", methods=["GET"])
def get_csv_by_id(csv_id):
    try:
        csv_data = db.csvmetadata.aggregate(
            [
                {"$match": {"_id": ObjectId(csv_id)}},
                {"$addFields": {"_id": {"$toString": "$_id"}}},
            ],
        )
        if not csv_data:
            return jsonify({"message": "CSV data not found"}), 404

        return jsonify({"data": list(csv_data)[0]}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@csv_routes.route("/csv/<csv_id>/data", methods=["GET"])
def get_csv_data_by_id(csv_id):
    try:
        page = request.args.get("page", default=1, type=int)
        page_size = request.args.get("page_size", default=10, type=int)

        if page < 1:
            return jsonify({"message": "Invalid page number"}), 400

        if page_size < 1:
            return jsonify({"message": "Invalid page size"}), 400

        skip = (page - 1) * page_size
        limit = page_size

        csv_data = db.csv.aggregate(
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

        total = db.csv.count_documents({"csv_id": ObjectId(csv_id)})

        if not csv_data:
            return jsonify({"message": "CSV data not found"}), 404

        return jsonify({"data": list(csv_data), "total": total}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@csv_routes.route("/csv/<csv_id>/statistics", methods=["GET"])
def get_csv_statistics(csv_id):
    csv_data = db.csv.aggregate(
        [
            {
                "$match": {"csv_id": ObjectId(csv_id)},
            },
            {
                "$addFields": {"_id": {"$toString": "$_id"}},
            },
            {
                "$project": {"csv_id": 0},
            },
        ]
    )

    if not csv_data:
        return jsonify({"message": "CSV data not found"}), 404

    data = pd.DataFrame(list(csv_data)).drop(columns=["_id"])

    if data.empty:
        return jsonify({"message": "CSV data not found"}), 404

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
                k: float(v) for k, v in data[column].quantile([0.25, 0.5, 0.75]).items()
            }

            Q1 = data[column].quantile(0.25)
            Q3 = data[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = data[(data[column] < lower_bound) | (data[column] > upper_bound)]
            statistics["outliers"][column] = outliers.astype(object).to_dict(
                orient="records"
            )

    return jsonify(statistics), 200


@csv_routes.route("/csv/query", methods=["GET"])
def query_csv():
    column = request.args.get("column")
    value = request.args.get("value")
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=10, type=int)

    skip = (page - 1) * page_size
    limit = page_size

    if not column or not value:
        return jsonify({"message": "Missing column or value"}), 400

    query = {column: value}
    csv_data = db.csv.aggregate(
        [
            {"$match": query},
            {"$skip": skip},
            {"$limit": limit},
            {"$addFields": {"_id": {"$toString": "$_id"}}},
        ]
    )
    csv_count = db.csv.count_documents(query)

    if not csv_data:
        return jsonify({"message": "CSV data not found"}), 404

    return jsonify({"data": list(csv_data), "total": csv_count}), 200
