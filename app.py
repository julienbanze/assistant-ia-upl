import streamlit as st
from groq import Groq

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="IA Assistant UPL", page_icon="🎓", layout="centered")

# --- RÉCUPÉRATION DE LA CLÉ DEPUIS SECRETS.TOML ---
try:
    # Utilisation de la clé sécurisée gsk_...
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("Erreur : La clé API est introuvable dans secrets.toml.")
    st.stop()

# --- STYLE VISUEL ---
st.markdown("""
    <style>
    .stChatInputContainer { padding-bottom: 20px; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- ENTÊTE PERSONNALISÉ ---
st.title("🎓 Assistant IA Universitaire")
st.write("Posez vos questions sur vos cours, vos mémoires ou votre orientation à l'UPL.")

# --- GESTION DE LA MÉMOIRE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- ZONE DE DIALOGUE AVEC RESTRICTIONS ---
if prompt := st.chat_input("Ex: Comment faire un plan de mémoire ?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Bloc de configuration des instructions (System Prompt)
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "Tu es l'assistant IA exclusif créé par Julien BANZE KANDOLO pour les étudiants de l'UPL. "
                            "CONSIGNE STRICTE : Tu es un expert académique. Tu ne dois répondre QU'AUX QUESTIONS "
                            "liées à l'enseignement, aux cours, aux examens, à l'orientation académique et à la rédaction de mémoires. "
                            "Si l'étudiant pose une question hors sujet (musique, sport, cuisine, etc.), réponds exactement ceci : "
                            "'Désolé, en tant qu'assistant académique de l'UPL, je suis programmé uniquement pour "
                            "répondre aux questions concernant vos études et votre parcours universitaire.'"
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile", # Modèle ultra-rapide
            )
            
            reponse = chat_completion.choices[0].message.content
            st.markdown(reponse)
            st.session_state.messages.append({"role": "assistant", "content": reponse})
            
        except Exception as e:
            st.error("Désolé, je rencontre une petite difficulté technique. Réessaye dans un instant.")

# --- PIED DE PAGE PROFESSIONNEL ---
st.markdown("---")
st.markdown("© 2026 | Projet de fin d'études - Julien BANZE KANDOLO | Université Protestante de Lubumbashi")