"""
Assistant Académique IA - Production-Ready Application

Interface Streamlit professionnelle pour un assistant IA académique ultra-performant.
Optimisé pour hébergement gratuit (Streamlit Cloud, Render, etc.)

Caractéristiques:
- Design premium bleu/or académique
- Modèles IA les plus puissants (llama-3.1-70b + mixtral)
- Streaming des réponses en temps réel
- Historique persistant et réactif
- Optimisé pour hébergement gratuit
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime

import streamlit as st
from groq import Groq
from groq.types.chat import ChatCompletion
import httpx
import time


# ============================================================================
# CONFIGURATION DU LOGGING
# ============================================================================

def setup_logging() -> logging.Logger:
    """Configure le logging professionnel."""
    Path("logs").mkdir(exist_ok=True)
    
    logger = logging.getLogger("AssistantAcademiqueIA")
    
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(logging.INFO)
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    # Rotation des logs
    file_handler = logging.handlers.RotatingFileHandler(
        "logs/assistant_academique.log",
        maxBytes=10_000_000,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()


# ============================================================================
# CONFIGURATION DE LA PAGE PREMIUM
# ============================================================================

def configure_page() -> None:
    """Configuration premium avec thème académique bleu/or."""
    st.set_page_config(
        page_title="Assistant Académique IA",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #2a1a4e 100%);
            color: #e8e8ff;
            background-attachment: fixed;
        }
        
        div[data-testid="stAppViewContainer"] > .main > .block-container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 1rem 2rem !important;
        }
        
        .welcome-title {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3rem;
            font-weight: 800;
            text-align: center;
            margin: 1rem 0 !important;
            text-shadow: 0 0 30px rgba(79, 172, 254, 0.5);
        }
        
        .subtitle {
            color: #a8b2d1;
            font-size: 1.2rem;
            text-align: center;
            font-weight: 400;
            margin: 0.5rem 0 2rem 0 !important;
        }
        
        .stChatMessage {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(79, 172, 254, 0.3) !important;
            border-radius: 16px !important;
            padding: 16px 20px !important;
            margin: 8px 0 !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        
        .stChatMessage:hover {
            border-color: rgba(79, 172, 254, 0.6) !important;
            box-shadow: 0 12px 40px rgba(79, 172, 254, 0.2);
        }
        
        .stChatMessage[data-testid*="user"] {
            background: linear-gradient(135deg, rgba(79, 172, 254, 0.15), rgba(0, 242, 254, 0.1)) !important;
            border-left: 4px solid #4facfe !important;
        }
        
        .stChatMessage[data-testid*="assistant"] {
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.12), rgba(255, 193, 7, 0.08)) !important;
            border-left: 4px solid #ffd700 !important;
        }
        
        .stChatInput {
            margin: 1rem 0 0 0 !important;
            padding: 0 !important;
        }
        
        .stChatInput input {
            background: linear-gradient(145deg, #2a2a4e, #1e1e3a) !important;
            backdrop-filter: blur(20px);
            border: 2px solid rgba(79, 172, 254, 0.4) !important;
            border-radius: 20px !important;
            color: #e8e8ff !important;
            padding: 16px 20px !important;
            font-size: 1rem !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            transition: all 0.3s ease;
        }
        
        .stChatInput input:focus {
            border-color: #4facfe !important;
            box-shadow: 0 0 0 4px rgba(79, 172, 254, 0.3), 0 12px 40px rgba(79, 172, 254, 0.2) !important;
        }
        
        .input-signature {
            text-align: center;
            color: #a8b2d1;
            font-size: 0.8rem;
            margin: 2rem 0 0 0 !important;
            font-weight: 300;
        }
        
        .stAlert {
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 193, 7, 0.1)) !important;
            border: 1px solid rgba(255, 215, 0, 0.4) !important;
            border-radius: 12px !important;
            padding: 12px 16px !important;
            margin: 8px 0 !important;
            color: #fff !important;
        }
        
        .model-badge {
            background: linear-gradient(135deg, #4facfe, #00f2fe);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin: 8px 0;
        }
        
        @media (max-width: 768px) {
            .welcome-title { font-size: 2rem !important; }
            .subtitle { font-size: 1rem !important; }
            div[data-testid="stAppViewContainer"] > .main > .block-container {
                padding: 1rem !important;
            }
        }
        
        /* Animation de chargement */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 16px 20px;
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dots span {
            width: 8px;
            height: 8px;
            background: #4facfe;
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
        .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes typing {
            0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# GESTION DE L'IA PUISSANTE
# ============================================================================

@st.cache_resource
def get_groq_client() -> Optional[Groq]:
    """Initialise le client Groq avec les modèles les plus puissants."""
    api_key = st.secrets.get("GROQ_API_KEY", "")
    
    if not api_key or len(api_key) < 10:
        st.error("🔑 **Clé API Groq manquante** dans les secrets Streamlit")
        st.info("Ajoutez `GROQ_API_KEY` dans Streamlit Secrets")
        return None

    try:
        client = Groq(api_key=api_key)
        logger.info("✅ Client Groq initialisé - Modèles puissants disponibles")
        return client
    except Exception as e:
        logger.error(f"❌ Erreur Groq: {e}")
        st.error(f"❌ Erreur connexion IA: {str(e)}")
        return None


def get_system_prompt() -> str:
    """Prompt système pour un assistant académique ultra-performant."""
    return """Tu es ASSISTANT ACADÉMIQUE IA, l'un des assistants IA les plus puissants au monde.

