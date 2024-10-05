from flask import Blueprint, request, jsonify
import os
import pandas as pd
import csv
from app.db.db import db
from bson import json_util

csv_routes = Blueprint("csv", __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")

# Create the uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@csv_routes.route("/csv", methods=["POST"])
def csv_upload():
    if "file" not in request.files:
        return jsonify({"message": "No file found"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No file found"}), 400

    if file and file.filename.endswith(".csv"):
        print(f"Saving {file.filename} to {os.path.join(UPLOAD_FOLDER, file.filename)}")
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        try:
            # with open(filepath, newline="", encoding="utf-8") as csvfile:
            #     reader = csv.DictReader(csvfile)
            #     rows = list(reader)

            data = pd.read_csv(filepath)
            rows = data.to_dict(orient="records")

            if rows and len(rows) > 0:
                db.csv.insert_many(rows)
                return jsonify({"message": "CSV uploaded successfully"}), 200

        except Exception as e:
            return jsonify({"message": str(e)}), 500

    else:
        return jsonify({"message": "Invalid file type"}), 400


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
        data_cursor = db.csv.find().skip(skip).limit(limit)
        data = list(data_cursor)
        total = db.csv.count_documents({})
        return json_util.dumps({"data": data, "total": total}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@csv_routes.route("/csv/statistics", methods=["GET"])
def get_csv_statistics():
    csv_data = db.csv.find()

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

    return json_util.dumps(statistics), 200
