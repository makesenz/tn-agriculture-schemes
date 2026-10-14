import os
import uuid
from pathlib import Path

import requests
import streamlit as st


# =========================================================
# CONFIGURATION
# =========================================================

APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = APP_DIR / "static" / "Emblem_of_Tamil_Nadu.svg.webp"

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000/api/chat",
)

APP_TITLE = "தமிழ்நாடு வேளாண்மை திட்டங்கள் எளிய வழிகாட்டி"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CSS — STYLING ONLY
# HTML CONTENT IS NOT USED FOR UI RENDERING
# =========================================================

st.markdown(
    """
    <style>
    :root {
        --forest: #176b49;
        --forest-dark: #124d37;
        --text-main: #26372d;
        --text-muted: #788379;
        --border: #e0e7e1;
        --surface-soft: #f7faf7;
        --green-soft: #edf7ef;
    }

    .stApp {
        background: #f8faf8;
        color: var(--text-main);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1120px;
        padding-top: 3rem;
        padding-bottom: 2rem;
    }

    #MainMenu,
    footer {
        visibility: hidden;
    }

    /* Sidebar */

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding: 1rem 1rem 1.5rem;
    }

    [data-testid="stSidebar"] button {
        border-radius: 11px;
        min-height: 42px;
        font-weight: 600;
    }

    [data-testid="stSidebar"] button[kind="primary"] {
        background: var(--forest) !important;
        color: white !important;
        border: 1px solid var(--forest) !important;
    }

    [data-testid="stSidebar"] button[kind="primary"]:hover {
        background: var(--forest-dark) !important;
        border-color: var(--forest-dark) !important;
    }

    [data-testid="stSidebar"] button[kind="primary"] p,
    [data-testid="stSidebar"] button[kind="primary"] span {
        color: white !important;
    }

    .sidebar-section-label {
        color: var(--text-muted);
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1.5px;
        margin: 24px 0 10px;
    }

    .sidebar-muted {
        color: var(--text-muted);
        font-size: 13px;
        line-height: 1.7;
    }

    .brand-title {
        font-size: 15px;
        line-height: 1.7;
        font-weight: 800;
        color: var(--forest);
    }

    .brand-subtitle {
        font-size: 12px;
        line-height: 1.7;
        color: var(--text-muted);
    }

    /* Main welcome screen */

    .hero-eyebrow {
        color: var(--forest);
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1.8px;
        margin-bottom: 18px;
    }

    .hero-title {
        font-size: clamp(32px, 4vw, 46px);
        line-height: 1.3;
        font-weight: 800;
        letter-spacing: -1px;
        color: var(--text-main);
        margin: 0 0 16px 0;
    }

    .hero-description {
        color: var(--text-muted);
        font-size: 15px;
        line-height: 1.9;
        margin-bottom: 22px;
    }

    .status-pill {
        display: inline-block;
        background: #eff8f0;
        border: 1px solid #d6e9d9;
        border-radius: 24px;
        padding: 10px 15px;
        color: #245a3e;
        font-size: 12px;
        font-weight: 700;
    }

    .suggestions-heading {
        color: var(--text-muted);
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1.5px;
        margin: 32px 0 12px;
    }

    /* Chat messages */

    [data-testid="stChatMessage"] {
        background: white;
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 18px;
        margin-bottom: 14px;
    }

    [data-testid="stChatInput"] {
        background: white;
        border-radius: 14px;
        border-color: var(--border);
    }

    /* Source cards */

    .source-heading {
        color: var(--forest);
        font-size: 14px;
        font-weight: 800;
        margin-bottom: 10px;
    }

    .source-name {
        color: var(--text-main);
        font-size: 13px;
        font-weight: 700;
        overflow-wrap: anywhere;
    }

    .source-page {
        color: var(--text-muted);
        font-size: 12px;
        margin-top: 3px;
    }

    .source-box {
        background: white;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 14px 16px;
        margin-top: 10px;
    }

    .footer-note {
        color: var(--text-muted);
        font-size: 11px;
        line-height: 1.8;
        text-align: center;
        margin-top: 40px;
    }

    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"] {
            padding-top: 1.5rem;
        }

        .hero-title {
            font-size: 32px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "active_conversation" not in st.session_state:
    st.session_state.active_conversation = None

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


def create_conversation():
    conversation_id = str(uuid.uuid4())

    st.session_state.conversations[conversation_id] = {
        "title": "New conversation",
        "messages": [],
    }

    st.session_state.active_conversation = conversation_id


def get_active_conversation():
    conversation_id = st.session_state.active_conversation

    if conversation_id is None:
        return None

    return st.session_state.conversations.get(conversation_id)


# =========================================================
# BACKEND API
# =========================================================

def ask_backend(question):
    try:
        response = requests.post(
            API_URL,
            json={"question": question},
            timeout=120,
        )

        response.raise_for_status()
        data = response.json()

        answer = data.get("answer", data.get("response", ""))
        sources = data.get("sources", [])

        if not answer:
            answer = (
                "மன்னிக்கவும், இந்தக் கேள்விக்கான பதிலை "
                "தற்போது பெற முடியவில்லை."
            )

        return {
            "answer": str(answer),
            "sources": sources if isinstance(sources, list) else [],
            "error": False,
        }

    except requests.exceptions.ConnectionError:
        return {
            "answer": (
                "Backend server-ஐ connect செய்ய முடியவில்லை. "
                "FastAPI server இயங்குகிறதா என்று சரிபார்க்கவும்."
            ),
            "sources": [],
            "error": True,
        }

    except requests.exceptions.Timeout:
        return {
            "answer": (
                "பதில் பெற அதிக நேரம் ஆகிறது. "
                "தயவுசெய்து மீண்டும் முயற்சி செய்யவும்."
            ),
            "sources": [],
            "error": True,
        }

    except requests.exceptions.HTTPError as exc:
        status_code = (
            exc.response.status_code
            if exc.response is not None
            else "unknown"
        )

        return {
            "answer": (
                f"API request தோல்வியடைந்தது (HTTP {status_code}). "
                "Backend terminal logs-ஐ சரிபார்க்கவும்."
            ),
            "sources": [],
            "error": True,
        }

    except (ValueError, requests.exceptions.RequestException):
        return {
            "answer": (
                "பதில் பெறும்போது ஒரு பிழை ஏற்பட்டது. "
                "மீண்டும் முயற்சி செய்யவும்."
            ),
            "sources": [],
            "error": True,
        }


def process_question(question):
    question = question.strip()

    if not question:
        return

    if st.session_state.active_conversation is None:
        create_conversation()

    conversation = get_active_conversation()

    if conversation is None:
        create_conversation()
        conversation = get_active_conversation()

    conversation["messages"].append({
        "role": "user",
        "content": question,
    })

    if conversation["title"] == "New conversation":
        conversation["title"] = (
            question[:42] + "…"
            if len(question) > 42
            else question
        )

    with st.spinner("திட்ட விவரங்களைச் சரிபார்க்கிறோம்..."):
        result = ask_backend(question)

    conversation["messages"].append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
        "error": result["error"],
    })


# =========================================================
# SOURCE RENDERING — NATIVE STREAMLIT COMPONENTS
# =========================================================


def render_sources(sources):
    if not sources:
        return

    # Compact, collapsible source references
    with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
        for source in sources:
            if isinstance(source, str):
                st.markdown(f"- {source}")

            elif isinstance(source, dict):
                filename = (
                    source.get("filename")
                    or source.get("file_name")
                    or source.get("source")
                    or source.get("file")
                    or source.get("title")
                    or "Official document"
                )

                page = (
                    source.get("page")
                    or source.get("page_number")
                    or source.get("page_no")
                )

                url = source.get("url") or source.get("link")

                if page is not None and source.get(
                    "page_is_zero_based", False
                ):
                    try:
                        page = int(page) + 1
                    except (TypeError, ValueError):
                        pass

                label = str(filename)

                if page is not None:
                    label += f" · Page {page}"

                if isinstance(url, str) and url.startswith(
                    ("https://", "http://")
                ):
                    st.markdown(f"- [{label}]({url})")
                else:
                    st.markdown(f"- {label}")

            else:
                st.markdown(f"- {str(source)}")



# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=76)

    st.markdown(
        '<div class="brand-title">'
        'தமிழ்நாடு வேளாண்மை'
        '</div>'
        '<div class="brand-subtitle">'
        'திட்டங்கள் எளிய வழிகாட்டி'
        '</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    if st.button(
        "＋ New conversation",
        type="primary",
        use_container_width=True,
        key="new_conversation_button",
    ):
        create_conversation()
        st.rerun()

    st.markdown(
        '<div class="sidebar-section-label">RECENT CHATS</div>',
        unsafe_allow_html=True,
    )

    conversations = st.session_state.conversations

    if not conversations:
        st.markdown(
            '<div class="sidebar-muted">'
            'Your recent conversations will appear here.'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        for conversation_id, conversation_data in (
            list(conversations.items())[::-1]
        ):
            title = conversation_data["title"]

            if len(title) > 32:
                title = title[:32] + "…"

            is_active = (
                conversation_id
                == st.session_state.active_conversation
            )

            label = f"{'● ' if is_active else ''}{title}"

            if st.button(
                label,
                key=f"conversation_{conversation_id}",
                use_container_width=True,
            ):
                st.session_state.active_conversation = conversation_id
                st.rerun()

    st.divider()

    st.markdown("### 🔎 Evidence-based answers")
    st.caption(
        "Answers are grounded in available government documents "
        "and agricultural scheme sources. Check cited sources "
        "for scheme information."
    )


# =========================================================
# MAIN WORKSPACE
# =========================================================

conversation = get_active_conversation()
has_messages = bool(
    conversation and conversation.get("messages")
)


if not has_messages:
    st.markdown(
        '<div class="hero-eyebrow">'
        'AGRICULTURE · GOVERNMENT SCHEMES'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-title">'
        'How can we help you today?'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-description">'
        'தமிழ்நாடு விவசாயத் திட்டங்கள், மானியங்கள், தகுதிகள் '
        'மற்றும் விண்ணப்ப நடைமுறைகளைப் பற்றி கேளுங்கள். '
        'Ask in Tamil or English.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="status-pill">'
        '🟢 AI assistant · Source-based responses'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="suggestions-heading">'
        'SUGGESTED QUESTIONS'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "🚜 Machinery subsidies",
            use_container_width=True,
            key="suggest_machinery",
        ):
            st.session_state.pending_question = (
                "What machinery subsidies are available "
                "for farmers in Tamil Nadu?"
            )
            st.rerun()

    with col2:
        if st.button(
            "📋 Farmer eligibility",
            use_container_width=True,
            key="suggest_eligibility",
        ):
            st.session_state.pending_question = (
                "What are the eligibility criteria for "
                "agricultural schemes in Tamil Nadu?"
            )
            st.rerun()

    col3, col4 = st.columns(2)

    with col3:
        if st.button(
            "🌱 Seed subsidies",
            use_container_width=True,
            key="suggest_seeds",
        ):
            st.session_state.pending_question = (
                "What seed subsidies are available "
                "for farmers in Tamil Nadu?"
            )
            st.rerun()

    with col4:
        if st.button(
            "🧾 Application process",
            use_container_width=True,
            key="suggest_application",
        ):
            st.session_state.pending_question = (
                "How can I apply for agricultural "
                "government schemes in Tamil Nadu?"
            )
            st.rerun()


else:
    for message in conversation["messages"]:
        role = message["role"]
        avatar = "🧑‍🌾" if role == "user" else "🌾"

        with st.chat_message(role, avatar=avatar):
            st.markdown(message["content"])

            if role == "assistant":
                render_sources(message.get("sources", []))

                if (
                    not message.get("sources")
                    and not message.get("error", False)
                ):
                    st.caption(
                        "No source references were returned by the API."
                    )


# =========================================================
# CHAT INPUT
# =========================================================

submitted_question = st.chat_input(
    "Ask about agriculture schemes... / தமிழில் கேளுங்கள்"
)

question_to_process = None

if st.session_state.pending_question:
    question_to_process = st.session_state.pending_question
    st.session_state.pending_question = None

elif submitted_question:
    question_to_process = submitted_question

if question_to_process:
    process_question(question_to_process)
    st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "தமிழ்நாடு வேளாண்மை திட்டங்கள் எளிய வழிகாட்டி · "
    "Verify scheme eligibility and current availability "
    "with the relevant official department."
)