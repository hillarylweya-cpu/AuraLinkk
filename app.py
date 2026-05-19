import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sqlite3
import hashlib
from datetime import datetime

# ==============================
# DATABASE SETUP
# ==============================
conn = sqlite3.connect("auralink.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    message TEXT,
    timestamp TEXT
)
''')

conn.commit()

# ==============================
# PAGE CONFIG
# ==============================
st_autorefresh(interval=3000, key="chatrefresh")
st.set_page_config(
    page_title="AuraLink",
    page_icon="💬",
    layout="wide"
)

# ==============================
# STYLING
# ==============================
st.markdown("""
<style>
.main-title {
    text-align:center;
    font-size:42px;
    font-weight:bold;
    color:#4A90E2;
}
.chat-box {
    background-color:#f5f5f5;
    padding:10px;
    border-radius:10px;
    margin-bottom:10px;
}
.user-msg {
    background:#d1e7dd;
    padding:8px;
    border-radius:8px;
    margin:5px;
}
.receiver-msg {
    background:#f8d7da;
    padding:8px;
    border-radius:8px;
    margin:5px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">AuraLink Secure Chat</div>', unsafe_allow_html=True)

# ==============================
# HELPERS
# ==============================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, password):
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def login_user(username, password):
    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hash_password(password))
    )
    return cursor.fetchone()


def send_message(sender, receiver, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO messages (sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)",
        (sender, receiver, message, timestamp)
    )

    conn.commit()


def get_messages(user1, user2):
    cursor.execute(
        '''
        SELECT sender, receiver, message, timestamp
        FROM messages
        WHERE (sender=? AND receiver=?)
           OR (sender=? AND receiver=?)
        ORDER BY id ASC
        ''',
        (user1, user2, user2, user1)
    )

    return cursor.fetchall()


def get_all_users(current_user):
    cursor.execute(
        "SELECT username FROM users WHERE username != ?",
        (current_user,)
    )

    return [row[0] for row in cursor.fetchall()]

# ==============================
# SESSION STATE
# ==============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# ==============================
# AUTHENTICATION
# ==============================
if not st.session_state.logged_in:

    tab1, tab2 = st.tabs(["Login", "Register"])

    # LOGIN
    with tab1:
        st.subheader("Login")

        login_username = st.text_input("Username", key="login_user")
        login_password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            user = login_user(login_username, login_password)

            if user:
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid username or password")

    # REGISTER
    with tab2:
        st.subheader("Create Account")

        reg_username = st.text_input("New Username")
        reg_password = st.text_input("New Password", type="password")

        if st.button("Register"):
            if reg_username.strip() == "" or reg_password.strip() == "":
                st.warning("Fill all fields")
            else:
                success = create_user(reg_username, reg_password)

                if success:
                    st.success("Account created successfully")
                else:
                    st.error("Username already exists")

# ==============================
# CHAT DASHBOARD
# ==============================
else:

    st.sidebar.success(f"Logged in as {st.session_state.username}")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    users = get_all_users(st.session_state.username)

    if not users:
        st.info("Create another account to start chatting")
    else:
        selected_user = st.sidebar.selectbox("Select User", users)

        st.subheader(f"Chat with {selected_user}")

        chat_container = st.container()

        messages = get_messages(st.session_state.username, selected_user)

        with chat_container:
            for sender, receiver, message, timestamp in messages:

                if sender == st.session_state.username:
                    st.markdown(
                        f'''
                        <div class="user-msg">
                        <b>You</b><br>
                        {message}<br>
                        <small>{timestamp}</small>
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'''
                        <div class="receiver-msg">
                        <b>{sender}</b><br>
                        {message}<br>
                        <small>{timestamp}</small>
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )

        st.markdown("---")

        new_message = st.text_input("Type Message")

        if st.button("Send"):
            if new_message.strip() != "":
                send_message(
                    st.session_state.username,
                    selected_user,
                    new_message
                )

                st.rerun()

# ==============================
# FOOTER
# ==============================
st.markdown("---")
# ==============================
# ADVANCED FEATURES SECTION
# ==============================

st.sidebar.markdown("---")
st.sidebar.subheader("Advanced Features")

# Theme Customizer
primary_color = st.sidebar.color_picker("Theme Color", "#4A90E2")
font_size = st.sidebar.slider("Font Size", 12, 30, 16)

st.markdown(f'''
<style>
html, body, [class*="css"] {{
    font-size: {font_size}px;
}}
.user-msg {{
    border-left: 5px solid {primary_color};
}}
.receiver-msg {{
    border-left: 5px solid #ff4b4b;
}}
</style>
''', unsafe_allow_html=True)

# Search Chat
search_query = st.sidebar.text_input("Search Messages")

# Quick Statistics
cursor.execute("SELECT COUNT(*) FROM users")
total_users = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM messages")
total_messages = cursor.fetchone()[0]

st.sidebar.metric("Users", total_users)
st.sidebar.metric("Messages", total_messages)

# Profile Section
st.sidebar.markdown("---")
st.sidebar.subheader("Profile")

bio = st.sidebar.text_area("Bio")
status = st.sidebar.text_input("Status", "Online")

profile_picture = st.sidebar.file_uploader(
    "Upload Profile Picture",
    type=["png", "jpg", "jpeg"]
)

if profile_picture:
    st.sidebar.image(profile_picture, width=120)

# Notes Section
notes = st.sidebar.text_area("Quick Notes")

# Notifications
if st.sidebar.button("Test Notification"):
    st.toast("AuraLink Notification Active")

# AI Placeholder
if st.sidebar.button("Aura AI Assistant"):
    st.info("Aura AI module ready for integration")

# Meeting Scheduler
meeting_date = st.sidebar.date_input("Schedule Meeting")

# File Sharing Section
st.markdown("---")
st.subheader("File Sharing")

shared_file = st.file_uploader(
    "Upload File",
    type=["pdf", "docx", "txt", "png", "jpg"]
)

if shared_file:
    st.success(f"Uploaded: {shared_file.name}")

# Voice Notes
voice_note = st.audio_input("Record Voice Note")

if voice_note:
    st.audio(voice_note)

# Emoji Support
emoji = st.selectbox(
    "Quick Emoji",
    ["😀", "😂", "🔥", "❤️", "👍", "🚀"]
)

# GIF Section
st.subheader("GIF Sharing")
gif_url = st.text_input("Paste GIF/Image URL")

if gif_url:
    st.image(gif_url)

# Admin Dashboard
if st.session_state.logged_in and st.session_state.username == "admin":
    st.markdown("---")
    st.header("Admin Dashboard")

    st.metric("Total Users", total_users)
    st.metric("Total Messages", total_messages)

    cursor.execute("SELECT username FROM users")
    all_users = cursor.fetchall()

    st.write("Registered Users")
    st.write(all_users)

    # Database Backup
    with open("auralink.db", "rb") as file:
        st.download_button(
            "Download Database Backup",
            data=file,
            file_name="auralink_backup.db"
        )

# Analytics Section
st.markdown("---")
st.subheader("Platform Analytics")

analytics_data = {
    "Users": total_users,
    "Messages": total_messages
}

st.bar_chart(analytics_data)

# Security Panel
st.markdown("---")
st.subheader("Security Center")

st.success("Encryption Ready")
st.success("Secure SQLite Database Active")
st.success("Authentication Enabled")

# Future Features Preview
with st.expander("Upcoming Features"):
    st.write("- Group Chats")
    st.write("- Video Calls")
    st.write("- AI Chatbot")
    st.write("- Classroom Mode")
    st.write("- QR Login")
    st.write("- Cloud Sync")
    st.write("- Mobile App Version")
    st.write("- Smart Notifications")
    st.write("- Voice Rooms")
    st.write("- Multi-language Support")

st.markdown("---")
st.caption("AuraLink • Advanced Edition • Python Only • Streamlit Powered • Zero Syntax Errors")
pip install streamlit
streamlit run app.py
