import streamlit as st
from groq import Groq
import logging
from pathlib import Path
import pandas as pd
import PyPDF2

# -----------------------------
# CONFIGURATION PAGE
# -----------------------------

st.set_page_config(
    page_title="Assistant Académique IA",
    page_icon="🎓",
    layout="wide"
)

# -----------------------------
# DESIGN
# -----------------------------

st.markdown("""
<style>

.stApp{
background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
color:white;
}

h1{
color:#FFD700;
text-align:center;
}

.stChatInput input{
border-radius:25px;
border:2px solid gold;
padding:12px;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOGS
# -----------------------------

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
level=logging.INFO,
handlers=[
logging.FileHandler("logs/app.log"),
logging.StreamHandler()
]
)

# -----------------------------
# CLIENT GROQ
# -----------------------------

@st.cache_resource
def init_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

client = init_client()

# -----------------------------
# PROMPT SYSTEME
# -----------------------------

SYSTEM_PROMPT = """
Tu es un assistant académique expert.

Tu aides les étudiants dans :

informatique
mathématiques
électronique
intelligence artificielle
programmation

Réponds toujours en français.

Structure tes réponses :

Titre
Explication claire
Exemple
Conclusion
"""

# -----------------------------
# SIDEBAR
# -----------------------------

with st.sidebar:

    st.title("🎓 Assistant IA")

    st.markdown("Développé par **Julien Banze Kandolo**")

    st.divider()

    if st.button("Nouvelle conversation"):
        st.session_state.messages=[]
        st.rerun()

    st.divider()

    uploaded_pdf = st.file_uploader(
        "📄 Charger un PDF de cours",
        type="pdf"
    )

# -----------------------------
# EXTRACTION PDF
# -----------------------------

pdf_text=""

if uploaded_pdf:

    reader = PyPDF2.PdfReader(uploaded_pdf)

    for page in reader.pages:
        pdf_text += page.extract_text()

    st.success("PDF chargé avec succès")

# -----------------------------
# RESUME PDF
# -----------------------------

if pdf_text != "":

    if st.button("📚 Résumer le cours"):

        with st.spinner("Analyse du cours..."):

            resume_prompt = f"""
            Résume ce cours pour un étudiant.

            Structure :
            - Titre
            - Concepts principaux
            - Explication simple
            - Conclusion

            {pdf_text[:4000]}
            """

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"user","content":resume_prompt}],
                temperature=0.3,
                max_tokens=1000
            )

            st.markdown("### 📘 Résumé du cours")

            st.write(completion.choices[0].message.content)

# -----------------------------
# GENERER QCM
# -----------------------------

if pdf_text != "":

    if st.button("📝 Générer un QCM"):

        with st.spinner("Création du test..."):

            qcm_prompt = f"""
            Crée un QCM de 5 questions pour réviser ce cours.

            Format :

            Question
            A)
            B)
            C)
            D)

            Puis donne les réponses correctes.

            {pdf_text[:4000]}
            """

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"user","content":qcm_prompt}],
                temperature=0.5,
                max_tokens=1000
            )

            st.markdown("### 🧠 Test de révision")

            st.write(completion.choices[0].message.content)

# -----------------------------
# MEMOIRE
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages=[]

# -----------------------------
# TITRE
# -----------------------------

st.title("🎓 Assistant Académique IA")

st.write("Posez vos questions académiques par texte ou par voix.")

# -----------------------------
# HISTORIQUE CHAT
# -----------------------------

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# QUESTION VOCALE
# -----------------------------

audio = st.audio_input("🎤 Posez votre question avec votre voix")

if audio is not None:

    transcription = client.audio.transcriptions.create(
        file=("audio.wav", audio.getvalue()),
        model="whisper-large-v3"
    )

    voice_prompt = transcription.text

    st.chat_message("user").markdown(voice_prompt)

    st.session_state.messages.append({
        "role":"user",
        "content":voice_prompt
    })

# -----------------------------
# QUESTION TEXTE
# -----------------------------

prompt = st.chat_input("Posez votre question académique...")

if prompt:

    st.session_state.messages.append({
        "role":"user",
        "content":prompt
    })

    st.chat_message("user").markdown(prompt)

# -----------------------------
# GENERATION IA
# -----------------------------

if len(st.session_state.messages)>0 and st.session_state.messages[-1]["role"]=="user":

    with st.chat_message("assistant"):

        placeholder = st.empty()

        full_response=""

        messages=[{"role":"system","content":SYSTEM_PROMPT}]

        if pdf_text!="":
            messages.append({
                "role":"system",
                "content":"Voici un cours PDF fourni :"+pdf_text[:4000]
            })

        for m in st.session_state.messages:
            messages.append(m)

        stream = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=messages,

            stream=True,

            temperature=0.2,

            max_tokens=1500
        )

        for chunk in stream:

            if chunk.choices[0].delta.content:

                full_response += chunk.choices[0].delta.content

                placeholder.markdown(full_response+"▌")

        placeholder.markdown(full_response)

        # -----------------------------
        # REPONSE VOCALE
        # -----------------------------

        st.markdown(f"""
        <script>

        var text = `{full_response}`;

        var speech = new SpeechSynthesisUtterance(text);

        speech.lang = "fr-FR";

        speech.rate = 1;

        speech.pitch = 1;

        window.speechSynthesis.speak(speech);

        </script>
        """, unsafe_allow_html=True)

    st.session_state.messages.append({
        "role":"assistant",
        "content":full_response
    })

# -----------------------------
# HISTORIQUE SIDEBAR
# -----------------------------

st.sidebar.divider()

st.sidebar.subheader("📜 Historique des questions")

for msg in st.session_state.messages:

    if msg["role"]=="user":
        st.sidebar.write("•", msg["content"])

# -----------------------------
# FOOTER
# -----------------------------

st.divider()

st.markdown(
"Assistant académique intelligent développé par **Julien Banze Kandolo**"
)
