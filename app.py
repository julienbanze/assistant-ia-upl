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
informatique, mathématiques, électronique, intelligence artificielle, programmation.
Réponds toujours en français.

Règles supplémentaires :
1. Si la question est impolie ou insultante, refuse poliment.
2. Si la question mentionne "Julien Banze Kandolo" ou variantes, affiche un message respectueux pour le créateur.
3. Reconnais et explique correctement les abréviations courantes (ex: UPL = Université Protestante de Lubumbashi).
4. Tu peux répéter la question dans une autre langue (anglais ou espagnol) mais réponds toujours en français.
5. Structure les réponses : Titre, Explication, Exemple, Conclusion.
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
    st.success("PDF chargé avec succès")

# -----------------------------
# MEMOIRE CHAT
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages=[]

# -----------------------------
# TITRE
# -----------------------------
st.title("🎓 Assistant Académique IA")
st.write("Posez vos questions académiques en français. L’IA peut répéter la question dans une autre langue et répondra en français.")

# -----------------------------
# HISTORIQUE
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# QUESTION TEXTE
# -----------------------------
prompt = st.chat_input("Posez votre question")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    st.chat_message("user").markdown(prompt)

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

        # Vérification créateur
        if "julien banze kandolo" in question.lower():
            rep = "🙏 Ce projet a été créé par Julien Banze Kandolo, merci de le respecter !"
        else:
            # Génération IA
            messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":question}]
            if pdf_text!="":
                messages.append({"role":"system","content":"Cours fourni par l'utilisateur :"+pdf_text[:4000]})
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
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
        """, unsafe_allow_html=True)

        # Ajouter à la mémoire
        st.session_state.messages.append({"role":"assistant","content":rep})

# -----------------------------
# GENERATION IA TEXTE + VOIX (non appel)
# -----------------------------
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"]=="user" and not st.session_state.call_mode:
    with st.chat_message("assistant"):
        messages=[{"role":"system","content":SYSTEM_PROMPT}]
        for m in st.session_state.messages:
            messages.append(m)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2,
            max_tokens=1200
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
# FOOTER
# -----------------------------
st.divider()
st.markdown("Assistant académique intelligent développé par **Julien Banze Kandolo**")
