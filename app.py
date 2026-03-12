import streamlit as st
from groq import Groq
import logging
from pathlib import Path
import PyPDF2

# -----------------------------
# CONFIG PAGE
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
# GROQ CLIENT
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
informatique, mathématiques, électronique, intelligence artificielle, programmation
Réponds toujours en français.
Structure tes réponses : titre, explication, exemple, conclusion.
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

    uploaded_pdf = st.file_uploader("📄 Charger un PDF de cours", type="pdf")

# -----------------------------
# EXTRACTION PDF
# -----------------------------
pdf_text=""
if uploaded_pdf:
    reader = PyPDF2.PdfReader(uploaded_pdf)
    for page in reader.pages:
        pdf_text += page.extract_text()
    st.success("PDF chargé")

# -----------------------------
# RESUME PDF
# -----------------------------
if pdf_text != "":
    if st.button("📚 Résumer le cours"):
        resume_prompt = f"Résume ce cours pour un étudiant : {pdf_text[:4000]}"
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":resume_prompt}],
            temperature=0.3,
            max_tokens=800
        )
        st.markdown("### 📘 Résumé")
        st.write(completion.choices[0].message.content)

# -----------------------------
# QCM
# -----------------------------
if pdf_text != "":
    if st.button("📝 Générer QCM"):
        qcm_prompt = f"Crée un QCM de 5 questions basé sur ce cours : {pdf_text[:4000]}"
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":qcm_prompt}],
            temperature=0.5,
            max_tokens=800
        )
        st.markdown("### 🧠 Test")
        st.write(completion.choices[0].message.content)

# -----------------------------
# MEMOIRE CHAT
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages=[]

# -----------------------------
# TITRE
# -----------------------------
st.title("🎓 Assistant Académique IA")
st.write("Posez vos questions académiques par texte ou par voix.")

# -----------------------------
# HISTORIQUE
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# QUESTION VOCALE
# -----------------------------
audio = st.audio_input("🎤 Parlez à l'assistant")
if audio is not None:
    transcription = client.audio.transcriptions.create(
        file=("audio.wav", audio.getvalue()),
        model="whisper-large-v3"
    )
    voice_prompt = transcription.text
    st.chat_message("user").markdown(voice_prompt)
    st.session_state.messages.append({"role":"user","content":voice_prompt})

# -----------------------------
# QUESTION TEXTE
# -----------------------------
prompt = st.chat_input("Posez votre question")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    st.chat_message("user").markdown(prompt)

# -----------------------------
# GENERATION IA
# -----------------------------
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"]=="user":
    with st.chat_message("assistant"):
        messages=[{"role":"system","content":SYSTEM_PROMPT}]
        for m in st.session_state.messages:
            messages.append(m)

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2,
            max_tokens=1000
        )

        response = completion.choices[0].message.content
        st.markdown(response)

        # VOIX IA
        st.markdown(f"""
        <script>
        var speech = new SpeechSynthesisUtterance(`{response}`);
        speech.lang="fr-FR";
        window.speechSynthesis.speak(speech);
        </script>
        """, unsafe_allow_html=True)

    st.session_state.messages.append({"role":"assistant","content":response})

# -----------------------------
# MODE APPEL VOCAL AMÉLIORÉ
# -----------------------------
st.divider()
st.subheader("📞 Mode appel vocal")

if "call_mode" not in st.session_state:
    st.session_state.call_mode=False

col1,col2=st.columns(2)
with col1:
    if st.button("📞 Démarrer appel"):
        st.session_state.call_mode=True
with col2:
    if st.button("❌ Terminer appel"):
        st.session_state.call_mode=False

if st.session_state.call_mode:
    st.info("🎤 Parlez avec le micro et validez l'enregistrement")

    audio_call = st.audio_input("Votre question")
    if audio_call is not None:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_call.getvalue()),
            model="whisper-large-v3"
        )
        question = transcription.text
        st.write("🧑 Vous :", question)

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":question}
            ],
            temperature=0.2,
            max_tokens=800
        )

        rep = completion.choices[0].message.content
        st.write("🤖 IA :", rep)

        # VOIX IA
        st.markdown(f"""
        <script>
        var speech = new SpeechSynthesisUtterance(`{rep}`);
        speech.lang="fr-FR";
        window.speechSynthesis.speak(speech);
        </script>
        """,unsafe_allow_html=True)

# -----------------------------
# FOOTER
# -----------------------------
st.divider()
st.markdown("Assistant académique développé par **Julien Banze Kandolo**")
