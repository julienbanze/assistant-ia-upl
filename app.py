import streamlit as st
from supabase import create_client
from groq import Groq
import logging
from pathlib import Path

# -----------------------
# CONFIGURATION PAGE
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

h1{
color:#ffd700;
text-align:center;
font-size:2.8em;
}

.stChatInput input{
border-radius:25px;
border:2px solid #ffd700;
padding:12px;
}
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
def init_groq_client():
    try:
        return Groq(api_key="ta_cle_groq")  # Remplace par ta clé Groq
    except:
        st.error("Erreur : ajoute ta clé Groq")
        st.stop()

groq_client = init_groq_client()

# -----------------------
# SUPABASE CLIENT
# -----------------------
SUPABASE_URL = "https://syvlefgsyjgebwzmyoyp.supabase.co"
SUPABASE_KEY = "sb_publishable_7_CzCKPJ-QJmgFC4-5GONg_d1cqw4F3"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------
# PROMPT IA
# -----------------------
SYSTEM_PROMPT = """
Tu es un assistant académique intelligent.
Réponds toujours en français.
Structure ta réponse :
Titre
Introduction
Explication claire
Conclusion
"""

# -----------------------
# INSCRIPTION / LOGIN SIMPLIFIÉ
# -----------------------
st.markdown("## 🎓 Assistant Académique IA")
email = st.text_input("Votre email (pour sauvegarder vos messages)")

if email:
    # Vérifier si l'utilisateur existe
    data = supabase.table("utilisateurs").select("*").eq("email", email).execute().data
    if not data:
        # Inscription automatique
        supabase.table("utilisateurs").insert({"email": email}).execute()
        user_id = supabase.table("utilisateurs").select("id").eq("email", email).execute().data[0]["id"]
    else:
        user_id = data[0]["id"]
else:
    st.warning("Veuillez entrer votre email pour continuer.")
    st.stop()

# -----------------------
# MEMOIRE CHAT
# -----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique pour cet utilisateur
historique = supabase.table("messages").select("*").eq("user_id", user_id).order("created_at", desc=False).execute().data
for msg in historique:
    role = "user" if msg.get("question") else "assistant"
    content = msg.get("question") or msg.get("reponse")
    st.chat_message(role).markdown(content)

# -----------------------
# QUESTION TEXTE
# -----------------------
prompt = st.chat_input("Posez votre question académique...")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role":"user","content":prompt})

    # -----------------------
    # REPONSE IA
    # -----------------------
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        messages = [{"role":"system","content":SYSTEM_PROMPT}]
        for msg in st.session_state.messages:
            messages.append(msg)

        try:
            stream = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                stream=True,
                temperature=0.2,
                max_tokens=1500
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"Erreur IA : {e}")

        # -----------------------
        # Sauvegarde dans Supabase
        # -----------------------
        supabase.table("messages").insert({
            "user_id": user_id,
            "question": prompt,
            "reponse": full_response
        }).execute()

        st.session_state.messages.append({"role":"assistant","content":full_response})

# -----------------------
# FOOTER
# -----------------------
st.markdown("---")
st.markdown("Développé par **Julien Banze Kandolo**")
