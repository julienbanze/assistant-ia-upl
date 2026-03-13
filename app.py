import streamlit as st
from groq import Groq
import logging
from pathlib import Path
import mysql.connector
import bcrypt

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
.main {background: linear-gradient(135deg,#1e3c72,#2a5298,#4a69bd);}
.stApp {background: linear-gradient(135deg,#1e3c72,#2a5298,#4a69bd);}
h1{color:#ffd700;text-align:center;font-size:2.8em;}
.stChatInput input{border-radius:25px;border:2px solid #ffd700;padding:12px;}
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
# DATABASE CONNECTION
# -----------------------
def connect_db():
    return mysql.connector.connect(
        host=st.secrets["DB_HOST"],        # ex: remotemysql.com
        port=st.secrets["DB_PORT"],        # ex: 3306
        user=st.secrets["DB_USER"],        # ex: user
        password=st.secrets["DB_PASS"],    # ex: password
        database=st.secrets["DB_NAME"]     # ex: assistant_ia
    )

def register_user(fullname, email, password):
    db = connect_db()
    cursor = db.cursor()
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        cursor.execute(
            "INSERT INTO users (fullname,email,password) VALUES (%s,%s,%s)",
            (fullname,email,hashed_pw)
        )
        db.commit()
        return True
    except mysql.connector.Error:
        return False
    finally:
        cursor.close()
        db.close()

def login_user(email,password):
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        return user
    return None

def save_chat(user_id, question, response):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO chats (user_id, question, response) VALUES (%s,%s,%s)",
                   (user_id, question, response))
    db.commit()
    cursor.close()
    db.close()

# -----------------------
# SYSTEM PROMPT
# -----------------------
SYSTEM_PROMPT = """
Tu es un assistant académique intelligent.
Réponds toujours en français.
Structure ta réponse : Titre, Introduction, Explication, Conclusion
"""

# -----------------------
# SESSION
# -----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user" not in st.session_state:
    st.session_state.user = None

# -----------------------
# AUTHENTIFICATION
# -----------------------
st.sidebar.title("Connexion / Inscription")
choice = st.sidebar.radio("Action", ["Connexion","Inscription"])

if choice=="Inscription":
    fullname = st.sidebar.text_input("Nom complet")
    email_reg = st.sidebar.text_input("Email")
    password_reg = st.sidebar.text_input("Mot de passe",type="password")
    if st.sidebar.button("S'inscrire"):
        if register_user(fullname,email_reg,password_reg):
            st.sidebar.success("Inscription réussie ! Connectez-vous.")
        else:
            st.sidebar.error("Erreur : Email déjà utilisé.")

if choice=="Connexion":
    email = st.sidebar.text_input("Email",key="login_email")
    password = st.sidebar.text_input("Mot de passe",type="password",key="login_pass")
    if st.sidebar.button("Se connecter"):
        user = login_user(email,password)
        if user:
            st.session_state.user = user
            st.sidebar.success(f"Connecté : {user['fullname']}")
        else:
            st.sidebar.error("Email ou mot de passe incorrect")

# -----------------------
# MAIN CHAT
# -----------------------
if st.session_state.user:
    st.title("🎓 Assistant Académique IA")
    st.write("Posez vos questions académiques par texte ou par voix.")

    # HISTORIQUE
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # INPUT
    prompt = st.chat_input("Posez votre question académique...")
    if prompt:
        # Filtrer les mauvaises questions
        lower_prompt = prompt.lower()
        forbidden = ["drague","insulte","spam","offense"]
        if any(word in lower_prompt for word in forbidden):
            st.chat_message("assistant").markdown("❌ Désolé, je ne peux pas répondre à cette question.")
        else:
            st.session_state.messages.append({"role":"user","content":prompt})
            with st.chat_message("assistant"):
                placeholder = st.empty()
                full_response=""
                messages = [{"role":"system","content":SYSTEM_PROMPT}]
                for m in st.session_state.messages:
                    messages.append(m)
                # Reconnaître le créateur
                if "julien banze" in prompt.lower():
                    full_response = "👏 Vous posez une question sur le créateur ! Julien Banze Kandolo est passionné par l'IA et l'éducation."
                    placeholder.markdown(full_response)
                else:
                    # GENERATION IA
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
                # SAUVEGARDE CHAT
                save_chat(st.session_state.user["id"], prompt, full_response)
                st.session_state.messages.append({"role":"assistant","content":full_response})

    # FOOTER
    st.markdown("---")
    st.markdown(f"Connecté : {st.session_state.user['fullname']} | Développé par Julien Banze Kandolo")
