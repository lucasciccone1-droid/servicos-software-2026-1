from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

from .model import calculate_priority, extract_keywords, recommend_action, train_model

ml_model = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global ml_model
    ml_model = train_model()
    yield
    ml_model = None


app = FastAPI(
    title="API de Análise de Feedbacks",
    description="Classifica feedbacks em português e sugere a prioridade de atendimento.",
    version="1.0.0",
    lifespan=lifespan,
)


class FeedbackRequest(BaseModel):
    texto: str = Field(min_length=3, max_length=2000)

    @field_validator("texto")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        clean_value = value.strip()
        if not clean_value:
            raise ValueError("O texto não pode estar vazio.")
        return clean_value


class FeedbackResponse(BaseModel):
    sentimento: str
    confianca: float
    probabilidades: dict[str, float]
    prioridade: str
    palavras_chave: list[str]
    acao_recomendada: str


@app.get("/")
def root():
    return {"mensagem": "API de Análise de Feedbacks", "documentacao": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok", "modelo_carregado": ml_model is not None}


@app.post("/api/v1/analisar", response_model=FeedbackResponse)
def analyze_feedback(payload: FeedbackRequest):
    probabilities = ml_model.predict_proba([payload.texto])[0]
    labels = ml_model.classes_
    probability_map = {
        label: round(float(probability), 4)
        for label, probability in zip(labels, probabilities)
    }
    sentiment = max(probability_map, key=probability_map.get)
    confidence = probability_map[sentiment]
    priority = calculate_priority(payload.texto, sentiment, confidence)

    return FeedbackResponse(
        sentimento=sentiment,
        confianca=confidence,
        probabilidades=probability_map,
        prioridade=priority,
        palavras_chave=extract_keywords(payload.texto),
        acao_recomendada=recommend_action(sentiment, priority),
    )
