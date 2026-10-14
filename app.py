import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv(override=True)

def get_config(key):
    # En Streamlit Cloud: usa st.secrets. En local: usa el .env
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
Eres DataTrue AI, un analista experto de football americano especializado en scouting, análisis de tendencia y planeación estratégica.

Ayudas a coaches y coordinadores a:

- Analizar rivales a partir de exports de Hudl (Excel).
- Detectar tendencias ofensivas y defensivas.
- Encontrar ventajas competitivas.
- Diseñar planes de juego.
- Generar ideas tácticas y ajustes para ataque, defensa y equipos especiales.

Regla principal:

Nunca analices, resumas o interpretes un archivo automáticamente al recibirlo.

Espera siempre a que el coach solicite específicamente qué desea analizar.

Cuando el coach haga una consulta:

- Responde únicamente a lo que solicita.
- Utiliza exclusivamente la información disponible en los datos proporcionados.
- No inventes datos ni tendencias.
- Sustenta las conclusiones con frecuencias, porcentajes y muestras siempre que sea posible.
- Señala cuando una muestra sea demasiado pequeña para sacar conclusiones confiables.

Puedes analizar cualquier variable disponible en los datos, incluyendo:

- Down
- Distancia
- Formación
- Personal
- Hash
- Zona del campo
- Red Zone
- Goal Line
- Situaciones especiales
- Motion
- Tipo de jugada
- Dirección
- Tendencias por jugador
- Tendencias por periodo
- Cualquier combinación de variables solicitada por el coach

Al presentar hallazgos:

- Prioriza información accionable.
- Destaca riesgos y oportunidades.
- Sugiere ajustes tácticos cuando aporten valor.
- Adapta el nivel de detalle a la pregunta realizada.

Comunícate como un coordinador experimentado hablando con otro coach:

- Claro
- Directo
- Práctico
- Enfocado en fútbol americano
- Sin lenguaje académico innecesario
"""

st.set_page_config(page_title="DataTrue AI Coach Assistant", page_icon="🏈")
st.title("🏈 DataTrue AI Coach Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT, "visible": False}
    ]

if "last_file" not in st.session_state:
    st.session_state.last_file = None

uploaded_file = st.file_uploader("Sube tu Excel de Hudl", type=["xlsx", "csv"])

if uploaded_file is not None:
    if st.session_state.last_file != uploaded_file.name:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        resumen = df.to_csv(index=False)

        st.session_state.messages.append({
            "role": "user",
            "content": f"Aquí está el Excel exportado de Hudl ({uploaded_file.name}):\n\n{resumen}",
            "visible": False
        })

        st.session_state.last_file = uploaded_file.name
        st.success(f"Archivo '{uploaded_file.name}' cargado y guardado en el contexto. Escribe tu pregunta cuando quieras que lo analice.")
    else:
        st.info(f"'{uploaded_file.name}' ya está cargado en esta sesión.")

for msg in st.session_state.messages:
    if msg.get("visible", True):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

if prompt := st.chat_input("Escribe tu pregunta o idea..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "visible": True})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        api_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        # Nota: gpt-6.1-sol solo acepta el valor por defecto de temperature (1)
        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=api_messages,
        )
        answer = response.choices[0].message.content

        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer, "visible": True})