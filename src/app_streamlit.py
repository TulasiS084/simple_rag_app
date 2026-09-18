import streamlit as st
import streamlit.components.v1 as components
import os
import sys
import tempfile
import time
import json
import re
from typing import List, Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.rag_pipeline.pipeline import RAGPipeline
    from src.rag_pipeline.config import RAGConfig
    from src.create_sample_pdf import generate_sample_pdf
    from src.rag_pipeline.voice import generate_speech_audio, clean_text_for_speech
except ImportError:
    from rag_pipeline.pipeline import RAGPipeline
    from rag_pipeline.config import RAGConfig
    from create_sample_pdf import generate_sample_pdf
    from rag_pipeline.voice import generate_speech_audio, clean_text_for_speech

# -----------------------------------------------------------------------------
# Streamlit Page Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="RAG AI Voice & Chatbot Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ChatGPT-style UI
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background: linear-gradient(135deg, #1E222A 0%, #282C34 100%);
        border: 1px solid #3E4451;
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 12px;
        color: #ECEFF4;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
    }
    .metric-value {
        font-size: 22px;
        font-weight: 700;
        color: #61AFEF;
    }
    .metric-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #ABB2BF;
        margin-bottom: 2px;
    }
    /* Source Chunk Box */
    .source-box {
        background-color: #21252B;
        border-left: 4px solid #98C379;
        border-radius: 6px;
        padding: 10px 14px;
        margin: 8px 0;
        font-size: 13px;
        line-height: 1.5;
        color: #ABB2BF;
    }
    .source-meta {
        font-size: 11px;
        font-weight: 600;
        color: #E5C07B;
        margin-bottom: 4px;
    }
    /* Button Polish */
    div.stButton > button {
        border-radius: 18px;
        transition: all 0.2s ease;
        font-weight: 500;
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 3px 6px rgba(97, 175, 239, 0.25);
    }
    /* Native Chat Input */
    div[data-testid="stChatInput"] {
        border-radius: 24px;
        border: 1px solid #4B5263;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Pipeline Initialization (Cached in session)
# -----------------------------------------------------------------------------
@st.cache_resource
def load_pipeline():
    config = RAGConfig(
        chunk_size=500,
        chunk_overlap=50,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        collection_name="rag_dashboard_collection",
        top_k=3,
        llm_provider="fallback"
    )
    return RAGPipeline(config)

pipeline = load_pipeline()

# -----------------------------------------------------------------------------
# Session State Management
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Hello! I am your RAG AI Voice Assistant.**\n\n"
                "📌 **How to interact:**\n"
                "- 📁 Upload any PDF or document in the sidebar, or click **'⚡ Load Sample Paper'**.\n"
                "- 🎙️ Use the **Voice Dictation** tool on the right to speak questions.\n"
                "- 🔊 Click the **speaker button on the bottom-left** of any answer to hear it spoken loud and clear!"
            ),
            "sources": []
        }
    ]

if "indexed_docs" not in st.session_state:
    st.session_state.indexed_docs = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "active_audio_idx" not in st.session_state:
    st.session_state.active_audio_idx = None

