import streamlit as st
from supabase import create_client, Client
from hashlib import sha256
from datetime import datetime
from groq import Groq
import logging
from pathlib import Path

# -----------------------
# CONFIGURATION BASE / GROQ
# -----------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def init_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("Ajoutez GROQ_API_KEY dans Settings > Secrets")
        st.stop()

client = init_client()

# -----------------------
# LOGS
# -----------------------
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# -----------------------
# SESSION STATE
# -----------------------
if "user" not in st.session_state:
    st.session_state.user = None

# -----------------------
# UTILS
# -----------------------
def hash_password(password):
    return sha256(password.encode()).hexdigest()

def login(email, password):
    hashed = hash_password(password)
    res = supabase.table("users").select("*").eq("email", email).eq("password", hashed).execute()
    if res.data and len(res.data) > 0:
        return res.data[0]
    return None

def register(nom, email, password):
    exists = supabase.table("users").select("*").eq("email", email).execute()
    if exists.data and len(exists.data) > 0:
        return None
    hashed = hash_password(password)
    res = supabase.table("users").insert({
        "nom": nom,
        "email": email,
        "password": hashed,
        "date_inscription": datetime.now()
    }).execute()
    return res.data[0]

def save_message(user_id, question, reponse):
    supabase.table("messages").insert({
        "user_id": user_id,
        "question": question,
        "reponse": reponse,
        "date": datetime.now()
    }).execute()

def get_user_messages(user_id):
    res = supabase.table("messages").select("*").eq("user_id", user_id).order("date", desc=True).execute()
    return res.data

def get_all_messages():
    res = supabase.table("messages").select("*").order("date", desc=True).execute()
    return res.data

# -----------------------
# INTERFACE STREAMLIT
# -----------------------
st.set_page_config(page_title="Assistant Académique IA 🎓", page_icon="🎓", layout="wide")
st.title("🎓 Assistant Académique IA")

# -----------------------
# LOGIN / INSCRIPTION
# -----------------------
if st.session_state.user is None:
    tab1, tab2 = st.tabs(["Connexion", "Inscription"])
    
    with tab1:
        st.subheader("Connexion")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Mot de passe", type="password", key="login_pwd")
        if st.button("Se connecter"):
            user = login(email, password)
            if user:
                st.session_state.user = user
                st.success(f"Bienvenue {user['nom']} !")
            else:
                st.error("Email ou mot de passe incorrect")

    with tab2:
        st.subheader("Inscription")
        nom = st.text_input("Nom complet", key="reg_nom")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Mot de passe", type="password", key="reg_pwd")
        if st.button("S'inscrire"):
            user = register(nom, email, password)
            if user:
                st.session_state.user = user
                st.success(f"Inscription réussie. Bienvenue {user['nom']} !")
            else:
                st.error("Email déjà utilisé")

# -----------------------
# UTILISATEUR CONNECTÉ
# -----------------------
else:
    user = st.session_state.user
    st.write(f"Connecté en tant que : **{user['nom']}**")

    # -----------------------
    # INPUT VOCALE
    # -----------------------
    audio = st.audio_input("🎤 Posez votre question avec votre voix")
    prompt = None
    if audio is not None:
        try:
            transcription = client.audio.transcriptions.create(
                file=("audio.wav", audio.getvalue()),
                model="whisper-large-v3"
            )
            prompt = transcription.text.strip()
            if prompt:
                st.markdown(f"**Vous avez dit :** {prompt}")
        except Exception:
            st.warning("Erreur lors de la transcription vocale")

    # -----------------------
    # INPUT TEXTE
    # -----------------------
    if prompt is None:
        prompt = st.text_input("Posez votre question académique…")

    if prompt:
        try:
            # Appel Groq IA
            messages_payload = [
                {"role": "system", "content": "Tu es un assistant académique intelligent. Réponds en français. Structure : Titre, Introduction, Explication, Conclusion."},
                {"role": "user", "content": prompt}
            ]
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages_payload,
                stream=False,
                temperature=0.2,
                max_tokens=1500
            )
            reponse = response.choices[0].message.content

            # Sauvegarde
            save_message(user["id"], prompt, reponse)
            st.success("Message enregistré !")
            st.markdown(f"**Réponse IA :** {reponse}")

        except Exception as e:
            st.error(f"Erreur IA : {e}")

    # -----------------------
    # Historique messages utilisateur
    # -----------------------
    st.subheader("Mes messages")
    messages_user = get_user_messages(user["id"])
    for msg in messages_user:
        st.markdown(f"**Q:** {msg['question']}  \n**R:** {msg['reponse']}  \n*{msg['date']}*")

    # -----------------------
    # PANEL ADMIN
    # -----------------------
    if user["email"] == "tonemail@example.com":  # remplace par ton email admin
        st.subheader("Panel Admin : Tous les messages")
        all_msgs = get_all_messages()
        for msg in all_msgs:
            st.markdown(f"**User ID:** {msg['user_id']}  \n**Q:** {msg['question']}  \n**R:** {msg['reponse']}  \n*{msg['date']}*")
