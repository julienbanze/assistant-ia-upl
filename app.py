import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
from supabase import create_client
import bcrypt

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="Assistant IA 🎓", layout="wide")

# Initialisation propre du session_state
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------
# SUPABASE
# -----------------------
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Erreur de connexion à Supabase. Vérifiez vos secrets.")
    st.stop()

# -----------------------
# FONCTIONS AUTH & DB
# -----------------------
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def register(username, password):
    if not username or not password:
        st.warning("Veuillez remplir tous les champs.")
        return
    
    existing = supabase.table("utilisateurs").select("*").eq("username", username).execute()
    if existing.data:
        st.error("Ce nom d'utilisateur existe déjà.")
        return

    hashed = hash_password(password)
    supabase.table("utilisateurs").insert({"username": username, "password": hashed}).execute()
    st.success("Compte créé avec succès ! Connectez-vous.")

def login(username, password):
    if not username or not password:
        return False
    data = supabase.table("utilisateurs").select("*").eq("username", username).execute()
    if not data.data:
        return False
    user = data.data[0]
    return check_password(password, user["password"])

def save_message(username, role, content):
    try:
        supabase.table("messages").insert({
            "username": username,
            "role": role,
            "content": content
        }).execute()
    except Exception as e:
        st.error(f"Erreur sauvegarde : {e}")

@st.cache_data(show_spinner=False)
def load_messages_from_db(username):
    data = supabase.table("messages").select("*").eq("username", username).order("created_at").execute()
    return [{"role": m["role"], "content": m["content"]} for m in data.data] if data.data else []

# -----------------------
# UI AUTHENTIFICATION
# -----------------------
if st.session_state.user is None:
    st.title("🔐 Assistant Académique")
    tab1, tab2 = st.tabs(["Connexion", "Créer un compte"])

    with tab1:
        u = st.text_input("Nom d'utilisateur", key="login_user")
        p = st.text_input("Mot de passe", type="password", key="login_pass")
        if st.button("Se connecter"):
            if login(u, p):
                st.session_state.user = u
                # Charger l'historique une seule fois à la connexion
                st.session_state.messages = load_messages_from_db(u)
                st.rerun()
            else:
                st.error("Identifiants incorrects")

    with tab2:
        u2 = st.text_input("Nouveau nom", key="reg_user")
        p2 = st.text_input("Nouveau mot de passe", type="password", key="reg_pass")
        if st.button("Créer le compte"):
            register(u2, p2)
    st.stop()

# -----------------------
# INTERFACE PRINCIPALE
# -----------------------
st.sidebar.title(f"👤 {st.session_state.user}")
mode = st.sidebar.selectbox("Mode de réponse", ["Étudiant", "Enseignant"])

if st.sidebar.button("🗑️ Effacer l'historique"):
    supabase.table("messages").delete().eq("username", st.session_state.user).execute()
    st.session_state.messages = []
    st.rerun()

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.session_state.messages = []
    st.rerun()

# -----------------------
# LOGIQUE IA
# -----------------------
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def get_system_prompt():
    prompt = "Tu es un assistant académique expert. "
    if mode == "Étudiant":
        prompt += "Vulgarise les concepts, utilise un ton encourageant et des exemples simples."
    else:
        prompt += "Fournis des réponses techniques, rigoureuses et structurées pour un niveau universitaire."
    return prompt

def tts_audio(text):
    # On limite la longueur pour éviter les erreurs gTTS sur des textes trop longs
    t = gTTS(text=text[:500], lang="fr") 
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    t.save(f.name)
    return f.name

# Affichage du chat
st.title("🎓 Assistant IA")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrée utilisateur
if prompt := st.chat_input("Posez votre question ici..."):
    # 1. Affichage immédiat et sauvegarde
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message(st.session_state.user, "user", prompt)

    # 2. Réponse de l'IA
    with st.chat_message("assistant"):
        full_response = ""
        placeholder = st.empty()
        
        # Préparation du contexte (10 derniers messages)
        context = [{"role": "system", "content": get_system_prompt()}]
        context.extend(st.session_state.messages[-10:])

        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=context,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                placeholder.markdown(full_response + "▌")
        
        placeholder.markdown(full_response)
        
        # Audio
        try:
            audio_path = tts_audio(full_response)
            st.audio(audio_path)
        except:
            pass # L'audio est optionnel, on ne bloque pas si gTTS échoue

    # 3. Sauvegarde finale de la réponse assistant
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    save_message(st.session_state.user, "assistant", full_response)
