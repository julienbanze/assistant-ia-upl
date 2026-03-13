import streamlit as st
from groq import Groq
import logging
from pathlib import Path
import mysql.connector
import bcrypt
import PyPDF2

# -----------------------
# CONFIG PAGE
# -----------------------
st.set_page_config(
    page_title="Assistant Académique IA 🎓",
    page_icon="🎓",
    layout="wide"
)

# -----------------------
# DESIGN
# -----------------------
st.markdown("""
<style>
.main {background: linear-gradient(135deg,#1e3c72,#2a5298,#4a69bd)}
.stApp {background: linear-gradient(135deg,#1e3c72,#2a5298,#4a69bd)}

h1{color:#ffd700;text-align:center;font-size:2.8em;}
.stChatInput input{border-radius:25px;border:2px solid #ffd700;padding:12px;}
.sidebar .sidebar-content{background:#111;}
</style>
""", unsafe_allow_html=True)

# -----------------------
# LOGS
# -----------------------
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()]
)

# -----------------------
# GROQ CLIENT
# -----------------------
@st.cache_resource
def init_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("Ajoutez GROQ_API_KEY dans Settings > Secrets")
        st.stop()

client = init_client()

# -----------------------
# MYSQL CONNECTION
# -----------------------
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Met ton mot de passe XAMPP ici
        database="assistant_ia"
    )

# -----------------------
# FUNCTIONS
# -----------------------
def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password: str, hashed: str):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_user(nom, email, password):
    db = connect_db()
    cursor = db.cursor()
    hashed = hash_password(password)
    cursor.execute("INSERT INTO users (nom,email,password) VALUES (%s,%s,%s)", (nom,email,hashed))
    db.commit()
    db.close()

def get_user(email):
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    db.close()
    return user

def save_chat(user_id, role, message):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO chat_history (user_id,role,message) VALUES (%s,%s,%s)", (user_id, role, message))
    db.commit()
    db.close()

def save_pdf(user_id, nom_fichier, contenu):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO pdf_uploads (user_id, nom_fichier, contenu) VALUES (%s,%s,%s)", (user_id, nom_fichier, contenu))
    db.commit()
    db.close()

# -----------------------
# SESSION MANAGEMENT
# -----------------------
if "user" not in st.session_state:
    st.session_state.user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------
# AUTHENTICATION
# -----------------------
if st.session_state.user is None:
    st.title("Connexion / Inscription")
    tab = st.tabs(["Connexion","Inscription"])
    
    with tab[0]:
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            user = get_user(email)
            if user and check_password(password, user["password"]):
                st.session_state.user = user
                st.success(f"Bienvenue {user['nom']} !")
                st.experimental_rerun()
            else:
                st.error("Email ou mot de passe incorrect")

    with tab[1]:
        nom = st.text_input("Nom complet")
        email_reg = st.text_input("Email")
        password_reg = st.text_input("Mot de passe", type="password")
        if st.button("S'inscrire"):
            if get_user(email_reg):
                st.error("Email déjà utilisé")
            else:
                create_user(nom, email_reg, password_reg)
                st.success("Compte créé ! Vous pouvez maintenant vous connecter")

# -----------------------
# APP MAIN
# -----------------------
if st.session_state.user:
    st.markdown(f"## 🎓 Assistant Académique IA - Connecté comme {st.session_state.user['nom']}")
    
    # Sidebar
    with st.sidebar:
        if st.button("Déconnexion"):
            st.session_state.user = None
            st.session_state.messages = []
            st.experimental_rerun()
        uploaded_pdf = st.file_uploader("📄 Charger un PDF de cours", type="pdf")
    
    # PDF extraction
    pdf_text = ""
    if uploaded_pdf:
        reader = PyPDF2.PdfReader(uploaded_pdf)
        for page in reader.pages:
            pdf_text += page.extract_text()
        st.success("PDF chargé avec succès")
        save_pdf(st.session_state.user['id'], uploaded_pdf.name, pdf_text[:5000])
    
    # Voice input
    audio = st.audio_input("🎤 Posez votre question avec votre voix")
    if audio:
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio.getvalue()),
            model="whisper-large-v3"
        )
        voice_prompt = transcription.text.strip()
        if voice_prompt:
            st.chat_message("user").markdown(voice_prompt)
            st.session_state.messages.append({"role":"user","content":voice_prompt})
            save_chat(st.session_state.user['id'], "user", voice_prompt)

    # Text input
    prompt = st.chat_input("Posez votre question académique...")
    if prompt:
        st.session_state.messages.append({"role":"user","content":prompt})
        st.chat_message("user").markdown(prompt)
        save_chat(st.session_state.user['id'], "user", prompt)
    
    # IA Response
    if st.session_state.messages and st.session_state.messages[-1]["role"]=="user":
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            messages = [{"role":"system","content":"Tu es un assistant académique intelligent et réponds en français"}]
            if pdf_text: 
                messages.append({"role":"system","content":"Cours PDF fourni: "+pdf_text[:4000]})
            for msg in st.session_state.messages:
                # Detection du créateur
                if "julien banze kandolo" in msg["content"].lower():
                    full_response = "⚡ Cet assistant a été créé par Julien Banze Kandolo, passionné d'IA et d'éducation !"
                    placeholder.markdown(full_response)
                    save_chat(st.session_state.user['id'], "assistant", full_response)
                    break
                messages.append(msg)
            
            if not full_response:
                try:
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
                    save_chat(st.session_state.user['id'], "assistant", full_response)
                except Exception as e:
                    st.error(f"Erreur IA : {e}")
