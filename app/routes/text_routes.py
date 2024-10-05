from flask import Blueprint, request, jsonify
from transformers import pipeline
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import io
import base64

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
