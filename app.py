import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
from supabase import create_client
import bcrypt

# --- CONFIG ---
st.set_page_config(page_title="Assistant IA 🎓", layout="wide")

# --- INITIALISATION ---
if "user" not in st.session_state: st.session_state.user = None
if "messages" not in st.session_state: st.session_state.messages = []

# --- CONNEXION SUPABASE ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Erreur de configuration Secrets.")
    st.stop()

# --- FONCTIONS RÉSILIENTES ---
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except: return False

def login(username, password):
    try:
        res = supabase.table("utilisateurs").select("*").eq("username", username).execute()
        if res.data:
            return check_password(password, res.data[0]["password"])
    except Exception as e:
        st.error(f"Erreur DB : {e}")
    return False

def register(username, password):
    try:
        hashed = hash_password(password)
        supabase.table("utilisateurs").insert({"username": username, "password": hashed}).execute()
        st.success("Compte créé !")
    except:
        st.error("Ce nom d'utilisateur est déjà pris.")

def save_msg(user, role, content):
    try:
        supabase.table("messages").insert({"username": user, "role": role, "content": content}).execute()
    except: pass

# --- UI AUTH ---
if not st.session_state.user:
    st.title("🔐 Connexion")
    t1, t2 = st.tabs(["Login", "Inscription"])
    with t1:
        u = st.text_input("Pseudo")
        p = st.text_input("Pass", type="password")
        if st.button("Entrer"):
            if login(u, p):
                st.session_state.user = u
                # Charger l'historique
                hist = supabase.table("messages").select("*").eq("username", u).order("created_at").execute()
                st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in hist.data]
                st.rerun()
            else: st.error("Échec")
    with t2:
        u2, p2 = st.text_input("Nouveau"), st.text_input("Nouveau Pass", type="password")
        if st.button("Créer"): register(u2, p2)
    st.stop()

# --- INTERFACE CHAT ---
st.sidebar.title(f"👤 {st.session_state.user}")
if st.sidebar.button("Déconnexion"):
    st.session_state.clear()
    st.rerun()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.write(msg["content"])

if prompt := st.chat_input("Ta question..."):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_msg(st.session_state.user, "user", prompt)

    with st.chat_message("assistant"):
        resp = ""
        container = st.empty()
        # Appel API Groq
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Assistant académique."}] + st.session_state.messages[-5:],
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                resp += content
                container.write(resp)
        
        # Audio gTTS
        try:
            tts = gTTS(text=resp[:300], lang='fr')
            with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
                tts.save(fp.name)
                st.audio(fp.name)
        except: pass

    st.session_state.messages.append({"role": "assistant", "content": resp})
    save_msg(st.session_state.user, "assistant", resp)
