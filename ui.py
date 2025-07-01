import streamlit as st
from client import create_agent, execute_task  # Your backend logic

# Page configuration
st.set_page_config(page_title="RepoBot", page_icon="🤖", layout="wide")

# Sidebar content
with st.sidebar:
    st.title("🤖 RepoBot")
    st.markdown("Your GitHub Intelligence Assistant.")
    st.markdown("Ask about pull requests, issues, workflows, and more.")
    st.markdown("---")
    st.caption("Built with mcp-use + fastmcp")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# App title
st.title("💬 RepoBot Chat")

# Custom CSS to fix layout and remove shadow
st.markdown("""
    <style>
    .chat-container {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .user-msg {
        background-color: #e3f2fd;
    }
    .bot-msg {
        background-color: #f1f8e9;
    }
    .stChatInput > div {
        width: 100%;
    }

    /* Remove box shadows from chat elements */
    .chat-container, .stChatInput > div, .stMarkdown {
        box-shadow: none !important;
    }

    /* Remove spinner container shadow */
    div[data-testid="stSpinner"] {
        box-shadow: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Show chat history
for chat in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(f"<div class='chat-container user-msg'>{chat['user']}</div>", unsafe_allow_html=True)
    with st.chat_message("assistant"):
        st.markdown(f"<div class='chat-container bot-msg'>{chat['agent']}</div>", unsafe_allow_html=True)

# Input box
prompt = st.chat_input("Ask about GitHub repositories...")

if prompt:
    # Show user message
    with st.chat_message("user"):
        st.markdown(f"<div class='chat-container user-msg'>{prompt}</div>", unsafe_allow_html=True)

    agent = create_agent()
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = execute_task(agent, prompt)
            except Exception as e:
                response = f"❌ Error: {e}"
            st.markdown(f"<div class='chat-container bot-msg'>{response}</div>", unsafe_allow_html=True)

    # Save chat to session
    st.session_state.chat_history.append({
        "user": prompt,
        "agent": response
    })
