import streamlit as st
import google.generativeai as genai
import time
from PIL import Image
import io
import base64


st.set_page_config(
    page_title="Assistant Intelligent | Julien Banze Kandolo",
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500&display=swap');
    
    html, body, [data-testid="stapp"] {
        font-family: 'Google Sans', sans-serif;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    [data-testid="stSidebar"] {
        background-color: #1e1f20;
        border-right: 1px solid #333;
    }

    .branding-box {
        padding: 1.5rem;
        background: linear-gradient(135deg, #2b2c2e 0%, #1e1f20 100%);
        border-radius: 12px;
        border: 1px solid #444;
        margin-bottom: 2rem;
    }

    .dev-name {
        color: #8ab4f8;
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 0px;
    }

    .dev-title {
        color: #9aa0a6;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stChatMessage {
        border-radius: 20px;
        padding: 1.5rem;
        max-width: 85%;
        margin-bottom: 1rem;
    }

    .stChatInputContainer {
        padding-bottom: 2rem;
        background-color: transparent !important;
    }

    .stButton>button {
        width: 100%;
        border-radius: 50px;
        background-color: #333;
        color: white;
        border: 1px solid #444;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #444;
        border: 1px solid #8ab4f8;
    }
</style>
""", unsafe_allow_html=True)


apiKey = st.secrets["api_key"] if "api_key" in st.secrets else ""
if apiKey:
    genai.configure(api_key=apiKey)
else:
    st.error("Clé API manquante. Veuillez la configurer dans vos secrets Streamlit.")
    st.stop()


system_instruction = (
    "Tu es Gemini 1.5 Pro, un assistant polyvalent de haute précision et de niveau doctoral, conçu par l'expert Julien Banze Kandolo. "
    "Tu dois aider dans tous les domaines : académique, codage expert, analyse d'image complexe et vie quotidienne. "
    "Ton raisonnement doit être profond, tes sources doivent être suggérées quand c'est possible, et ton ton doit être celui d'un mentor professionnel."
)

generation_config = {
    "temperature": 0.7, 
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}


model = genai.GenerativeModel(
    model_name='gemini-1.5-pro',
    system_instruction=system_instruction,
    generation_config=generation_config
)


if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_response" not in st.session_state:
    st.session_state.last_response = ""

def text_to_speech(text):
    """Convertit le texte en audio via l'API Gemini TTS."""
    try:
        tts_model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-tts")
        response = tts_model.generate_content(
            contents=[{"parts": [{"text": f"Dis avec une voix chaleureuse et posée : {text}"}]}],
            generation_config={
                "response_modalities": ["AUDIO"],
                "speech_config": {"voice_config": {"prebuilt_voice_config": {"voice_name": "Kore"}}}
            }
        )
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        return audio_data
    except Exception as e:
        st.error(f"Erreur lors de la génération vocale : {e}")
        return None


with st.sidebar:
    st.markdown(f"""
    <div class="branding-box">
        <p class="dev-title">Développeur & Architecte IA</p>
        <p class="dev-name">Julien Banze Kandolo</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h2 style='color: white; font-size: 1.5rem;'>🎓 Gemini 1.5 Pro</h2>", unsafe_allow_html=True)
    
    if st.button("＋ Nouvelle Session Académique"):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.session_state.last_response = ""
        st.rerun()
    
    st.divider()
    
    st.markdown("<p style='color: white;'>Vision & Documents</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Analysez une image ou un graphique...", type=['png', 'jpg', 'jpeg'])
    if uploaded_file:
        st.image(uploaded_file, caption="Média chargé pour analyse Pro", use_container_width=True)

    st.divider()
    if st.session_state.last_response:
        st.markdown("<p style='color: white;'>Accessibilité</p>", unsafe_allow_html=True)
        if st.button("🔊 Écouter la réponse Pro"):
            with st.spinner("Synthèse vocale en cours..."):
            
                audio_bytes = text_to_speech(st.session_state.last_response[:1000])
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/wav")


st.markdown(f"""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='font-weight: 500; font-size: 2.2rem;'>🎓 Assistant Universitaire & Polyvalent</h1>
        <p style='color: #9aa0a6;'>Intelligence de niveau Pro • Système conçu par Julien Banze Kandolo</p>
    </div>
""", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Posez votre question complexe ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            inputs = [prompt]
            if uploaded_file:
                img = Image.open(uploaded_file)
                inputs.append(img)
            
          
            chat = model.start_chat(history=st.session_state.chat_history)
            response = chat.send_message(inputs, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.01)
            
            message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.last_response = full_response
            st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
            st.session_state.chat_history.append({"role": "model", "parts": [full_response]})
            
        except Exception as e:
            st.error(f"Erreur de modèle Pro : {str(e)}")

st.markdown("<p style='text-align: center; color: #555; font-size: 0.7rem; margin-top: 5rem;'>Moteur Gemini 1.5 Pro | JBK Enterprise Edition | Assistant Académique Global</p>", unsafe_allow_html=True)
