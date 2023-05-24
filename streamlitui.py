import os
import tempfile
import streamlit as st
from streamlit_chat import message
from pdfquery import PDFQuery

st.set_page_config(page_title="ChatPDF")


def display_messages():
    st.subheader("Chat")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        message(msg, is_user=is_user, key=str(i))
    st.session_state["thinking_spinner"] = st.empty()


def process_input():
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        with st.session_state["thinking_spinner"], st.spinner(f"Thinking"):
            query_text = st.session_state["pdfquery"].ask(user_text)

        st.session_state["messages"].append((user_text, True))
        st.session_state["messages"].append((query_text, False))


def read_and_save_file():
    st.session_state["pdfquery"].forget()  # to reset the knowledge base
    st.session_state["messages"] = []
    st.session_state["user_input"] = ""

    for file in st.session_state["file_uploader"]:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name

        with st.session_state["ingestion_spinner"], st.spinner(f"Ingesting {file.name}"):
            st.session_state["pdfquery"].ingest(file_path)
        os.remove(file_path)


def is_openai_api_key_set() -> bool:
    return len(st.session_state["OPENAI_API_KEY"]) > 0


def main():
    if len(st.session_state) == 0:
        st.session_state["messages"] = []
        st.session_state["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")
        if is_openai_api_key_set():
            st.session_state["pdfquery"] = PDFQuery(st.session_state["OPENAI_API_KEY"])
        else:
            st.session_state["pdfquery"] = None

    st.header("ChatPDF")

    if st.text_input("OpenAI API Key", value=st.session_state["OPENAI_API_KEY"], key="input_OPENAI_API_KEY", type="password"):
        if (
            len(st.session_state["input_OPENAI_API_KEY"]) > 0
            and st.session_state["input_OPENAI_API_KEY"] != st.session_state["OPENAI_API_KEY"]
        ):
            st.session_state["OPENAI_API_KEY"] = st.session_state["input_OPENAI_API_KEY"]
            if st.session_state["pdfquery"] is not None:
                st.warning("Please, upload the files again.")
            st.session_state["messages"] = []
            st.session_state["user_input"] = ""
            st.session_state["pdfquery"] = PDFQuery(st.session_state["OPENAI_API_KEY"])

    st.subheader("Upload a document")
    st.file_uploader(
        "Upload document",
        type=["pdf"],
        key="file_uploader",
        on_change=read_and_save_file,
        label_visibility="collapsed",
        accept_multiple_files=True,
        disabled=not is_openai_api_key_set(),
    )

    st.session_state["ingestion_spinner"] = st.empty()

    display_messages()
    st.text_input("Message", key="user_input", disabled=not is_openai_api_key_set(), on_change=process_input)

    st.divider()
    st.markdown("Source code: [Github](https://github.com/Anil-matcha/ChatPDF)")


if __name__ == "__main__":
    main()