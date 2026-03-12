"""
Assistant IA - Production-Ready Application

Une application Streamlit professionnelle fournissant une interface chat
pour interroger un modèle d'IA. Conçue pour être extensible, robuste et
facile à adapter.

Architecture:
- Gestion d'erreurs robuste
- Logging complet
- Type hints
- Validation des entrées
- Cache et optimisation

Usage:
    streamlit run app.py
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime

import streamlit as st
from groq import Groq
from groq.types.chat import ChatCompletion
import httpx  # nécessaire pour solution de contournement des proxies


# ============================================================================
# CONFIGURATION DU LOGGING
# ============================================================================

def setup_logging() -> logging.Logger:
    """
    Configure le logging pour l'application.
    
    Returns:
        logging.Logger: Logger configuré
    """
    # Créer dossier logs s'il n'existe pas
    Path("logs").mkdir(exist_ok=True)
    
    logger = logging.getLogger("AssistantIA")
    
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Format de log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    # Fichier handler (rotation)
    file_handler = logging.handlers.RotatingFileHandler(
        "logs/assistant_ia.log",
        maxBytes=5_000_000,  # 5 MB
        backupCount=3
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()


# ============================================================================
# CONFIGURATION DE LA PAGE
# ============================================================================

def configure_page() -> None:
    """Configure la page Streamlit avec le style global.

    Cette fonction est appelée une seule fois, donc pas de décorateur de cache.
    """
    st.set_page_config(
        page_title="Assistant IA",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background-color: #0a0e27 !important;
            color: #e3e3e3;
        }
        
        /* centre le contenu principal et limite sa largeur */
        div[data-testid="stAppViewContainer"] > .main > .block-container {
            max-width: 800px;
            margin: 0 auto;
            padding-top: 2rem;
        }
        
        .welcome-title {
            background: linear-gradient(90deg, #4f46e5, #7c3aed, #ec4899, #4f46e5);
            background-size: 300% auto;
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.8rem;
            font-weight: 700;
            animation: grad_flow 6s linear infinite;
            text-align: center;
            margin: 2rem 0;
        }
        
        @keyframes grad_flow { 0% { background-position: 0% 50%; } 100% { background-position: 300% 50%; } }
        
        .stChatMessage { 
            background: #1a1f3a; 
            border-left: 3px solid #4f46e5; 
            border-radius: 12px; 
            padding: 8px;
        }
        
        .input-signature { text-align: center; color: #8ab4f8; font-size: 0.85rem; margin-bottom: 1rem; font-weight: 500; }
        
        .stButton > button { width: 100%; border-radius: 8px; border: 1px solid #4f46e5; background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; font-weight: 600; transition: all 0.3s ease; }
        
        .stButton > button:hover { box-shadow: 0 8px 20px rgba(79, 70, 229, 0.4); transform: translateY(-2px); }
        
        @media (max-width: 768px) {
            .welcome-title { font-size: 1.8rem !important; }
            .stChatMessage { font-size: 0.9rem; }
            .input-signature { font-size: 0.75rem; }
            .stButton > button { font-size: 0.9rem; }
        }
    </style>
    """, unsafe_allow_html=True)
    
    logger.info("Page configuration applied")


# ============================================================================
# GESTION DE LA CONFIGURATION
# ============================================================================

@st.cache_resource
def get_groq_client() -> Optional[Groq]:
    """
    Initialise et retourne le client Groq.

    Si l'appel standard échoue à cause d'un argument `proxies` non supporté
    (TypeError), on réessaie en fournissant explicitement un `httpx.Client`
    dépourvu de ce paramètre.

    Returns:
        Groq: Client Groq configuré

    Raises:
        ValueError: Si la clé API est manquante ou invalide
        Exception: Tout autre problème d'initialisation
    """
    api_key = st.secrets.get("GROQ_API_KEY")

    if not api_key:
        logger.error("GROQ_API_KEY manquante dans les secrets")
        raise ValueError("GROQ_API_KEY manquante")

    if len(api_key) < 10:
        logger.error("GROQ_API_KEY invalide")
        raise ValueError("GROQ_API_KEY invalide")

    try:
        client = Groq(api_key=api_key)
        logger.info("Client Groq initialisé sans http_client personnalisé")
        return client

    except TypeError as e:
        if "proxies" in str(e):
            logger.warning(
                "Erreur proxies lors de l'init Groq, réessai avec httpx.Client simple"
            )
            http_client = httpx.Client()
            client = Groq(api_key=api_key, http_client=http_client)
            logger.info("Client Groq initialisé avec http_client personnalisé")
            return client
        else:
            # erreur non anticipée, relancer
            logger.error(f"TypeError inattendue lors de l'init Groq: {e}")
            raise
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation Groq: {str(e)}")
        raise


# ============================================================================
# GESTION DU CHAT
# ============================================================================

