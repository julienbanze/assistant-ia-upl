import streamlit as st

# -----------------------
# CONFIG PAGE
# -----------------------
st.set_page_config(
    page_title="Assistant IA",
    page_icon="💬",
    layout="wide"
)

# -----------------------
# STYLE CSS
# -----------------------
st.markdown("""
<style>

/* Champ de saisie */
.stTextInput > div > div > input {
    border-radius: 25px;
    padding: 12px 15px;
    border: 2px solid #ccc;
    outline: none;
}

/* Focus = bordure rouge */
.stTextInput > div > div > input:focus {
    border: 2px solid red !important;
    box-shadow: none !important;
}

/* Bouton WhatsApp */
.stButton > button {
    background-color: #25D366;
    color: white;
    border-radius: 50%;
    height: 45px;
    width: 45px;
    border: none;
    font-size: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Hover bouton */
.stButton > button:hover {
    background-color: #1ebe5d;
}

</style>
""", unsafe_allow_html=True)

# -----------------------
# TITRE
# -----------------------
st.title("💬 Assistant IA")

# -----------------------
# SESSION CHAT
# -----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------
# AFFICHAGE MESSAGES
# -----------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# -----------------------
# INPUT + BOUTON
# -----------------------
col1, col2 = st.columns([8,1])

with col1:
    user_input = st.text_input(
        "Tape ton message...",
        label_visibility="collapsed",
        key="input"
    )

with col2:
    send = st.button("➤")

# -----------------------
# ENVOI MESSAGE
# -----------------------
if send and user_input:
    # message utilisateur
    st.session_state.messages.append({"role": "user", "content": user_input})

    # réponse simple (remplace ici par ton IA)
    response = f"Tu as dit : {user_input}"

    st.session_state.messages.append({"role": "assistant", "content": response})

    # refresh pour afficher
    st.rerun()
