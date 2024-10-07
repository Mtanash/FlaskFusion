from transformers import pipeline
import spacy


summarizer = pipeline("summarization", model="t5-small")
sentiment_analyzer = pipeline("sentiment-analysis")
classifier = pipeline(
    model="lxyuan/distilbert-base-multilingual-cased-sentiments-student",
    return_all_scores=True,
)
nlp = spacy.load("en_core_web_sm")


class TextProcessingService:
    @staticmethod
    def summarize_text(text: str) -> str:
        summary = summarizer(text, max_length=100, min_length=10, do_sample=False)[0][
            "summary_text"
        ]
        return summary

    @staticmethod
    def get_text_keywords(text: str) -> list:
        doc = nlp(text)
        keywords = {
            token.text
            for token in doc
            if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop
        }
        return list(keywords)

    @staticmethod
    def analyze_sentiment(text: str) -> dict:
        result = sentiment_analyzer(text)[0]
        return {"label": result["label"], "score": result["score"]}

    @staticmethod
    def categorize_text(text: str) -> dict:
        categories = classifier(text)
        return {"categories": categories}
