import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
from supabase import create_client
import bcrypt

# -----------------------
# CONFIG & DESIGN WHATSAPP
# -----------------------
st.set_page_config(page_title="Assistant IA 🎓", layout="wide")

# CSS pour le bouton style WhatsApp et supprimer le rouge agressif
st.markdown("""
    <style>
    /* Bouton d'envoi style WhatsApp */
    button[kind="primary"] {
        background-color: #25D366 !important;
        color: white !important;
        border-radius: 50% !important;
        width: 45px !important;
        height: 45px !important;
        border: none !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12) !important;
    }
    
    /* Masquer le contour rouge des erreurs pour un look plus propre */
    .stException, .stAlert {
        border: none !important;
        background-color: #f0f2f5 !important;
        color: #1f1f1f !important;
    }
    
    /* Input arrondi */
    .stChatInput textarea {
        border-radius: 25px !important;
        padding-left: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------
# SUPABASE
# -----------------------

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------
# SESSION
# -----------------------

if "user" not in st.session_state:
    st.session_state.user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "loaded_history" not in st.session_state:
    st.session_state.loaded_history = False

# -----------------------
# PASSWORD
# -----------------------

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# -----------------------
# AUTH
# -----------------------

def register(username, password):
    existing = supabase.table("utilisateurs").select("*").eq("username", username).execute()

    if existing.data:
        st.error("Utilisateur existe déjà")
        return

    hashed = hash_password(password)

    supabase.table("utilisateurs").insert({
        "username": username,
        "password": hashed
    }).execute()

    st.success("Compte créé")

def login(username, password):
    data = supabase.table("utilisateurs").select("*").eq("username", username).execute()

    if not data.data:
        return False

    user = data.data[0]

    return check_password(password, user["password"])

# -----------------------
# MESSAGES DB
# -----------------------

def save_message(username, role, content):
    supabase.table("messages").insert({
        "username": username,
        "role": role,
        "content": content
    }).execute()

def load_messages(username):
    data = supabase.table("messages") \
        .select("*") \
        .eq("username", username) \
        .order("created_at") \
        .execute()

    return data.data if data.data else []

# -----------------------
# LOGIN UI
# -----------------------

if not st.session_state.user:

    st.title("🔐 Authentification")

    tab1, tab2 = st.tabs(["Connexion", "Créer compte"])

    with tab1:
        u = st.text_input("Nom")
        p = st.text_input("Mot de passe", type="password")

        if st.button("Se connecter"):
            if login(u, p):
                st.session_state.user = u
                st.success("Connecté")
                st.rerun()
            else:
                st.error("Erreur")

    with tab2:
        u2 = st.text_input("Nouveau nom")
        p2 = st.text_input("Mot de passe", type="password")

        if st.button("Créer compte"):
            register(u2, p2)

    st.stop()

# -----------------------
# SIDEBAR
# -----------------------

st.sidebar.write(f"👤 {st.session_state.user}")

if st.sidebar.button("Déconnexion"):
    st.session_state.user = None
    st.session_state.messages = []
    st.session_state.loaded_history = False
    st.rerun()

if st.sidebar.button("🗑️ Effacer historique"):
    supabase.table("messages").delete().eq("username", st.session_state.user).execute()
    st.session_state.messages = []
    st.rerun()

mode = st.sidebar.selectbox("Mode", ["Étudiant", "Enseignant"])

# -----------------------
# IA
# -----------------------

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def get_prompt():
    base = "Assistant académique. Réponds uniquement aux questions éducatives."

    if mode == "Étudiant":
        base += " Explique simplement."
    else:
        base += " Réponse détaillée."

    return base

# -----------------------
# VOIX
# -----------------------

def tts(text):
    t = gTTS(text=text, lang="fr")
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    t.save(f.name)
    return f.name

# -----------------------
# CHARGER HISTORIQUE
# -----------------------

if not st.session_state.loaded_history:
    history = load_messages(st.session_state.user)

    st.session_state.messages = [
        {"role": m["role"], "content": m["content"]}
        for m in history
    ]

    st.session_state.loaded_history = True

# -----------------------
# UI CHAT
# -----------------------

st.title("🎓 Assistant IA")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------
# INPUT (WHATSAPP STYLE)
# -----------------------

prompt = st.chat_input("Pose ta question...")

if prompt:

    st.chat_message("user").markdown(prompt)

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    save_message(st.session_state.user, "user", prompt)

# -----------------------
# REPONSE IA
# -----------------------

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":

    with st.chat_message("assistant"):

        full = ""
        placeholder = st.empty()

        messages = [{"role": "system", "content": get_prompt()}]

        for m in st.session_state.messages[-10:]:
            messages.append(m)

        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                placeholder.markdown(full + "▌")

        placeholder.markdown(full)

        audio = tts(full)
        st.audio(audio)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full
    })

    save_message(st.session_state.user, "assistant", full)