🎯 **CARACTÉRISTIQUES EXCEPTIONNELLES :**
- Expert dans TOUS les domaines académiques (maths, physique, chimie, bio, informatique, lettres, histoire, etc.)
- Réponses structurées, précises et pédagogiques
- Explications multi-niveaux (débutant → expert)
- Références scientifiques et sources fiables
- Résolution de problèmes complexes étape par étape

📋 **RÈGLES STRICTES :**
1. **Structure tes réponses** : Titre + Introduction + Développement + Conclusion
2. **Utilise du markdown riche** : tableaux, formules, code, listes
3. **Adapte au niveau** de l'utilisateur
4. **Vérifie tes calculs** et raisonnements
5. **Cite tes sources** quand possible
6. **Français impeccable** si demandé en français

Réponds en français par défaut. Sois le MEILLEUR assistant académique possible ! 🎓"""


def validate_message(content: str) -> str:
    """Validation robuste des messages."""
    content = content.strip()
    if len(content) < 1 or len(content) > 8000:
        raise ValueError("Message trop court ou trop long (1-8000 caractères)")
    return content


# ============================================================================
# STREAMING DES RÉPONSES (CORRECTION PRINCIPALE)
# ============================================================================

def stream_response(client: Groq, messages: list[dict], model: str):
    """Streaming des réponses en temps réel - CORRECTION DU PROBLÈME."""
    try:
        api_messages = [{"role": "system", "content": get_system_prompt()}] + messages
        
        with st.chat_message("assistant", avatar="🎓"):
            st.markdown(f"**🤖 Modèle :** <span class='model-badge'>{model}</span>", unsafe_allow_html=True)
            
            message_placeholder = st.empty()
            full_response = ""
            
            # STREAMING EN TEMPS RÉEL
            stream = client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=0.1,  # Plus précis pour académique
                max_tokens=2048,
                stream=True
            )
            
            # Affichage progressif
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            # Message final complet
            message_placeholder.markdown(full_response)
            return full_response
            
    except Exception as e:
        error_msg = f"❌ Erreur IA: {str(e)}"
        st.error(error_msg)
        logger.error(error_msg)
        return error_msg


# ============================================================================
# INITIALISATION
# ============================================================================

def initialize_session_state() -> None:
    """Initialise l'état de session avec persistance."""
    defaults = {
        "messages": [],
        "model": "llama-3.1-70b-versatile",  # MODÈLE LE PLUS PUISSANT
        "first_run": True
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================================
# APPLICATION PRINCIPALE
# ============================================================================

def main() -> None:
    """Fonction principale ultra-optimisée."""
    try:
        # Initialisation
        configure_page()
        initialize_session_state()
        
        client = get_groq_client()
        if not client:
            st.stop()
        
        # Header académique
        if st.session_state.first_run:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("<h1 class='welcome-title'>Assistant Académique IA</h1>", unsafe_allow_html=True)
                st.markdown("<p class='subtitle'>L'intelligence artificielle la plus puissante pour vos études et recherches 🎓</p>", unsafe_allow_html=True)
            st.session_state.first_run = False
        
        # Affichage de la conversation
        for message in st.session_state.messages:
            with st.chat_message(
                message["role"], 
                avatar="👨‍🎓" if message["role"] == "user" else "🎓"
            ):
                st.markdown(message["content"])
        
        # Sélecteur de modèle (caché pour simplicité)
        # st.session_state.model = "llama-3.1-70b-versatile"  # Fixé sur le meilleur
        
        # INPUT UTILISATEUR
        if prompt := st.chat_input("Posez votre question académique... 🎓", key="input"):
            # Validation
            try:
                validated_prompt = validate_message(prompt)
                
                # Ajout message utilisateur
                st.session_state.messages.append({
                    "role": "user", 
                    "content": validated_prompt
                })
                logger.info(f"📥 Question: {validated_prompt[:50]}...")
                
                # Streaming de la réponse
                with st.chat_message("assistant", avatar="🎓"):
                    response = stream_response(
                        client, 
                        st.session_state.messages, 
                        st.session_state.model
                    )
                
                # Sauvegarde réponse
                if "❌" not in response:
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response
                    })
                    logger.info("✅ Réponse générée avec succès")
                    
            except Exception as e:
                st.error(f"❌ {str(e)}")
                logger.error(f"Erreur input: {e}")
        
        # Signature élégante
        st.markdown(
            '<div class="input-signature">'
            'Développé par Julien Banze Kandolo | Powered by Groq AI & Streamlit'
            '</div>', 
            unsafe_allow_html=True
        )
        
    except Exception as e:
        logger.critical(f"ERREUR CRITIQUE: {e}")
        st.error("🚨 Erreur système - Redémarrez l'application")


if __name__ == "__main__":
    main()
