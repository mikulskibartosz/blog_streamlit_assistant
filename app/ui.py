from .ai import AI
from .loader import Loader
import streamlit as st


def show_ui(ai: AI, loader: Loader):
    with st.sidebar:
        reset = st.button("New chat")
        if reset:
            ai.clear_vector_store_and_reset_thread()
            if "messages" in st.session_state:
                st.session_state.messages = []

    st.title("Chat with your documents or YouTube videos")

    if not ai.is_ready():
        st.subheader("Upload your document or enter a YouTube URL")
        youtube_url = st.text_input("Paste the YouTube URL and press Enter", "")
        uploaded_pdf = st.file_uploader("Upload a PDF file", type=["pdf"])

        if youtube_url:
            with st.spinner("Loading transcript..."):
                loader.upload_youtube_transcript(youtube_url)
            st.success("Transcript loaded")
        if uploaded_pdf:
            with st.spinner("Loading PDF..."):
                loader.upload_pdf_file(uploaded_pdf)
            st.success("PDF loaded")

    if ai.is_ready():
        st.subheader("Ask your question")

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "How can I help you?"}
            ]

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input(placeholder="Ask a question:"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.spinner("Thinking..."):
                ai_response = ai.ask(prompt)

            st.session_state.messages.append(
                {"role": "assistant", "content": ai_response}
            )
            st.chat_message("assistant").write(ai_response)
