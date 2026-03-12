"""
Assistant Académique JBK - Production-Ready Application

Une application Streamlit professionnelle pour l'assistance académique 
à l'Université Pédagogique de Lubumbashi (UPL).

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
    """Configure la page Streamlit avec tous les styles.

    **Remarque**: cette fonction ne doit plus être décorée avec `@st.cache_*` car
    `st.set_page_config` ne peut être appelé qu'une seule fois par page. Les
    décorateurs de cache peuvent réexécuter la fonction lors des reruns et
    provoquer l'erreur critique signalée par l'utilisateur.
    """
    st.set_page_config(
        page_title="Assistant Académique JBK | UPL",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background-color: #0a0e27 !important;
            color: #e3e3e3;
        }
        
        .jbk-card {
            padding: 20px;
            background: linear-gradient(145deg, #1a1f3a, #0f1220);
            border-radius: 12px;
            border: 1px solid #2d3748;
            text-align: center;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        
        .jbk-card:hover { border-color: #4f46e5; box-shadow: 0 8px 12px rgba(79, 70, 229, 0.2); }
        
        .jbk-title { font-size: 0.75rem; color: #8ab4f8; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin: 0; }
        
        .jbk-name { font-size: 1.3rem; font-weight: 700; color: #8ab4f8; margin: 0.5rem 0 0 0; }
        
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
        
        .stChatMessage { background: #1a1f3a; border-left: 3px solid #4f46e5; border-radius: 8px; }
        
        .input-signature { text-align: center; color: #8ab4f8; font-size: 0.85rem; margin-bottom: 1rem; font-weight: 500; }
        
        .stButton > button { width: 100%; border-radius: 8px; border: 1px solid #4f46e5; background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; font-weight: 600; transition: all 0.3s ease; }
        
        .stButton > button:hover { box-shadow: 0 8px 20px rgba(79, 70, 229, 0.4); transform: translateY(-2px); }
        
        @media (max-width: 768px) {
            .welcome-title { font-size: 1.8rem !important; }
            .jbk-name { font-size: 1rem !important; }
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
    
    Returns:
        Groq: Client Groq configuré
        
    Raises:
        ValueError: Si la clé API est manquante
    """
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
        
        if not api_key:
            logger.error("GROQ_API_KEY manquante dans les secrets")
            raise ValueError("GROQ_API_KEY manquante")
        
        if len(api_key) < 10:
            logger.error("GROQ_API_KEY invalide")
            raise ValueError("GROQ_API_KEY invalide")
        
        client = Groq(api_key=api_key)
        logger.info("Client Groq initialisé avec succès")
        return client
    
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
            raise ValueError("Veuillez rester poli dans vos demandes — je suis un assistant académique.")
    
    return content


def get_system_prompt() -> str:
    """Retourne le prompt système pour l'assistant.

    Le prompt guide l'IA vers un comportement pédagogique, courtois et poli. Si l'utilisateur
    envoie des propos grossiers ou déplacés, l'assistant doit répondre calmement qu'il n'est
    pas conçu pour ce type de requête et encourager le respect.
    """
    return """Tu es un assistant académique expert pour l'Université Protestante de Lubumbashi (UPL).

Tu dois:
1. Aider les étudiants avec leurs cours et devoirs
2. Expliquer les concepts complexes de manière claire et pédagogique
3. Fournir des références académiques quand c'est pertinent
4. Encourager la réflexion critique et individuelle
5. Respecter l'intégrité académique

Reste toujours respectueux envers l'utilisateur et réponds de façon courtoise. Si l'utilisateur pose une
question impolie, dénigrante ou hors sujet, explique calmement que tu n'es pas conçu pour ce type de requête
et demande de rester poli.

Réponds toujours de manière professionnelle.
Si la question est en français, réponds en français.
Fournis des réponses structurées et bien organisées.
Sois concis mais complet."""


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

def render_sidebar() -> Optional[str]:
    """Affiche la barre latérale minimaliste et retourne l'action sélectionnée."""

    st.sidebar.markdown("# Menu")

    # boutons principaux alignés en colonne, style simple comme Gemini
    if st.sidebar.button("➕ Nouvelle session", use_container_width=True):
        logger.info("Nouvelle session demandée")
        return "new_session"

    if st.sidebar.button("📊 Statistiques", use_container_width=True):
        logger.info("Statistiques demandées")
        return "stats"

    st.sidebar.markdown("---")

    st.sidebar.markdown(
        """
        <div style='padding:10px; border:1px solid #444; border-radius:8px; background:#1a1f3a;'>
        <strong>Assistant Académique JBK</strong><br/>
        Créé par : <em>Julien Banze Kandolo</em><br/>
        <a href='https://upl.ac.ug' style='color:#8ab4f8;'>Université Protestante de Lubumbashi (UPL)</a><br/>
        Powered by <strong>Groq API</strong>
        </div>
        """,
        unsafe_allow_html=True
    )

    return None


def show_statistics() -> None:
    """Affiche les statistiques de la conversation."""
    if not st.session_state.messages:
        st.info("Aucun message pour le moment")
        return
    
    user_msgs = sum(1 for m in st.session_state.messages if m["role"] == "user")
    assistant_msgs = sum(1 for m in st.session_state.messages if m["role"] == "assistant")
    total_chars = sum(len(m["content"]) for m in st.session_state.messages)
    
    with st.sidebar:
        st.metric("Messages totaux", len(st.session_state.messages))
        st.metric("Vos messages", user_msgs)
        st.metric("Réponses", assistant_msgs)
        st.metric("Caractères total", f"{total_chars:,}")


# ============================================================================
# APPLICATION PRINCIPALE
# ============================================================================

def main() -> None:
    """Fonction principale de l'application."""
    try:
        # Configuration
        configure_page()
        initialize_session_state()
        
        # Barre latérale
        sidebar_action = render_sidebar()
        
        if sidebar_action == "new_session":
            st.session_state.messages = []
            st.rerun()
        
        elif sidebar_action == "stats":
            show_statistics()
        
        # Écran d'accueil
        if not st.session_state.messages:
            st.markdown("<h1 class='welcome-title'>Assistant Académique JBK</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center;'>Posez votre question académique dans la zone de chat ci‑dessous.</p>", unsafe_allow_html=True)
        
        # Afficher la conversation existante
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🧑‍🎓" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])
        
        # Signature
        st.markdown('<div class="input-signature">Julien Banze Kandolo • Assistant Académique JBK 🎓</div>', 
                   unsafe_allow_html=True)
        
        # Input utilisateur
        if user_input := st.chat_input("Votre question académique..."):
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

# Les blocs supplémentaires situés ici étaient des vestiges d'un essai
# antérieur et exécutaient d'autres commandes Streamlit en dehors de la
# logique principale. Ils ont été supprimés pour éviter les reruns inattendus
# et l'erreur de configuration de la page. La seule entrée utilisateur
# nécessaire est déjà gérée dans la fonction `main()`.
