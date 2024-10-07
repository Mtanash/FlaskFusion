from app.db.db import db
from bson import ObjectId
from transformers import pipeline
import spacy


summarizer = pipeline("summarization", model="t5-small")
sentiment_analyzer = pipeline("sentiment-analysis")

classifier = pipeline(
    model="lxyuan/distilbert-base-multilingual-cased-sentiments-student",
    return_all_scores=True,
)


nlp = spacy.load("en_core_web_sm")


def create_text(text: str) -> dict:
    db.text.insert_one({"text": text})
    return {"message": "Text created successfully"}


def update_text(id: str, data: dict) -> dict:
    db.text.update_one({"_id": id}, {"$set": data})
    return {"message": "Text updated successfully"}


def delete_text(id: str) -> dict:
    db.text.delete_one({"_id": id})
    return {"message": "Text deleted successfully"}


def get_text(page: int = 1, page_size: int = 10) -> dict:
    skip = (page - 1) * page_size
    limit = page_size
    data_cursor = db.text.aggregate(
        [
            {"$skip": skip},
            {"$limit": limit},
            {"$addFields": {"_id": {"$toString": "$_id"}}},
        ]
    )
    data = list(data_cursor)
    total = db.text.count_documents({})
    return {"data": data, "total": total}


def get_text_by_id(id: str) -> dict:
    return db.text.find_one({"_id": ObjectId(id)})


def summarize_text(text: str) -> str:

    summary = summarizer(text, max_length=100, min_length=10, do_sample=False)[0][
        "summary_text"
    ]
    return summary


def get_text_keywords(text: str) -> list:

    doc = nlp(text)
    keywords = set()

    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop:
            keywords.add(token.text)

    return list(keywords)


def analyze_sentiment(text: str) -> dict:
    result = sentiment_analyzer(text)
    sentiment = result[0]

    return {"label": sentiment["label"], "score": sentiment["score"]}


def categorize_text(text: str) -> dict:
    categories = classifier(text)

    return {"categories": categories}
