import streamlit as st
from groq import Groq
import pandas as pd

from database import (
register_user,
login_user,
save_search,
save_chat,
connect_db
)

st.set_page_config(
page_title="Assistant Académique IA 🎓",
page_icon="🎓",
layout="wide"
)

st.title("🎓 Assistant Académique IA")

@st.cache_resource
def init_client():

    return Groq(api_key=st.secrets["GROQ_API_KEY"])

client = init_client()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user" not in st.session_state:
    st.session_state.user = None


menu = st.sidebar.selectbox(
"Menu",
[
"Inscription",
"Connexion",
"Assistant IA",
"Admin Dashboard"
]
)

# -------------------
# INSCRIPTION
# -------------------

if menu == "Inscription":

    st.header("Créer un compte")

    nom = st.text_input("Nom")
    email = st.text_input("Email")
    password = st.text_input("Mot de passe",type="password")

    if st.button("S'inscrire"):

        register_user(nom,email,password)

        st.success("Compte créé avec succès")


# -------------------
# LOGIN
# -------------------

elif menu == "Connexion":

    st.header("Connexion")

    email = st.text_input("Email")
    password = st.text_input("Mot de passe",type="password")

    if st.button("Se connecter"):

        user = login_user(email,password)

        if user:

            st.session_state.user = user
            st.success("Connexion réussie")

        else:

            st.error("Email ou mot de passe incorrect")


# -------------------
# ASSISTANT IA
# -------------------

elif menu == "Assistant IA":

    if st.session_state.user is None:

        st.warning("Veuillez vous connecter")

    else:

        for msg in st.session_state.messages:

            with st.chat_message(msg["role"]):

                st.markdown(msg["content"])


        prompt = st.chat_input("Posez votre question académique...")

        if prompt:

            st.session_state.messages.append({
            "role":"user",
            "content":prompt
            })

            save_chat(st.session_state.user["id"],"user",prompt)

            st.chat_message("user").markdown(prompt)

            with st.chat_message("assistant"):

                placeholder = st.empty()

                full_response = ""

                messages = [{
                "role":"system",
                "content":"Tu es un assistant académique intelligent."
                }]

                for m in st.session_state.messages:

                    messages.append(m)

                stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                stream=True
                )

                for chunk in stream:

                    if chunk.choices[0].delta.content:

                        full_response += chunk.choices[0].delta.content

                        placeholder.markdown(full_response + "▌")

                placeholder.markdown(full_response)

            st.session_state.messages.append({
            "role":"assistant",
            "content":full_response
            })

            save_chat(st.session_state.user["id"],"assistant",full_response)

            save_search(
            st.session_state.user["id"],
            prompt,
            full_response
            )

# -------------------
# ADMIN
# -------------------

elif menu == "Admin Dashboard":

    st.title("Dashboard Admin")

    db = connect_db()

    st.subheader("Utilisateurs")

    users = pd.read_sql("SELECT * FROM users",db)

    st.dataframe(users)

    st.subheader("Recherches")

    recherches = pd.read_sql("""

    SELECT
    users.nom,
    users.email,
    recherches.question,
    recherches.date_recherche

    FROM recherches

    JOIN users
    ON users.id = recherches.user_id

    """,db)

    st.dataframe(recherches)

    st.subheader("Conversations")

    chat = pd.read_sql("""

    SELECT
    users.nom,
    chat_history.role,
    chat_history.message,
    chat_history.date_message

    FROM chat_history

    JOIN users
    ON users.id = chat_history.user_id

    """,db)

    st.dataframe(chat)