# -----------------------------------------------------------------------------
# Sidebar: Document Management, Voice Assistant & Model Config
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎙️ Voice Assistant Settings")
    auto_speak = st.toggle("⚡ Auto-Speak Responses Loudly", value=False, help="Automatically speaks new assistant answers through your speakers")
    voice_speed = st.select_slider("🗣️ Speech Speed", options=[-2, -1, 0, 1, 2], value=0, format_func=lambda x: {
        -2: "Slower", -1: "Slow", 0: "Normal", 1: "Fast", 2: "Faster"
    }[x])

    st.markdown("---")
    st.markdown("## 📚 Document Hub")
    st.caption("Upload documents to build your local RAG knowledge base.")

    upload_tab, sample_tab, raw_tab = st.tabs(["📁 Upload", "📄 Sample", "✍️ Notes"])

    with upload_tab:
        uploaded_files = st.file_uploader(
            "Upload Documents",
            type=["pdf", "txt", "md", "csv", "docx"],
            accept_multiple_files=True,
            help="Supported formats: PDF, TXT, Markdown, CSV, Word"
        )
        if st.button("🚀 Ingest Documents", use_container_width=True, type="primary"):
            if uploaded_files:
                prog = st.progress(0, text="Indexing files...")
                total_files = len(uploaded_files)
                new_chunks = 0
                for idx, uf in enumerate(uploaded_files):
                    suffix = os.path.splitext(uf.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uf.read())
                        tmp_path = tmp.name
                    try:
                        res = pipeline.ingest(tmp_path)
                        chunks_got = res.get("chunks_processed", 0)
                        new_chunks += chunks_got
                        st.session_state.indexed_docs.append({
                            "name": uf.name,
                            "type": suffix.lstrip(".").upper(),
                            "chunks": chunks_got
                        })
                    except Exception as e:
                        st.error(f"Error processing {uf.name}: {e}")
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    prog.progress((idx + 1) / total_files, text=f"Indexed {uf.name}")
                prog.empty()
                st.success(f"Indexed {new_chunks} chunks from {total_files} file(s)!")
            else:
                st.warning("Please select at least one document.")

    with sample_tab:
        st.markdown("Test RAG immediately with a pre-formatted research paper.")
        if st.button("⚡ Load Sample Paper", use_container_width=True):
            with st.spinner("Indexing sample paper..."):
                sample_path = os.path.join(PROJECT_ROOT, "data", "sample_rag_paper.pdf")
                if not os.path.exists(sample_path):
                    generate_sample_pdf(sample_path)
                try:
                    res = pipeline.ingest(sample_path)
                    st.session_state.indexed_docs.append({
                        "name": "sample_rag_paper.pdf",
                        "type": "PDF",
                        "chunks": res.get("chunks_processed", 0)
                    })
                    st.success(f"Sample PDF indexed with {res.get('chunks_processed', 0)} chunks!")
                except Exception as e:
                    st.error(f"Error: {e}")

    with raw_tab:
        raw_title = st.text_input("Title", value="Notes.txt")
        raw_text = st.text_area("Paste content", height=100)
        if st.button("📥 Index Raw Content", use_container_width=True):
            if raw_text.strip():
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
                    tmp.write(raw_text)
                    tmp_path = tmp.name
                try:
                    res = pipeline.ingest(tmp_path)
                    st.session_state.indexed_docs.append({
                        "name": raw_title,
                        "type": "TXT",
                        "chunks": res.get("chunks_processed", 0)
                    })
                    st.success(f"Indexed {res.get('chunks_processed', 0)} chunks!")
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

    st.markdown("---")
    st.markdown("## ⚙️ Model & Retrieval")
    model_type = st.selectbox(
        "LLM Backend",
        options=["fallback", "huggingface", "gemini", "openai"],
        format_func=lambda x: {
            "fallback": "Offline Extractive Synthesizer (Default)",
            "huggingface": "Hugging Face Transformers (Local)",
            "gemini": "Google Gemini API",
            "openai": "OpenAI GPT API"
        }.get(x, x)
    )

    if model_type == "gemini":
        g_key = st.text_input("Gemini API Key", type="password")
        if g_key:
            os.environ["GEMINI_API_KEY"] = g_key
    elif model_type == "openai":
        o_key = st.text_input("OpenAI API Key", type="password")
        if o_key:
            os.environ["OPENAI_API_KEY"] = o_key

    top_k = st.slider("Top K Retrieved Chunks", min_value=1, max_value=8, value=3)

    st.markdown("---")
    st.markdown("## 🧹 Controls")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": "Chat cleared. How can I help you today?", "sources": []}
            ]
            st.session_state.active_audio_idx = None
            st.rerun()
    with c2:
        if st.button("⚠️ Reset DB", use_container_width=True):
            pipeline.reset()
            st.session_state.indexed_docs = []
            st.session_state.messages = [
                {"role": "assistant", "content": "Knowledge base reset. Upload new documents to start!", "sources": []}
            ]
            st.session_state.active_audio_idx = None
            st.success("Vector store reset.")
            st.rerun()

# -----------------------------------------------------------------------------
# Main Header & Metrics
# -----------------------------------------------------------------------------
st.title("🤖 RAG Knowledge Base & Voice Assistant")
st.markdown(
    "Query your documents using semantic search powered by **ChromaDB** and **sentence-transformers/all-MiniLM-L6-v2**."
)

stats = pipeline.get_stats()
total_chunks_in_db = stats.get("total_chunks", 0)
doc_count = len(st.session_state.indexed_docs)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">📄 Documents Indexed</div>
        <div class="metric-value">{doc_count}</div>
    </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🧩 Total Vector Chunks</div>
        <div class="metric-value">{total_chunks_in_db}</div>
    </div>
    """, unsafe_allow_html=True)
with m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🧠 Embedding Model</div>
        <div class="metric-value" style="font-size:16px; padding-top:4px;">all-MiniLM-L6-v2</div>
    </div>
    """, unsafe_allow_html=True)
with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">⚙️ Generator Mode</div>
        <div class="metric-value" style="font-size:16px; padding-top:4px;">{model_type.upper()}</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Quick Prompt Pills
