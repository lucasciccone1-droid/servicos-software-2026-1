import os

import gradio as gr
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_ENDPOINT = f"{BACKEND_URL}/api/v1/analisar"

SENTIMENT_ICONS = {"positivo": "😊", "neutro": "😐", "negativo": "😟"}
PRIORITY_LABELS = {"alta": "🔴 Alta", "média": "🟡 Média", "baixa": "🟢 Baixa"}


def analyze(text: str):
    if not text or len(text.strip()) < 3:
        return "Digite um feedback com pelo menos 3 caracteres.", {}

    try:
        response = requests.post(
            API_ENDPOINT,
            json={"texto": text.strip()},
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as error:
        return f"Não foi possível acessar o backend: `{error}`", {}

    sentiment = result["sentimento"]
    icon = SENTIMENT_ICONS.get(sentiment, "💬")
    confidence_percent = result["confianca"] * 100
    keywords = ", ".join(result["palavras_chave"]) or "nenhuma identificada"

    summary = f"""
### {icon} Sentimento: {sentiment.capitalize()}

- **Confiança do modelo:** {confidence_percent:.1f}%
- **Prioridade de atendimento:** {PRIORITY_LABELS.get(result["prioridade"], result["prioridade"])}
- **Palavras-chave:** {keywords}
- **Ação recomendada:** {result["acao_recomendada"]}
"""
    return summary, result


with gr.Blocks(title="Feedback Inteligente", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
# 💬 Feedback Inteligente
Analise comentários de clientes, identifique o sentimento e priorize o atendimento.
O frontend envia o texto para uma API REST executada em outro container.
"""
    )

    feedback_input = gr.Textbox(
        label="Feedback do cliente",
        placeholder="Ex.: Meu pedido chegou atrasado e o suporte não respondeu.",
        lines=5,
        max_lines=10,
    )
    analyze_button = gr.Button("Analisar feedback", variant="primary")

    with gr.Row():
        result_output = gr.Markdown(label="Resultado")
        json_output = gr.JSON(label="Resposta da API")

    gr.Examples(
        examples=[
            ["Adorei o produto, chegou antes do prazo e muito bem embalado!"],
            ["Gostaria de saber quando meu pedido será entregue."],
            ["O produto veio com defeito e preciso do reembolso urgente."],
        ],
        inputs=feedback_input,
    )

    analyze_button.click(analyze, feedback_input, [result_output, json_output])
    feedback_input.submit(analyze, feedback_input, [result_output, json_output])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
