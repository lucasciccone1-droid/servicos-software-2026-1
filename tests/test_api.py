from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "modelo_carregado": True}


def test_feedback_analysis_contract():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analisar",
            json={
                "texto": "O produto veio com defeito e preciso de reembolso urgente."
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["sentimento"] in {"positivo", "neutro", "negativo"}
        assert 0 <= result["confianca"] <= 1
        assert set(result["probabilidades"]) == {"positivo", "neutro", "negativo"}
        assert result["prioridade"] == "alta"
        assert isinstance(result["palavras_chave"], list)
        assert result["acao_recomendada"]


def test_model_classifies_the_three_sentiments():
    examples = {
        "positivo": "Excelente atendimento, adorei a experiência!",
        "neutro": "Qual é o prazo previsto para a entrega?",
        "negativo": "Péssimo suporte, ninguém resolveu meu problema.",
    }

    with TestClient(app) as client:
        for expected_sentiment, text in examples.items():
            response = client.post("/api/v1/analisar", json={"texto": text})
            assert response.status_code == 200
            assert response.json()["sentimento"] == expected_sentiment


def test_blank_feedback_is_rejected():
    with TestClient(app) as client:
        response = client.post("/api/v1/analisar", json={"texto": "   "})
        assert response.status_code == 422
