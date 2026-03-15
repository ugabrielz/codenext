from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "code_next_chatbot"


api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("Coloque sua API key no arquivo .env")


client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

SYSTEM_PROMPT = """
Você é o assistente virtual comercial da Code Next.

A Code Next desenvolve:
- landing pages
- sites profissionais
- sistemas sob medida

Sua função é QUALIFICAR o lead.

Você deve descobrir, de forma natural:
- nome da pessoa
- nome da empresa
- segmento
- tipo de serviço desejado
- objetivo do projeto
- prazo, se possível

Regras muito importantes:
- Nunca diga que vai adicionar o cliente no WhatsApp.
- Nunca diga que vai chamar o cliente no WhatsApp.
- Nunca diga que você mesmo vai entrar em contato depois.
- Você não inicia contato com ninguém.
- O cliente é quem deve clicar no link do WhatsApp para continuar.
- Quando já tiver informações suficientes, faça um resumo organizado.
- Depois do resumo, diga apenas para o cliente continuar no WhatsApp da Code Next.
- Não invente informações.
- Não invente preços fechados.
- Faça perguntas curtas e naturais.
- Não repita perguntas já respondidas.

Formato desejado quando já tiver dados suficientes:

Resumo do atendimento:
- Nome:
- Empresa:
- Segmento:
- Serviço desejado:
- Objetivo:
- Prazo:

Depois do resumo, convide o cliente a continuar pelo WhatsApp da Code Next.
"""
@app.route("/")
def home():
    session["messages"] = []
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Digite uma mensagem para continuar."}), 400

    if "messages" not in session:
        session["messages"] = []

    messages = session["messages"]
    messages.append({"role": "user", "content": user_message})

    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=full_messages,
            temperature=0.7
        )

        reply = completion.choices[0].message.content
        messages.append({
            "role": "assistant",
            "content": reply
        })

        session["messages"] = messages

        resumo = gerar_resumo_para_whatsapp(messages)

        whatsapp_link = None
        if resumo:
            campos_preenchidos = sum(
                1 for linha in resumo.splitlines()
                if "Não informado" not in linha and ":" in linha
            )

            if campos_preenchidos >= 4:
                whatsapp_link = gerar_link_whatsapp(resumo)

        return jsonify({
            "reply": reply,
            "summary": resumo,
            "whatsapp_link": whatsapp_link
        })

    except Exception as e:
        print("ERRO:", e)
        return jsonify({
            "reply": "Ocorreu um erro ao falar com a IA."
        }), 500
def gerar_resumo_para_whatsapp(messages):
    resumo_prompt = """
Com base na conversa, gere um resumo curto e organizado do lead.

Retorne EXATAMENTE neste formato:

Nome: ...
Empresa: ...
Segmento: ...
Serviço: ...
Objetivo: ...
Prazo: ...

Se alguma informação não tiver sido informada, escreva: Não informado
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "system", "content": resumo_prompt}] + messages,
            temperature=0.3
        )

        return response.choices[0].message.content.strip()
    except:
        return None
from urllib.parse import quote

def gerar_link_whatsapp(resumo):
    texto = f"""Olá, Gabriel! Vim pelo chatbot da Code Next.

{resumo}"""
    return f"https://wa.me/5517991652450?text={quote(texto)}"

@app.route("/demo-orcamento")
def demo_orcamento():
    return render_template("demo-orcamento.html")

@app.route("/demo-financeiro")
def demo_financeiro():
    return render_template("demo_financeiro.html")
if __name__ == "__main__":
    app.run(debug=True)
