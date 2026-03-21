import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
from supabase import create_client
import bcrypt
import os

# --- 1. CONFIGURATION & DESIGN WHATSAPP ---
st.set_page_config(page_title="Assistant IA 🎓", layout="wide")

# CSS pour supprimer le rouge et styliser comme WhatsApp
st.markdown("""
    <style>
    /* Supprimer les bordures rouges par défaut de Streamlit sur les erreurs */
    .stAlert { border: 1px solid #ddd; border-left: 5px solid #ff4b4b; background-color: #f9f9f9; color: black; }
    
    /* Style de la zone d'input (plus arrondi comme WhatsApp) */
    .stChatInput textarea {
        border-radius: 20px !important;
        border: 1px solid #ececec !important;
    }

    /* Personnalisation du bouton d'envoi (couleur verte WhatsApp) */
    button[kind="primary"] {
        background-color: #25D366 !important;
        border-color: #25D366 !important;
        color: white !important;
    }
    
    /* Fond de page plus doux */
    .stApp {
        background-color: #f0f2f5;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALISATION ---
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. CONNEXION SUPABASE ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    st.error("⚠️ Config manquante dans les Secrets.")
    st.stop()

# --- 4. FONCTIONS ---
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    try: return bcrypt.checkpw(password.encode(), hashed.encode())
    except: return False

def save_msg_to_db(user, role, content):
    try:
        supabase.table("messages").insert({"username": user, "role": role, "content": content}).execute()
    except: pass

def load_chat_history(username):
    try:
        res = supabase.table("messages").select("*").eq("username", username).order("created_at").execute()
        return [{"role": m["role"], "content": m["content"]} for m in res.data]
    except: return []

# --- 5. AUTHENTIFICATION ---
if st.session_state.user is None:
    st.title("🔐 Assistant Académique")
    tab1, tab2 = st.tabs(["Connexion", "Créer un compte"])

    with tab1:
        u = st.text_input("Nom d'utilisateur", key="login_u")
        p = st.text_input("Mot de passe", type="password", key="login_p")
        if st.button("Se connecter", use_container_width=True):
            try:
                res = supabase.table("utilisateurs").select("*").eq("username", u).execute()
                if res.data and check_password(p, res.data[0]["password"]):
                    st.session_state.user = u
                    st.session_state.messages = load_chat_history(u)
                    st.rerun()
                else: st.error("Identifiants incorrects.")
            except: st.error("Erreur de base de données. Vérifiez vos tables.")

    with tab2:
        u2 = st.text_input("Pseudo", key="reg_u")
        p2 = st.text_input("Mot de passe ", type="password", key="reg_p")
        if st.button("S'inscrire", use_container_width=True):
            if u2 and p2:
                try:
                    supabase.table("utilisateurs").insert({"username": u2, "password": hash_password(p2)}).execute()
                    st.success("Compte créé !")
                except: st.error("Pseudo déjà pris.")
    st.stop()

# --- 6. INTERFACE CHAT ---
st.sidebar.title(f"👤 {st.session_state.user}")
mode = st.sidebar.selectbox("Mode", ["Étudiant", "Enseignant"])

if st.sidebar.button("🗑️ Effacer l'historique"):
    try:
        supabase.table("messages").delete().eq("username", st.session_state.user).execute()
        st.session_state.messages = []
        st.rerun()
    except: pass

if st.sidebar.button("Déconnexion"):
    st.session_state.clear()
    st.rerun()

# --- 7. LOGIQUE IA ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Zone de saisie stylisée WhatsApp
if prompt := st.chat_input("Tapez votre message..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_msg_to_db(st.session_state.user, "user", prompt)

    with st.chat_message("assistant"):
        full_res = ""
        placeholder = st.empty()
        
        system_prompt = "Tu es un assistant académique. " + ("Explique simplement." if mode == "Étudiant" else "Sois technique.")
        context = [{"role": "system", "content": system_prompt}] + st.session_state.messages[-6:]

        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=context,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                placeholder.markdown(full_res + "▌")
        
        placeholder.markdown(full_res)

        try:
            tts = gTTS(text=full_res[:300], lang='fr')
            f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts.save(f.name)
            st.audio(f.name)
        except: pass

    st.session_state.messages.append({"role": "assistant", "content": full_res})
    save_msg_to_db(st.session_state.user, "assistant", full_res)
