import streamlit as st
from streamlit_mic_recorder import mic_recorder
from groq import Groq

# --- CONFIGURATION ---
st.set_page_config(page_title="Assistant Académique UPL", layout="centered")

# CSS pour affiner l'interface
st.markdown("""
    <style>
    .stChatInputContainer {
        padding-bottom: 20px;
    }
    .library-link {
        font-size: 14px;
        text-decoration: none;
        color: #00aaff;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ENTÊTE : LOGO + TITRE + LIEN BIBLIOTHÈQUE ---
col1, col2 = st.columns([0.15, 0.85])

with col1:
    # Affiche le logo (assure-toi que le fichier existe à la racine)
    st.image("logo.png", width=65)

with col2:
    st.title("Assistant Académique IA")
    # Lien vers la bibliothèque placé juste sous le titre ou à droite
    st.markdown('<a href="https://upl.ac.cd/bibliotheque/" target="_blank" class="library-link">📚 Accéder à la Bibliothèque Numérique UPL</a>', unsafe_allow_html=True)

st.write("---")

# --- INITIALISATION ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- AFFICHAGE DE L'HISTORIQUE ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- ZONE DE SAISIE (MICRO EN HAUT) ---
st.write("#### Pose ta question")

# Le micro est placé ici, donc au-dessus de st.chat_input
audio_zone = st.container()
with audio_zone:
    audio = mic_recorder(
        start_prompt="Enregistrer une question vocale 🎤",
        stop_prompt="Arrêter l'enregistrement ",
        key='recorder'
    )

# La barre de saisie de texte (toujours en bas par défaut dans Streamlit)
prompt = st.chat_input("Écris ton message ici...")

# --- LOGIQUE DE TRAITEMENT ---
if audio:
    # Note: Logique à compléter avec Groq Whisper pour transcrire l'audio
    st.info("Audio reçu. Analyse en cours...")
    # prompt = transcription_resultat

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        )
        response = st.write_stream(stream)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
