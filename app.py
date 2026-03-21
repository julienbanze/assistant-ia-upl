import streamlit as st
from groq import Groq
from gtts import gTTS
import tempfile
from supabase import create_client
import bcrypt
import os

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Assistant IA 🎓", layout="wide")

# --- 2. INITIALISATION DU SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. CONNEXION SUPABASE ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("⚠️ Erreur de configuration : Vérifiez vos Secrets Streamlit (URL et KEY).")
    st.stop()

# --- 4. FONCTIONS UTILITAIRES ---
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except:
        return False

# --- 5. LOGIQUE DE CHAT & DB ---
def save_msg_to_db(user, role, content):
    try:
        supabase.table("messages").insert({
            "username": user, 
            "role": role, 
            "content": content
        }).execute()
    except Exception as e:
        st.warning(f"Note : Impossible de sauvegarder le message en ligne ({e})")

def load_chat_history(username):
    try:
        res = supabase.table("messages").select("*").eq("username", username).order("created_at").execute()
        return [{"role": m["role"], "content": m["content"]} for m in res.data]
    except Exception as e:
        st.error(f"Erreur de chargement de l'historique : {e}")
        return []

# --- 6. INTERFACE D'AUTHENTIFICATION ---
if st.session_state.user is None:
    st.title("🔐 Assistant Académique")
    tab1, tab2 = st.tabs(["Connexion", "Créer un compte"])

    with tab1:
        u = st.text_input("Nom d'utilisateur", key="login_u")
        p = st.text_input("Mot de passe", type="password", key="login_p")
        if st.button("Se connecter"):
            try:
                res = supabase.table("utilisateurs").select("*").eq("username", u).execute()
                if res.data and check_password(p, res.data[0]["password"]):
                    st.session_state.user = u
                    st.session_state.messages = load_chat_history(u)
                    st.rerun()
                else:
                    st.error("Utilisateur ou mot de passe incorrect.")
            except Exception as e:
                st.error(f"Erreur de connexion à la base : {e}")

    with tab2:
        u2 = st.text_input("Choisir un pseudo", key="reg_u")
        p2 = st.text_input("Choisir un mot de passe", type="password", key="reg_p")
        if st.button("S'inscrire"):
            if u2 and p2:
                try:
                    hashed = hash_password(p2)
                    supabase.table("utilisateurs").insert({"username": u2, "password": hashed}).execute()
                    st.success("Compte créé ! Connectez-vous maintenant.")
                except:
                    st.error("Ce pseudo est déjà utilisé ou la table est introuvable.")
            else:
                st.warning("Veuillez remplir tous les champs.")
    st.stop()

# --- 7. INTERFACE PRINCIPALE (APRES CONNEXION) ---
st.sidebar.title(f"👤 {st.session_state.user}")
mode = st.sidebar.selectbox("Mode de réponse", ["Étudiant (Simple)", "Enseignant (Détaillé)"])

if st.sidebar.button("🗑️ Effacer l'historique"):
    try:
        supabase.table("messages").delete().eq("username", st.session_state.user).execute()
        st.session_state.messages = []
        st.rerun()
    except:
        st.error("Erreur lors de la suppression.")

if st.sidebar.button("Déconnexion"):
    st.session_state.clear()
    st.rerun()

# --- 8. MOTEUR IA (GROQ) ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("Clé API GROQ manquante dans les secrets.")
    st.stop()

# Affichage des messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrée utilisateur
if prompt := st.chat_input("Posez votre question académique..."):
    # Affichage utilisateur
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_msg_to_db(st.session_state.user, "user", prompt)

    # Réponse Assistant
    with st.chat_message("assistant"):
        full_res = ""
        placeholder = st.empty()
        
        system_msg = "Tu es un assistant académique. "
        system_msg += "Explique simplement." if "Étudiant" in mode else "Sois très détaillé et technique."
        
        # Contexte pour l'IA
        context = [{"role": "system", "content": system_msg}] + st.session_state.messages[-6:]

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

        # Audio (gTTS)
        try:
            tts = gTTS(text=full_res[:400], lang='fr')
            f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts.save(f.name)
            st.audio(f.name)
        except:
            pass

    # Sauvegarde assistant
    st.session_state.messages.append({"role": "assistant", "content": full_res})
    save_msg_to_db(st.session_state.user, "assistant", full_res)
