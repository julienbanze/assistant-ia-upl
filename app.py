import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="Assistant IA - Julien Banze Kandolo",
    page_icon="🎓",
    layout="centered"
)

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    h1, h3 { color: #1E3A8A; }
    .stChatInput button {
        background-color: #1E3A8A !important;
        color: white !important;
    }
    .stChatMessage { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception:
    st.error("⚠️ Erreur : La clé API 'GROQ_API_KEY' est manquante dans les Secrets Streamlit.")
    st.stop()


st.title("🎓 Assistant IA Académique")
st.markdown(f"Étudiant : Julien Banze Kandolo")
st.info("Université Protestante de Lubumbashi (UPL)")
st.write("---")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Bonjour ! Je suis l'assistant IA conçu par Julien Banze Kandolo. Je suis prêt à vous aider pour vos recherches. Que souhaitez-vous savoir ?"
        }
    ]


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("Je suis votre assistant academique..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
           
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system", 
                        "content": "Tu es l'assistant IA de Julien Banze Kandolo, étudiant à l'UPL. Tu es expert, poli et académique. Tu mentionnes Julien Banze Kandolo comme ton créateur."
                    },
                    *[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ]
                ],
                temperature=0.7,
            )
            
            reponse = completion.choices[0].message.content
            st.markdown(reponse)
            st.session_state.messages.append({"role": "assistant", "content": reponse})
            
        except Exception as e:
            st.error(f"Erreur : {str(e)}")

