import streamlit as st
from groq import Groq

# ---------------------------
# CONFIG PAGE
# ---------------------------

st.set_page_config(
    page_title="Assistant Académique IA",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Assistant Académique IA")
st.write("Posez vos questions académiques ou utilisez le micro.")

# ---------------------------
# CLIENT GROQ
# ---------------------------

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ---------------------------
# PROMPT SYSTEME
# ---------------------------

SYSTEM_PROMPT = """
Tu es un assistant académique.

Réponds toujours en français.

Structure :
Titre
Introduction
Explication
Conclusion
"""

# ---------------------------
# MEMOIRE CHAT
# ---------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------
# AFFICHAGE CHAT
# ---------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------
# INPUT TEXTE
# ---------------------------

prompt = st.chat_input("Posez votre question académique...")

if prompt:

    # afficher message utilisateur
    st.chat_message("user").markdown(prompt)

    # sauvegarde
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    # réponse IA
    with st.chat_message("assistant"):

        placeholder = st.empty()
        full_response = ""

        try:

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + st.session_state.messages

            stream = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages,
                stream=True
            )

            for chunk in stream:

                if chunk.choices[0].delta.content:

                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

        except Exception as e:

            st.error("Erreur IA : vérifiez votre clé API ou votre connexion.")
            st.write(e)

    # sauvegarder réponse
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )
