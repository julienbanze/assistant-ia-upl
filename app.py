import streamlit as st
from groq import Groq

st.set_page_config(page_title="IA Assistant UPL", page_icon="🎓", layout="centered")

try:
    
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("Erreur : La clé API est introuvable dans secrets.toml.")
    st.stop()

st.markdown("""
    <style>
    .stChatInputContainer { padding-bottom: 20px; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎓 Assistant IA Universitaire")
st.write("Posez vos questions sur vos cours, vos mémoires ou votre orientation à l'UPL.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ex: Comment faire un plan de mémoire ?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
  [22:05, 07/02/2026] JULIEN BANZE: on doit modifier de 49 à 64
[22:05, 07/02/2026] JULIEN BANZE: try:
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": "Tu es un assistant IA utile et polyvalent, créé par Julien BANZE KANDOLO."
                    },
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
            )
            st.session_state.messages.append({"role": "assistant", "content": reponse})
            
        except Exception as e:
            st.error("Désolé, je rencontre une petite difficulté technique. Réessaye dans un instant.")

st.markdown("---")

st.markdown("© 2026 | Projet de fin d'études - Julien BANZE KANDOLO | Université Protestante de Lubumbashi")
