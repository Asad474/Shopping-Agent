import os
from pathlib import Path
import streamlit as st

from shopping_agent import BASE_DIR, agent, get_text

st.set_page_config(page_title="AI Shopping Agent", page_icon="🤖", layout="wide")

# ---------------------------------------------------------------------------
# Header & Chat Controls
# ---------------------------------------------------------------------------
header_col1, header_col2 = st.columns([5, 1])
with header_col1:
    st.title("AI Shopping Assistant 🤖")
    st.caption("Tell me what you want — I'll search, rate, and order the best match for you.")
with header_col2:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pop("queued_prompt", None)
        st.session_state.pop("queued_image", None)
        st.rerun()

resources_dir = Path(BASE_DIR) / "resources"

# ---------------------------------------------------------------------------
# In-Chat Image Search Helper (Samples & Drag-and-Drop)
# ---------------------------------------------------------------------------
sample_images = []
if resources_dir.exists():
    sample_images = [
        f.name
        for f in resources_dir.iterdir()
        if f.suffix.lower() in [".png", ".jpg", ".jpeg"]
        and not f.name.startswith("upload_")
    ]

with st.expander("📷 Image Search Options (Upload or pick a sample photo)", expanded=False):
    inline_upload = st.file_uploader(
        "Upload a product image to search:",
        type=["png", "jpg", "jpeg"],
        key="chat_inline_uploader",
    )
    if inline_upload is not None:
        resources_dir.mkdir(parents=True, exist_ok=True)
        upload_path = resources_dir / f"upload_{inline_upload.name}"
        with open(upload_path, "wb") as f:
            f.write(inline_upload.getbuffer())
        st.image(str(upload_path), width=200, caption="Uploaded Image")
        if st.button("🔍 Search This Image", key="btn_search_uploaded_img"):
            st.session_state["queued_image"] = str(upload_path)
            st.session_state["queued_prompt"] = (
                f"Please search for the product in this image: {upload_path}"
            )
            st.rerun()

    if sample_images:
        st.divider()
        st.caption("Or test with a sample store image:")
        cols = st.columns(min(len(sample_images), 4))
        for idx, img_name in enumerate(sorted(sample_images)):
            col = cols[idx % 4]
            img_path = resources_dir / img_name
            with col:
                st.image(str(img_path), caption=img_name, use_container_width=True)
                if st.button(
                    f"Search {img_name}",
                    key=f"btn_sample_{img_name}",
                    use_container_width=True,
                ):
                    st.session_state["queued_image"] = str(img_path)
                    st.session_state["queued_prompt"] = (
                        f"Please search for the product in this image: {img_path}"
                    )
                    st.rerun()

# ---------------------------------------------------------------------------
# Chat Conversation History
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image") and os.path.exists(msg["image"]):
            st.image(msg["image"], width=220, caption="Product Photo")
        st.markdown(msg["content"].replace("$", r"\$"))

# ---------------------------------------------------------------------------
# Chat Input (Directly accepts text and/or file attachments via paperclip)
# ---------------------------------------------------------------------------
queued_prompt = st.session_state.pop("queued_prompt", None)
queued_image = st.session_state.pop("queued_image", None)

chat_val = st.chat_input(
    "Type what you want to buy or attach a product image...",
    accept_file=True,
    file_type=["png", "jpg", "jpeg"],
)

user_text = ""
image_path_to_send = None

if queued_prompt:
    user_text = queued_prompt
    image_path_to_send = queued_image
elif chat_val:
    if hasattr(chat_val, "text"):
        user_text = (chat_val.text or "").strip()
        uploaded_files = getattr(chat_val, "files", [])
    else:
        user_text = str(chat_val).strip()
        uploaded_files = []

    if uploaded_files:
        uploaded_file = uploaded_files[0]
        resources_dir.mkdir(parents=True, exist_ok=True)
        upload_path = resources_dir / f"upload_{uploaded_file.name}"
        with open(upload_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        image_path_to_send = str(upload_path)

        if not user_text:
            user_text = f"Please search for the product in this image: {image_path_to_send}"
        else:
            user_text = (
                f"Please search for the product in this image: {image_path_to_send}. "
                f"Note: {user_text}"
            )

if user_text:
    user_msg = {"role": "user", "content": user_text}
    if image_path_to_send:
        user_msg["image"] = image_path_to_send
    st.session_state.messages.append(user_msg)

    with st.chat_message("user"):
        if image_path_to_send:
            st.image(image_path_to_send, width=220, caption="Product Photo")
        st.markdown(user_text.replace("$", r"\$"))

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            clean_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
            result = agent.invoke({"messages": clean_messages})
            response = get_text(result["messages"][-1]).replace("`", "")

        st.markdown(response.replace("$", r"\$"))

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
