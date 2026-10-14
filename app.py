import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv(override=True)

def get_config(key):
    if key in st.secrets:
        return st.secrets[key]
    return os.getenv(key)

ENDPOINT = get_config("AZURE_OPENAI_ENDPOINT")
API_KEY = get_config("AZURE_OPENAI_API_KEY")
DEPLOYMENT = get_config("AZURE_OPENAI_DEPLOYMENT")

client = OpenAI(
    base_url=ENDPOINT,
    api_key=API_KEY,
)

SYSTEM_PROMPT = """
Eres DataTrue AI, un analista experto de football americano.

Ayudas a coaches a:
- Analizar rivales a partir de exports de Hudl (Excel).
- Detectar tendencias ofensivas y defensivas.
- Diseñar planes de juego.
- Proponer ideas creativas de ataque y defensa.

Cuando recibas datos de un Excel:
- Busca patrones por down y distancia, formación, hash, personal.
- Cuantifica tendencias (porcentajes, frecuencias).
- Señala riesgos y oportunidades.
- Propón soluciones concretas y accionables.

No analices ni resumas ningún archivo automáticamente al recibirlo.
Espera a que el coach haga una pregunta o pida explícitamente el análisis.

Sé claro, directo y práctico, como un coordinador hablando con otro coach.
"""

st.set_page_config(page_title="DataTrue AI Coach Assistant", page_icon="🏈")
st.title("🏈 DataTrue AI Coach Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT, "visible": False}
    ]

def leer_archivo(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    return df.to_csv(index=False)

for msg in st.session_state.messages:
    if msg.get("visible", True):
        with st.chat_message(msg["role"]):
            if msg.get("attachment_name"):
                st.markdown(f"📎 **{msg['attachment_name']}**")
            else:
                st.markdown(msg["content"])

prompt = st.chat_input(
    "Escribe tu pregunta o idea...",
    accept_file=True,
    file_type=["xlsx", "csv"],
)

if prompt:
    texto_usuario = prompt.text or ""
    archivo = prompt["files"][0] if prompt["files"] else None

    with st.chat_message("user"):
        if archivo:
            st.markdown(f"📎 **{archivo.name}**")
        if texto_usuario:
            st.markdown(texto_usuario)

    if archivo:
        resumen = leer_archivo(archivo)
        st.session_state.messages.append({
            "role": "user",
            "content": f"Aquí está el Excel exportado de Hudl ({archivo.name}):\n\n{resumen}",
            "visible": True,
            "attachment_name": archivo.name,
        })

    if texto_usuario:
        st.session_state.messages.append({
            "role": "user",
            "content": texto_usuario,
            "visible": True,
        })

    with st.chat_message("assistant"):
        api_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=api_messages,
        )
        answer = response.choices[0].message.content
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer, "visible": True})