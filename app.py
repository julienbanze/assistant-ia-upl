import streamlit as st
import google.generativeai as genai
import time
from PIL import Image

# --- CONFIGURATION INITIALE ---
st.set_page_config(
    page_title="Assistant Intelligent Pro | Julien Banze Kandolo",
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLE PERSONNALISÉ (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500&display=swap');
    html, body, [data-testid="stapp"] { font-family: 'Google Sans', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] { background-color: #1e1f20; border-right: 1px solid #333; }
    .branding-box {
        padding: 1.5rem;
        background: linear-gradient(135deg, #2b2c2e 0%, #1e1f20 100%);
        border-radius: 12px;
        border: 1px solid #444;
        margin-bottom: 2rem;
    }
    .dev-name { color: #8ab4f8; font-size: 1.1rem; font-weight: 500; margin-bottom: 0px; }
    .dev-title { color: #9aa0a6; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; }
    .stChatMessage { border-radius: 20px; padding: 1.5rem; max-width: 85%; margin-bottom: 1rem; }
    .stChatInputContainer { padding-bottom: 2rem; background-color: transparent !important; }
    .stButton>button { width: 100%; border-radius: 50px; background-color: #333; color: white; border: 1px solid #444; transition: 0.3s; }
    .stButton>button:hover { background-color: #444; border: 1px solid #8ab4f8; }
</style>
""", unsafe_allow_html=True)

# --- GESTION ULTRA-ROBUSTE DE LA CLÉ API ---
# On cherche la clé sous tous les noms possibles que vous auriez pu utiliser
api_key = None
possible_names = ["api_key", "GROQ_API_KEY", "API_KEY", "gemini_api_key", "google_api_key"]

for name in possible_names:
    if name in st.secrets:
        api_key = st.secrets[name]
        break

if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Erreur de configuration : {e}")
        st.stop()
else:
    # Si vraiment aucune clé n'est trouvée, on affiche un diagnostic complet
    st.error("🔑 AUCUNE CLÉ DÉTECTÉE")
    st.markdown(f"""
    ### Julien, vérifiez vos secrets Streamlit :
    1. Allez dans **Settings > Secrets**.
    2. Assurez-vous d'avoir écrit : `api_key = "VOTRE_CLE_AIza"`
    3. Noms testés par le code : {', '.join(possible_names)}
    """)
    st.stop()

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.markdown(f"""
    <div class="branding-box">
        <p class="dev-title">Développeur & Architecte IA</p>
        <p class="dev-name">Julien Banze Kandolo</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h2 style='color: white; font-size: 1.5rem;'>🎓 Gemini 1.5 Pro</h2>", unsafe_allow_html=True)
    st.success("✅ Système Connecté")

    if st.button("＋ Nouvelle Session"):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.session_state.last_response = ""
        st.rerun()
    
    st.divider()
    uploaded_file = st.file_uploader("Vision Pro (Images)", type=['png', 'jpg', 'jpeg'])

    if st.session_state.get("last_response"):
        if st.button("🔊 Synthèse Vocale"):
            with st.spinner("Génération audio..."):
                try:
                    tts_model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-tts")
                    response_tts = tts_model.generate_content(
                        contents=[{"parts": [{"text": f"Julien vous répond : {st.session_state.last_response[:800]}"}]}],
                        generation_config={
                            "response_modalities": ["AUDIO"],
                            "speech_config": {"voice_config": {"prebuilt_voice_config": {"voice_name": "Kore"}}}
                        }
                    )
                    audio_data = response_tts.candidates[0].content.parts[0].inline_data.data
                    st.audio(audio_data, format="audio/wav")
                except:
                    st.error("Audio momentanément indisponible.")

# --- ZONE DE CHAT ---
st.markdown("<h1 style='text-align: center;'>🎓 Assistant Expert JBK</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "last_response" not in st.session_state: st.session_state.last_response = ""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Posez votre question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            model = genai.GenerativeModel(
                model_name='gemini-1.5-pro',
                system_instruction="Tu es Gemini 1.5 Pro, assistant de Julien Banze Kandolo. Niveau doctoral.",
            )
            inputs = [prompt]
            if uploaded_file: inputs.append(Image.open(uploaded_file))
            
            chat = model.start_chat(history=st.session_state.chat_history)
            response = chat.send_message(inputs, stream=True)
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.last_response = full_response
            st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
            st.session_state.chat_history.append({"role": "model", "parts": [full_response]})
        except Exception as e:
            st.error(f"Erreur d'exécution : {e}")

st.markdown("<p style='text-align: center; color: #555; font-size: 0.7rem; margin-top: 5rem;'>JBK Enterprise Edition</p>", unsafe_allow_html=True)
