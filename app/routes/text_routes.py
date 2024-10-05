from flask import Blueprint, request, jsonify
from app.db.db import db
from bson import ObjectId
from transformers import pipeline
import spacy

text_routes = Blueprint("text", __name__)

summarizer = pipeline("summarization", model="t5-small")
sentiment_analyzer = pipeline("sentiment-analysis")
nlp = spacy.load("en_core_web_sm")


@text_routes.route("/text/summarize", methods=["POST"])
def summarize_text():
    text = request.json.get("text")

    if not text:
        return jsonify({"message": "No text found"}), 400

    try:
        summary = summarizer(text, max_length=100, min_length=10, do_sample=False)[0][
            "summary_text"
        ]
        return jsonify({"summary": summary}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@text_routes.route("/text/keywords", methods=["POST"])
def extract_keywords():
    text = request.json.get("text")

    if not text:
        return jsonify({"message": "No text found"}), 400

    try:
        doc = nlp(text)
        keywords = set()

        for token in doc:
            if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop:
                keywords.add(token.text)

        return jsonify({"keywords": list(keywords)}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@text_routes.route("/text/sentiment", methods=["POST"])
def analyze_sentiment():
    text = request.json.get("text")

    if not text:
        return jsonify({"message": "No text found"}), 400

    try:
        result = sentiment_analyzer(text)
        sentiment = result[0]

        return jsonify({"label": sentiment["label"], "score": sentiment["score"]}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500
