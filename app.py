import streamlit as st
import streamlit.components.v1 as components
import sqlite3
from datetime import datetime

st.set_page_config(page_title="IA Chat Uni - Persistant", page_icon="🛡️", layout="wide")

def init_db():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp TEXT, 
                  pseudo TEXT, 
                  contenu TEXT)''')
    conn.commit()
    conn.close()

def save_message(pseudo, contenu):
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO messages (timestamp, pseudo, contenu) VALUES (?, ?, ?)", 
              (now, pseudo, contenu))
    conn.commit()
    conn.close()

def load_messages():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute("SELECT timestamp, pseudo, contenu FROM messages ORDER BY id DESC")
    data = c.fetchall()
    conn.close()
    return data

init_db()

query_params = st.query_params
is_admin = query_params.get("boss") == "1"

if is_admin:
    st.markdown('<h1 style="color:red; text-align:center;">🛡️ CONSOLE DE SURVEILLANCE GÉNÉRALE</h1>', unsafe_allow_html=True)
else:
    st.title("🚀 Messagerie Étudiante (Sauvegarde Active)")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Discussion (Historique sauvegardé)")
    
    with st.form("chat_form", clear_on_submit=True):
        nom_user = st.text_input("Ton pseudo", value="Étudiant")
        msg_user = st.text_area("Ton message")
        submit = st.form_submit_button("Envoyer et Sauvegarder")
        
        if submit and msg_user:
            save_message(nom_user, msg_user)
            st.success("Message enregistré dans la base de données !")

    st.divider()
    historique = load_messages()
    
    if is_admin:
        st.write("📂 *Accès à la base de données SQLite :*")
    
    for time, user, text in historique:
        with st.chat_message("user" if not is_admin else "assistant"):
            st.write(f"*{user}* (le {time})")
            st.write(text)

with col2:
    st.subheader("Appel Audio P2P")
    
    audio_code = """
    <div style="background: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #ccc; color: black;">
        <script src="https://unpkg.com/peerjs@1.5.2/dist/peerjs.min.js"></script>
        <p style="font-size: 13px;">Votre ID pour l'appel :</p>
        <div id="peer-id" style="background:#f1f5f9; padding:10px; font-weight:bold; color:#1d4ed8;">Connexion...</div>
        <input type="text" id="dest-id" placeholder="ID du collègue" style="width:100%; margin-top:15px; padding:8px; border-radius:5px;">
        <button onclick="call()" style="width:100%; margin-top:10px; padding:10px; background:#16a34a; color:white; border:none; border-radius:5px; cursor:pointer;">🎤 Appeler maintenant</button>
        <audio id="remoteAudio" autoplay></audio>
        <script>
            const p = new Peer();
            p.on('open', id => { document.getElementById('peer-id').innerText = id; });
            p.on('call', c => {
                navigator.mediaDevices.getUserMedia({audio:true}).then(s => {
                    c.answer(s);
                    c.on('stream', rs => { document.getElementById('remoteAudio').srcObject = rs; });
                });
            });
            function call() {
                const d = document.getElementById('dest-id').value;
                navigator.mediaDevices.getUserMedia({audio:true}).then(s => {
                    const c = p.call(d, s);
                    c.on('stream', rs => { document.getElementById('remoteAudio').srcObject = rs; });
                });
            }
        </script>
    </div>
    """
    components.html(audio_code, height=350)

if is_admin:
    if st.sidebar.button("⚠️ Vider la base de données"):
        conn = sqlite3.connect('chat_history.db')
        c = conn.cursor()
        c.execute("DELETE FROM messages")
        conn.commit()
        conn.close()
        st.rerun()