# -----------------------------------------------------------------------------
st.markdown("##### 💡 Suggested Questions")
p1, p2, p3, p4 = st.columns(4)
with p1:
    if st.button("📋 Summarize Document", use_container_width=True):
        st.session_state.pending_prompt = "Can you provide a summary of the main points in the document?"
with p2:
    if st.button("🌟 Key Benefits of RAG", use_container_width=True):
        st.session_state.pending_prompt = "What are the main benefits of Retrieval-Augmented Generation?"
with p3:
    if st.button("🔢 What are the Steps?", use_container_width=True):
        st.session_state.pending_prompt = "What are the steps of the RAG pipeline?"
with p4:
    if st.button("🛡️ How does it prevent hallucinations?", use_container_width=True):
        st.session_state.pending_prompt = "How does RAG reduce or prevent hallucinations?"

st.markdown("---")

# -----------------------------------------------------------------------------
# Chat Messages Feed
# -----------------------------------------------------------------------------
for idx, msg in enumerate(st.session_state.messages):
    role = msg["role"]
    content = msg["content"]
    sources = msg.get("sources", [])

    with st.chat_message(role, avatar="🤖" if role == "assistant" else "👤"):
        st.markdown(content)

        # Bottom-left action toolbar for assistant responses (ChatGPT style)
        if role == "assistant" and idx > 0:
            act_col1, act_col2, act_col3, _ = st.columns([1.6, 1.4, 2.6, 6])
            
            with act_col1:
                # Speaker button on the left end
                if st.button("🔊 Speak", key=f"btn_speak_{idx}", help="Play answer loud through speakers"):
                    st.session_state.active_audio_idx = idx

            with act_col2:
                if st.button("⏹️ Stop", key=f"btn_stop_{idx}", help="Stop audio playback"):
                    if st.session_state.active_audio_idx == idx:
                        st.session_state.active_audio_idx = None

            with act_col3:
                # Context chunks toggle
                if sources:
                    with st.popover(f"🔍 Sources ({len(sources)})"):
                        for s_idx, chunk in enumerate(sources, 1):
                            if isinstance(chunk, dict):
                                text = chunk.get("text", "")
                                score = chunk.get("score")
                                meta = chunk.get("metadata", {})
                                source_doc = meta.get("source", "Document")
                                page = meta.get("page", 1)
                                score_str = f"Distance: {score:.4f}" if score is not None else "Matched"
                            else:
                                text = str(chunk)
                                source_doc = "Document"
                                page = 1
                                score_str = "Matched"

                            st.markdown(f"""
                            <div class="source-box">
                                <div class="source-meta">📌 [Chunk {s_idx}] • {source_doc} • Page {page} • <span style="color:#61AFEF;">{score_str}</span></div>
                                {text}
                            </div>
                            """, unsafe_allow_html=True)

            # If user clicked Speak (or auto-speak was triggered for this message):
            if st.session_state.active_audio_idx == idx:
                with st.spinner("🔊 Generating loud voice output..."):
                    audio_bytes = generate_speech_audio(content, volume=100, rate=voice_speed)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/wav", autoplay=True)
                    else:
                        st.info("💡 Windows audio speech synthesized.")

