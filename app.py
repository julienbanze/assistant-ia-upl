import streamlit as st
from groq import Groq
import logging
from pathlib import Path

# -----------------------
# CONFIG PAGE
# -----------------------

st.set_page_config(
    page_title="Assistant Académique IA 🎓",
    page_icon="🎓",
    layout="wide"
)

# -----------------------
# DESIGN PRO
# -----------------------

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    color: white;
}

h1, h2, h3 {
    color: #FFD700;
    text-align: center;
}

.stChatInput input {
    border-radius: 25px;
    border: 2px solid #FFD700;
    padding: 12px;
    background-color: #1e2a38;
    color: white;
}

.chat-message {
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# -----------------------
# LOGS
# -----------------------

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# -----------------------
# GROQ CLIENT
# -----------------------

@st.cache_resource
def init_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("Ajoutez GROQ_API_KEY dans Settings > Secrets")
        st.stop()

client = init_client()

# -----------------------
# ETAT SESSION
# -----------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "mode" not in st.session_state:
    st.session_state.mode = "Étudiant"

if "has_greeted" not in st.session_state:
    st.session_state.has_greeted = False

# -----------------------
# MODE (ETUDIANT / ENSEIGNANT)
# -----------------------

st.sidebar.title("⚙️ Paramètres")

mode = st.sidebar.selectbox(
    "Choisir le mode",
    ["Étudiant", "Enseignant"]
)

st.session_state.mode = mode

st.sidebar.markdown("---")
st.sidebar.write(f"Mode actuel : **{mode}**")

# -----------------------
# FILTRE ACADEMIQUE
# -----------------------

def is_academic(question):
    mots_interdits = [
        "football","match","musique","chanson",
        "film","serie","amour","copine","copain",
        "jeu","divertissement","buzz","people"
    ]

    question = question.lower()

    for mot in mots_interdits:
        if mot in question:
            return False
    return True

# -----------------------
# PROMPT INTELLIGENT
# -----------------------

def get_system_prompt(mode):

    base = """
Tu es un assistant académique professionnel.

Règles STRICTES :

- Tu réponds uniquement aux questions éducatives et académiques.
- Refuse toute question hors sujet avec professionnalisme.
- Ne salue qu'une seule fois au début.
- Réponds de manière naturelle, claire et moderne.
- Ne force pas introduction/développement/conclusion.
- Si la question est floue, demande clarification.
"""

    if mode == "Étudiant":
        base += """
Mode Étudiant :
- Explique simplement
- Utilise des exemples
- Vulgarise au maximum
"""
    else:
        base += """
Mode Enseignant :
- Réponses détaillées et structurées
- Niveau avancé
- Ajoute des notions techniques
"""

    return base

# -----------------------
# HEADER
# -----------------------

st.markdown("# 🎓 Assistant Académique IA")
st.write("Posez vos questions académiques uniquement.")

# -----------------------
# HISTORIQUE
# -----------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------
# INPUT UTILISATEUR
# -----------------------

prompt = st.chat_input("Pose ta question académique...")

if prompt:

    # FILTRAGE
    if not is_academic(prompt):
        response = "Je suis un assistant académique conçu pour répondre uniquement aux questions éducatives. Merci de poser une question en lien avec l’apprentissage."

        st.chat_message("assistant").markdown(response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

        st.stop()

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    st.chat_message("user").markdown(prompt)

# -----------------------
# REPONSE IA
# -----------------------

if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":

    with st.chat_message("assistant"):

        placeholder = st.empty()
        full_response = ""

        SYSTEM_PROMPT = get_system_prompt(st.session_state.mode)

        # GESTION SALUTATION
        if st.session_state.has_greeted:
            SYSTEM_PROMPT += "\nNe commence pas par une salutation."
        else:
            st.session_state.has_greeted = True

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # MEMOIRE INTELLIGENTE (limite à 10 derniers messages)
        for msg in st.session_state.messages[-10:]:
            messages.append(msg)

        try:

            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                stream=True,
                temperature=0.3,
                max_tokens=2000
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"Erreur IA : {e}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })

# -----------------------
# FOOTER
# -----------------------

st.markdown("---")
st.markdown("Développé par **Julien Banze Kandolo** 🚀")