def validate_message(content: str) -> str:
    """Valide et nettoie un message utilisateur.

    En plus de la validation habituelle, détecte les propos impolis ou vulgaires et
    lève une exception spéciale pour en informer le flux de la conversation.
    """
    if not isinstance(content, str):
        raise ValueError("Le message doit être une chaîne de caractères")
    
    content = content.strip()
    
    if not content:
        raise ValueError("Le message ne peut pas être vide")
    
    if len(content) > 10000:
        raise ValueError("Le message est trop long (max 10000 caractères)")

    # Simple filtre de grossièretés (français/anglais)
    bad_words = ["con", "pute", "merde", "salope", "idiot", "stupide", "fuck", "shit"]
    lowered = content.lower()
    for word in bad_words:
        if word in lowered.split():
            raise ValueError("Veuillez rester poli dans vos demandes — je suis un assistant IA.")
    
    return content


def get_system_prompt() -> str:
    """Retourne le prompt système pour l'assistant générique.

    Le modèle doit se comporter comme une IA puissante, claire et polie. Si l'utilisateur
    est impoli, répondre calmement qu'il préfère un langage respectueux.
    """
    return """Tu es un assistant IA généraliste, performant et courtois.

Tu dois:
1. Aider avec des questions techniques, pratiques ou générales
2. Expliquer les concepts clairement et de manière structurée
3. Fournir des références lorsque c'est pertinent
4. Rester respectueux et professionnel en toutes circonstances
5. Encourager la réflexion autonome

Réponds en français si la question est en français, sinon en anglais.
Sois concis mais complet et évite les digressions inutiles."""


def send_groq_message(
    client: Groq,
    messages: list[dict],
    model: str = "mixtral-8x7b-32768"
) -> str:
    """
    Envoie un message à l'API Groq et retourne la réponse.
    
    Args:
        client (Groq): Client Groq
        messages (list[dict]): Liste des messages
        model (str): Modèle à utiliser
    
    Returns:
        str: Réponse de l'API
    
    Raises:
        ValueError: Si les messages sont invalides
        Exception: Si l'API retourne une erreur
    """
    if not messages:
        raise ValueError("La liste des messages est vide")
    
    try:
        # Ajouter le prompt système
        api_messages = [
            {"role": "system", "content": get_system_prompt()}
        ] + messages
        
        logger.debug(f"Envoi de {len(api_messages)} messages à Groq")
        
        response: ChatCompletion = client.chat.completions.create(
            model=model,
            messages=api_messages,
            temperature=0.7,
            max_tokens=1024,
        )
        
        reply = response.choices[0].message.content
        logger.info(f"Réponse reçue de Groq ({len(reply)} caractères)")
        
        return reply
    
    except ValueError as e:
        logger.warning(f"Erreur de validation: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Erreur API Groq: {str(e)}")
        raise


def initialize_session_state() -> None:
    """Initialise l'état de session Streamlit."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        logger.info("Session d'état initialisée")


# ============================================================================
# INTERFACE UTILISATEUR
# ============================================================================





# ============================================================================
# APPLICATION PRINCIPALE
# ============================================================================

def main() -> None:
    """Fonction principale de l'application."""
    try:
        # Configuration
        configure_page()
        initialize_session_state()
        
        # Écran d'accueil
        if not st.session_state.messages:
            st.markdown("<h1 class='welcome-title'>Assistant IA</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center;'>Posez votre question ci‑dessous et l'IA répondra.</p>", unsafe_allow_html=True)
        
        # Afficher la conversation existante
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🧑‍🎓" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])
        
        # Signature
        st.markdown('<div class="input-signature">Développé par Julien Banze Kandolo</div>', unsafe_allow_html=True)
        
        # Input utilisateur
        if user_input := st.chat_input("Posez votre question ici..."):
            try:
                user_input = validate_message(user_input)
                st.session_state.messages.append({"role": "user", "content": user_input})
                logger.info(f"Message utilisateur reçu: {len(user_input)} caractères")

                # Envoi à l'API
                client = get_groq_client()
                api_messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                ]
                api_messages.append({"role": "user", "content": user_input})

                response = send_groq_message(client, api_messages)
                st.session_state.messages.append({"role": "assistant", "content": response})
                logger.info(f"Réponse générée: {len(response)} caractères")

            except ValueError as e:
                st.error(f"❌ {str(e)}")
                logger.warning(f"Entrée invalide: {str(e)}")
            except Exception as e:
                st.error(f"❌ Une erreur s'est produite: {str(e)}")
                logger.error(f"Erreur inattendue: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Erreur critique: {str(e)}")
        logger.critical(f"Erreur critique: {str(e)}")


if __name__ == "__main__":
    main()

# Anciennes tentatives ou widgets superflus ont été retirés afin de
# garder l'interface aussi propre et réactive que possible. Toute interaction
# se fait désormais via la zone de chat gérée par la fonction `main()`.