# -----------------------------------------------------------------------------
# Voice Input Assistant Bar (Microphone on the Right Space)
# -----------------------------------------------------------------------------
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Right space voice recognition widget: spoken words appear immediately in the box
v_col_left, v_col_right = st.columns([7, 3])
with v_col_right:
    with st.expander("🎙️ **Voice Assistant (Speak Question)**", expanded=False):
        st.caption("Click below to dictate your question using your microphone.")
        
        # Self-contained Web Speech API component (does NOT touch window.parent)
        components.html(r"""
        <div style="font-family: sans-serif; text-align: center;">
            <button id="mic-btn" onclick="startDictation()" 
                style="background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); color: #FFFFFF; border: none; border-radius: 20px; padding: 8px 18px; font-size: 13px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
                <span id="mic-icon" style="font-size: 16px;">🎙️</span> 
                <span id="mic-text">Click & Speak</span>
            </button>
            <div id="live-text" style="margin-top: 10px; font-size: 13px; color: #60A5FA; font-style: italic; min-height: 24px; padding: 6px; background: #1E293B; border-radius: 8px; border: 1px dashed #3B82F6;">
                (Your spoken words will appear here in real time)
            </div>
        </div>

        <script>
        var SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        var rec = null;
        var active = false;

        if (SpeechRec) {
            rec = new SpeechRec();
            rec.continuous = false;
            rec.interimResults = true;
            rec.lang = 'en-US';

            rec.onstart = function() {
                active = true;
                document.getElementById('mic-icon').innerText = "🔴";
                document.getElementById('mic-text').innerText = "Listening...";
                document.getElementById('mic-btn').style.background = "linear-gradient(135deg, #DC2626 0%, #991B1B 100%)";
                document.getElementById('live-text').innerText = "Listening to your voice...";
            };

            rec.onresult = function(e) {
                var spoken = "";
                for (var i = e.resultIndex; i < e.results.length; ++i) {
                    spoken += e.results[i][0].transcript;
                }
                // Spoken words appear in the live box dynamically as user speaks!
                document.getElementById('live-text').innerText = '🎤 "' + spoken + '"';
                
                // Copy to clipboard for instant pasting
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(spoken);
                }
            };

            rec.onerror = function(e) {
                document.getElementById('live-text').innerText = "Mic error: " + e.error;
                resetMic();
            };

            rec.onend = function() {
                resetMic();
            };
        }

        function resetMic() {
            active = false;
            document.getElementById('mic-icon').innerText = "🎙️";
            document.getElementById('mic-text').innerText = "Click & Speak";
            document.getElementById('mic-btn').style.background = "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)";
        }

        function startDictation() {
            if (!rec) {
                alert("Microphone recognition is not supported in this browser. Please use Chrome or Edge.");
                return;
            }
            if (active) {
                rec.stop();
            } else {
                rec.start();
            }
        }
        </script>
        """, height=105)

# -----------------------------------------------------------------------------
# Chat Input & Assistant Response Generation
# -----------------------------------------------------------------------------
user_query = st.chat_input("Ask any question about your documents...")

query_to_run = user_query or st.session_state.pending_prompt
st.session_state.pending_prompt = None

if query_to_run:
    # Append user question
    st.session_state.messages.append({"role": "user", "content": query_to_run, "sources": []})
    with st.chat_message("user", avatar="👤"):
        st.markdown(query_to_run)

    # Generate assistant answer
    with st.chat_message("assistant", avatar="🤖"):
        if total_chunks_in_db == 0:
            bot_reply = (
                "⚠️ **No Documents Indexed Yet!**\n\n"
                "🔹 Please upload a PDF or text document in the sidebar.\n"
                "🔹 Or click **'⚡ Load Sample Paper'** to test the pipeline with research content."
            )
            st.warning(bot_reply)
            st.session_state.messages.append({"role": "assistant", "content": bot_reply, "sources": []})
        else:
            with st.spinner("Searching documents & generating answer..."):
                try:
                    result = pipeline.query(query=query_to_run, top_k=top_k, model_type=model_type)
                    bot_reply = result.get("response", "No response generated.")
                    retrieved_chunks = result.get("context_chunks", [])

                    # Stream text simulation for conversational effect
                    message_placeholder = st.empty()
                    accumulated = ""
                    tokens = bot_reply.split(" ")
                    for token in tokens:
                        accumulated += token + " "
                        message_placeholder.markdown(accumulated + "▌")
                        time.sleep(0.015)
                    message_placeholder.markdown(bot_reply)

                    # New message index
                    new_idx = len(st.session_state.messages)
                    
                    # If auto-speak is enabled, trigger voice immediately
                    if auto_speak:
                        st.session_state.active_audio_idx = new_idx
                        with st.spinner("🔊 Speaking answer out loud..."):
                            audio_bytes = generate_speech_audio(bot_reply, volume=100, rate=voice_speed)
                            if audio_bytes:
                                st.audio(audio_bytes, format="audio/wav", autoplay=True)

                    # Save to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": bot_reply,
                        "sources": retrieved_chunks
                    })

                except Exception as e:
                    err_msg = f"❌ Error while generating answer: {e}"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg, "sources": []})

# -----------------------------------------------------------------------------
# Bottom Utilities: Export Conversation
# -----------------------------------------------------------------------------
if len(st.session_state.messages) > 1:
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    col_dl1, col_dl2 = st.columns([8, 2])
    with col_dl2:
        transcript_lines = ["# RAG AI Voice & Chat Transcript\n"]
        for m in st.session_state.messages:
            speaker = "AI Voice Assistant" if m["role"] == "assistant" else "User"
            transcript_lines.append(f"### {speaker}:\n{m['content']}\n")
        transcript = "\n".join(transcript_lines)
        
        st.download_button(
            label="💾 Export Chat as Markdown",
            data=transcript,
            file_name="rag_chat_transcript.md",
            mime="text/markdown",
            use_container_width=True
        )
