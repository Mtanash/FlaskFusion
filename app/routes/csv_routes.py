from flask import Blueprint, request, jsonify
import os
from app.db.db import db
from bson import ObjectId
from app.config import config
from app.repositories.csv_repository import CsvRepository
from app.services.csv_services import CsvService

csv_routes = Blueprint("csv", __name__)

csv_respository = CsvRepository(db)
csv_service = CsvService(csv_respository)

UPLOAD_FOLDER = config["csv_upload_folder"]
# Create the uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@csv_routes.route("/csv/upload", methods=["POST"])
def csv_upload():
    file = request.files.get("file")
    return jsonify(csv_service.process_and_upload_csv(file, UPLOAD_FOLDER)), 200


@csv_routes.route("/csv, methods=['POST']")
def post_csv():
    new_row = request.json

    # validate data
    if not new_row:
        return jsonify({"message": "No data found"}), 400

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
    return jsonify(csv_service.delete_csv_file(csv_id)), 200


@csv_routes.route("/csv/delete/<csv_id>", methods=["DELETE"])
def delete_csv(csv_id):
    return jsonify(csv_service.delete_csv_record(csv_id)), 200


@csv_routes.route("/csv", methods=["GET"])
def get_csv():
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=10, type=int)

    return jsonify(csv_service.get_csv(page, page_size)), 200


@csv_routes.route("/csv/<csv_id>", methods=["GET"])
def get_csv_by_id(csv_id):
    return jsonify(csv_service.get_csv_by_id(csv_id)), 200


@csv_routes.route("/csv/<csv_id>/data", methods=["GET"])
def get_csv_data_by_id(csv_id):
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=10, type=int)

    return jsonify(csv_service.get_csv_data_by_id(csv_id, page, page_size)), 200


@csv_routes.route("/csv/<csv_id>/statistics", methods=["GET"])
def get_csv_statistics(csv_id):
    return jsonify(csv_service.get_csv_statistics(csv_id)), 200


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
