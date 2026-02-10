import streamlit as st
import google.generativeai as genai
import time
from PIL import Image

# --- CONFIGURATION INITIALE ---
st.set_page_config(
    page_title="Assistant Académique | Julien Banze Kandolo",
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLE ÉPURÉ (STYLE GEMINI-LIKE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500&display=swap');
    
    html, body, [data-testid="stapp"] { 
        font-family: 'Google Sans', sans-serif;
        background-color: #131314;
    }
    
    /* Cacher les éléments Streamlit inutiles */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sidebar style */
    [data-testid="stSidebar"] { 
        background-color: #1e1f20; 
        border-right: 1px solid #333; 
    }
    
    .branding-box {
        padding: 1rem;
        background: #2b2c2e;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .dev-name { color: #e3e3e3; font-size: 1rem; font-weight: 500; }
    .dev-title { color: #8ab4f8; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Bulles de chat */
    .stChatMessage { 
        background-color: transparent !important;
        border-radius: 12px; 
        padding: 1rem; 
        margin-bottom: 0.5rem;
    }
    
    /* Input style */
    .stChatInputContainer { 
        padding-bottom: 2rem; 
        background-color: transparent !important;
    }
    
    /* Boutons */
    .stButton>button { 
        border-radius: 12px; 
        background-color: #333; 
        color: white; 
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { 
        background-color: #444; 
    }
    
    /* Suppression de l'espace en bas */
    .main .block-container {
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- GESTION DE LA CLÉ API ---
api_key = None
possible_names = ["api_key", "GROQ_API_KEY", "API_KEY", "gemini_api_key", "google_api_key"]

for name in possible_names:
    if name in st.secrets:
        api_key = st.secrets[name]
        break

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("🔑 Clé API manquante dans les Secrets.")
    st.stop()

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.markdown(f"""
    <div class="branding-box">
        <p class="dev-title">Développeur & Architecte IA</p>
        <p class="dev-name">Julien Banze Kandolo</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h3 style='color: #e3e3e3; font-size: 1.1rem; text-align:center;'>🎓 Assistant Académique</h3>", unsafe_allow_html=True)
    st.success("✅ IA Connectée")

    if st.button("＋ Nouveau Chat"):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.session_state.last_response = ""
        st.rerun()
    
    st.divider()
    uploaded_file = st.file_uploader("Joindre une image", type=['png', 'jpg', 'jpeg'])

    if st.session_state.get("last_response"):
        if st.button("🔊 Écouter la réponse"):
            with st.spinner("Préparation..."):
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
                    st.error("Audio indisponible.")

# --- ZONE DE CHAT ---
st.markdown("<h2 style='text-align: center; color: #e3e3e3; font-weight: 400;'>Comment puis-je vous aider, Julien ?</h2>", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "last_response" not in st.session_state: st.session_state.last_response = ""

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrée utilisateur
if prompt := st.chat_input("Écrivez votre question académique ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            # Passage au modèle Flash pour éviter l'erreur 404
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction="Tu es l'Assistant Académique, une IA experte développée par Julien Banze Kandolo. Réponds avec précision et élégance.",
            )
            
            inputs = [prompt]
            if uploaded_file:
                inputs.append(Image.open(uploaded_file))
            
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
            st.error(f"Désolé, une erreur est survenue : {e}")

# Footer discret et collé au contenu
st.markdown("<div style='text-align: center; color: #5f6368; font-size: 0.75rem; padding: 1rem;'>Développé par Julien Banze Kandolo | Assistant Académique v2</div>", unsafe_allow_html=True)
