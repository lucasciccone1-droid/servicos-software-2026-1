import csv
import re
import unicodedata
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "feedbacks.csv"

URGENT_TERMS = {
    "cancelar",
    "cancelamento",
    "defeito",
    "devolver",
    "estorno",
    "fraude",
    "péssimo",
    "procon",
    "reclamação",
    "reembolso",
    "urgente",
}

DOMAIN_TERMS = {
    "aplicativo",
    "atendimento",
    "compra",
    "entrega",
    "pedido",
    "produto",
    "qualidade",
    "reembolso",
    "site",
    "suporte",
    "troca",
}

STOPWORDS = {
    "a",
    "ao",
    "as",
    "com",
    "da",
    "de",
    "do",
    "e",
    "em",
    "esta",
    "foi",
    "muito",
    "na",
    "no",
    "o",
    "os",
    "para",
    "por",
    "que",
    "um",
    "uma",
}


def normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def load_training_data() -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []
    with DATASET_PATH.open(encoding="utf-8", newline="") as dataset:
        for row in csv.DictReader(dataset):
            texts.append(row["texto"])
            labels.append(row["sentimento"])
    return texts, labels


def train_model() -> Pipeline:
    texts, labels = load_training_data()
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    min_df=1,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=42,
                    solver="liblinear",
                ),
            ),
        ]
    )
    pipeline.fit(texts, labels)
    return pipeline


def extract_keywords(text: str, limit: int = 5) -> list[str]:
    words = re.findall(r"[a-záàâãéèêíïóôõöúçñ]+", text.lower())
    unique_words: list[str] = []
    for word in words:
        if len(word) < 4 or word in STOPWORDS or word in unique_words:
            continue
        unique_words.append(word)

    domain_first = sorted(
        unique_words,
        key=lambda word: (normalize(word) not in DOMAIN_TERMS, words.index(word)),
    )
    return domain_first[:limit]


def calculate_priority(text: str, sentiment: str, confidence: float) -> str:
    normalized = normalize(text)
    contains_urgent_term = any(normalize(term) in normalized for term in URGENT_TERMS)
    if sentiment == "negativo" and (contains_urgent_term or confidence >= 0.65):
        return "alta"
    if sentiment == "negativo" or contains_urgent_term:
        return "média"
    return "baixa"


def recommend_action(sentiment: str, priority: str) -> str:
    if priority == "alta":
        return (
            "Encaminhar imediatamente para atendimento humano e acompanhar a resolução."
        )
    if sentiment == "negativo":
        return "Responder com empatia, entender o problema e oferecer uma solução."
    if sentiment == "positivo":
        return "Agradecer o feedback e considerar o cliente para ações de fidelização."
    return "Registrar o comentário e solicitar mais detalhes caso seja necessário."
