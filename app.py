import streamlit as st
from groq import Groq
import json
import datetime


st.set_page_config(
    page_title="Assistant IA Pro - Julien Banze Kandolo",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
    <style>
    /* Fond général */
    .stApp { background-color: #f8f9fa; }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a202c; /* Sombre comme un IDE */
        color: #e2e8f0;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #63b3ed !important;
    }
    
    /* Messages du chat */
    .stChatMessage {
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
    }
    /* Message Assistant (Fond blanc) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
    }
    /* Message Utilisateur (Fond bleu très clair) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #ebf8ff;
        border: 1px solid #bee3f8;
    }
    
    /* Boutons */
    .stButton button {
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception:
    st.error("🚨 Erreur : Clé API manquante. Configurez `GROQ_API_KEY` dans les secrets.")
    st.stop()


if "messages" not in st.session_state:
    st.session_state.messages = []


with st.sidebar:
    st.title("🎛️ Centre de Contrôle")
    st.caption(f"Créé par **Julien Banze Kandolo** (UPL)")
    st.markdown("---")

    
    st.subheader("🧠 Modèle d'IA")
    model_option = st.selectbox(
        "Choisir l'intelligence :",
        (
            "llama-3.3-70b-versatile", 
            "llama-3.1-8b-instant",    
            "mixtral-8x7b-32768"       
        ),
        index=0,
        help="70b est plus intelligent pour le raisonnement. 8b est plus rapide."
    )

    
    st.subheader("⚙️ Paramètres")
    temperature = st.slider(
        "Température (Créativité)", 
        min_value=0.0, max_value=2.0, value=0.7, step=0.1,
        help="0 = Précis et factuel. 1+ = Créatif et imprévisible."
    )
    max_tokens = st.slider(
        "Longueur max réponse", 
        min_value=256, max_value=4096, value=2048, step=256
    )

    st.subheader("🎭 Mode Assistant")
    assistant_mode = st.radio(
        "Style de réponse :",
        ("🎓 Académique", "💻 Développeur", "✨ Créatif", "📝 Résumé")
    )

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Effacer", type="primary"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        
        chat_str = json.dumps(st.session_state.messages, indent=2, ensure_ascii=False)
        st.download_button(
            label="💾 Sauver",
            data=chat_str,
            file_name=f"chat_upl_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )

system_prompts = {
    "🎓 Académique": (
        "Tu es un assistant universitaire expert créé par Julien Banze Kandolo. "
        "Tes réponses doivent être rigoureuses, structurées, citer des sources si possible, "
        "et utiliser un ton formel. Utilise LaTeX pour les maths."
    ),
    "💻 Développeur": (
        "Tu es un expert en code (Python, C++, Java) créé par Julien Banze Kandolo. "
        "Tes réponses doivent être techniques. Fournis toujours le code complet, optimisé et commenté. "
        "Explique les bugs potentiels."
    ),
    "✨ Créatif": (
        "Tu es un assistant créatif et inspirant. N'hésite pas à utiliser des métaphores, "
        "un ton engageant et original. Tu as été créé par Julien."
    ),
    "📝 Résumé": (
        "Ton but est de synthétiser l'information de manière ultra-concise. "
        "Utilise des listes à puces. Va droit au but."
    )
}
current_system_prompt = system_prompts[assistant_mode]


st.title("🤖 Assistant IA ")
st.markdown(f"**Mode actuel :** `{assistant_mode}` | Modèle : `{model_option}`")


if not st.session_state.messages:
    st.info("👋 Bonjour ! Je suis prêt. Choisissez un mode dans la barre latérale et posez votre question.")

for message in st.session_state.messages:
    avatar = "🧑‍🎓" if message["role"] == "user" else "🧠"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


if prompt := st.chat_input("Je suis votre assistant pour vos rechercherches..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)

    
    with st.chat_message("assistant", avatar="🧠"):
        message_placeholder = st.empty()
        full_response = ""
        
    
        api_messages = [{"role": "system", "content": current_system_prompt}]
        
        for m in st.session_state.messages[-10:]:
            api_messages.append({"role": m["role"], "content": m["content"]})

        try:
            stream = client.chat.completions.create(
                model=model_option,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Erreur API : {e}")

st.markdown("---")
st.caption("Projet Académique | Université Protestante de Lubumbashi | IA & Recherche")
