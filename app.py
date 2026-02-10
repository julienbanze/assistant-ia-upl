import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Assistant IA | Julien Banze Kandolo",
    page_icon="🎓",
    layout="wide"
)

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    .stChatMessage { border-radius: 15px; }
    .branding { padding: 10px; border-radius: 10px; background: #1e1f20; border: 1px solid #333; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- RÉCUPÉRATION DE LA CLÉ (VERSION ROBUSTE) ---
# On cherche 'api_key' ou 'GROQ_API_KEY' pour être sûr
api_key = st.secrets.get("api_key") or st.secrets.get("GROQ_API_KEY")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
    except Exception as e:
        st.error(f"Erreur de configuration : {e}")
        st.stop()
else:
    st.error("🔑 CLÉ MANQUANTE DANS LES SECRETS STREAMLIT")
    st.info("Julien, allez dans Settings > Secrets et écrivez exactement : api_key = 'VOTRE_CLE_IMAGE_4'")
    st.stop()

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.markdown('<div class="branding"><h4>🎓 Expert JBK</h4><p>Julien Banze Kandolo</p></div>', unsafe_allow_html=True)
    st.success("✅ IA Connectée")
    if st.button("Effacer la discussion"):
        st.session_state.messages = []
        st.rerun()

# --- INTERFACE DE CHAT ---
st.title("Assistant Intelligent JBK")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Posez votre question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Génération de la réponse
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Désolé, une erreur est survenue : {e}")

st.caption("Développé par Julien Banze Kandolo | Propulsé par Gemini 1.5 Pro")
