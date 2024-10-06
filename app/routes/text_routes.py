from flask import Blueprint, request, jsonify
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import io
import base64
from app.services import text_services
from app.db.db import db
from sklearn.metrics.pairwise import cosine_similarity


text_routes = Blueprint("text", __name__)


@text_routes.route("/text", methods=["POST"])
def create_text():
    text = request.json.get("text")

    if not text:
        return jsonify({"message": "No text found"}), 400

    try:
        response = text_services.create_text(text)
        return jsonify(response), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@text_routes.route("/text", methods=["GET"])
def get_text():
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=10, type=int)

    if page < 1:
        return jsonify({"message": "Invalid page number"}), 400

    if page_size < 1:
        return jsonify({"message": "Invalid page size"}), 400

    try:
        data = text_services.get_text(page, page_size)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@text_routes.route("/text/<text_id>", methods=["GET"])
def get_text_by_id(text_id):
    try:
        text = text_services.get_text_by_id(text_id)
        return jsonify(text), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@text_routes.route("/text/<text_id>", methods=["DELETE"])
def delete_text(text_id):
    try:
        text_services.delete_text(text_id)
        return jsonify({"message": "Text deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@text_routes.route("/text/<text_id>/summarize", methods=["POST"])
def summarize_text(text_id):
    try:
        summary = text_services.summarize_text(text_id)
        text_services.update_text(text_id, {"summary": summary})
        return jsonify({"summary": summary}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@text_routes.route("/text/<text_id>/keywords", methods=["POST"])
def extract_keywords(text_id):
    try:
        keywords = text_services.get_text_keywords(text_id)
        text_services.update_text(text_id, {"keywords": keywords})
        return jsonify({"keywords": keywords}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@text_routes.route("/text/<text_id>/sentiment", methods=["POST"])
def analyze_sentiment(text_id):
    try:
        sentiment = text_services.analyze_sentiment(text_id)
        text_services.update_text(text_id, {"sentiment": sentiment})
        return jsonify(sentiment), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@text_routes.route("/text/tsne", methods=["POST"])
def tsne_visualization():
    texts = request.json.get("texts", [])

    if not texts or len(texts) < 2:
        return (
            jsonify({"message": "Not enough texts provided, at least 2 are required"}),
            400,
        )

    # Step 1: Convert texts to TF-IDF vectors
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(texts)

    n_samples = len(texts)
    perplexity = min(30, n_samples - 1)

    # Step 2: Apply T-SNE
    tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity)
    tsne_results = tsne.fit_transform(tfidf_matrix.toarray())

    # Step 3: Create a scatter plot
    plt.figure(figsize=(10, 8))
    plt.scatter(tsne_results[:, 0], tsne_results[:, 1], alpha=0.7)

    # Adding text labels to the points
    for i, txt in enumerate(texts):
        plt.annotate(txt[:10], (tsne_results[i, 0], tsne_results[i, 1]), fontsize=9)

    plt.title("T-SNE Visualization of Texts")
    plt.xlabel("T-SNE Component 1")
    plt.ylabel("T-SNE Component 2")

    # Step 4: Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)

    # Encode the plot as a base64
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")

    return jsonify({"image": img_base64}), 200


@text_routes.route("/text/search", methods=["POST"])
def search_text():
    query = request.json.get("query")

    if not query:
        return jsonify({"message": "Text and query are required"}), 400

    try:
        texts_cursor = db.text.aggregate(
            [{"$group": {"_id": 0, "texts": {"$push": "$text"}}}]
        )

        texts = list(texts_cursor)[0]["texts"]

        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(texts)

        query_vec = tfidf_vectorizer.transform([query])

        similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()

        similar_texts = sorted(
            [(texts[i], sim) for i, sim in enumerate(similarities)],
            key=lambda x: x[1],
            reverse=True,
        )[:3]

        return jsonify(similar_texts), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@text_routes.route("/text/<text_id>/categorize", methods=["POST"])
def categorize_text(text_id):
    try:
        category = text_services.categorize_text(text_id)
        text_services.update_text(text_id, {"category": category})
        return jsonify({"category": category}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
