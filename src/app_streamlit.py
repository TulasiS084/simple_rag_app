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
    from src.rag_pipeline.voice import text_to_speech_base64, clean_text_for_speech
except ImportError:
    from rag_pipeline.pipeline import RAGPipeline
    from rag_pipeline.config import RAGConfig
    from create_sample_pdf import generate_sample_pdf
    from rag_pipeline.voice import text_to_speech_base64, clean_text_for_speech

# -----------------------------------------------------------------------------
# Streamlit Page Configuration & Modern Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="RAG AI Voice & Chatbot Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ChatGPT-like action bar and voice elements
st.markdown("""
<style>
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #1E222A 0%, #282C34 100%);
        border: 1px solid #3E4451;
        border-radius: 12px;
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
    /* Action toolbar buttons below assistant message (ChatGPT style) */
    .chat-action-btn {
        background: transparent;
        border: none;
        color: #8A919E;
        font-size: 16px;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 6px;
        transition: all 0.2s ease;
    }
    .chat-action-btn:hover {
        background: #2C313A;
        color: #61AFEF;
    }
    /* Input Container Styling */
    div[data-testid="stChatInput"] {
        border-radius: 24px;
        border: 1px solid #4B5263;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Global JavaScript Engine for Loud Voice Synthesis & Real-Time Voice Input
# -----------------------------------------------------------------------------
# We inject this into the top-level window so that speech synthesis runs in the main parent context
components.html("""
<script>
(function() {
    // Top level window reference
    const pWindow = window.parent || window;

    // Attach loud speaker function globally to parent window
    pWindow.playLoudSpeech = function(rawText, rate, pitch) {
        try {
            const synth = pWindow.speechSynthesis || window.speechSynthesis;
            if (!synth) {
                alert("Speech synthesis is not supported on this browser.");
                return;
            }

            synth.cancel(); // Stop any active speech
            if (synth.paused) {
                synth.resume();
            }

            // Clean text: strip markdown symbols and emojis
            let clean = rawText.replace(/[*#_>`\[\]]/g, ' ')
                               .replace(/https?:\/\/\S+/g, '')
                               .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
                               .replace(/\s+/g, ' ')
                               .trim();

            if (!clean) return;

            const utterance = new SpeechSynthesisUtterance(clean);
            utterance.volume = 1.0; // 100% MAXIMUM LOUD VOLUME
            utterance.rate = rate || 1.0;
            utterance.pitch = pitch || 1.0;

            // Pick loud, clear, natural English voice
            function setVoice() {
                const voices = synth.getVoices();
                if (voices && voices.length > 0) {
                    let best = voices.find(v => v.lang.startsWith('en') && (
                        v.name.includes('Natural') || 
                        v.name.includes('Google') || 
                        v.name.includes('David') || 
                        v.name.includes('Zira') || 
                        v.name.includes('Samantha') || 
                        v.name.includes('Microsoft')
                    )) || voices.find(v => v.lang.startsWith('en')) || voices[0];
                    if (best) utterance.voice = best;
                }
            }

            setVoice();
            if (synth.onvoiceschanged !== undefined) {
                synth.onvoiceschanged = setVoice;
            }

            // Chrome keep-alive hack: periodically resume to prevent cutting off on long texts
            const interval = setInterval(function() {
                if (!synth.speaking) {
                    clearInterval(interval);
                } else {
                    synth.resume();
                }
            }, 1000);

            synth.speak(utterance);
        } catch(e) {
            console.error("Speech synthesis error:", e);
        }
    };

    pWindow.stopLoudSpeech = function() {
        try {
            const synth = pWindow.speechSynthesis || window.speechSynthesis;
            if (synth) synth.cancel();
        } catch(e) {}
    };

    pWindow.copyAnswerText = function(text) {
        try {
            navigator.clipboard.writeText(text);
            alert("📋 Answer copied to clipboard!");
        } catch(e) {}
    };
})();
</script>
""", height=0)

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
                "- 📁 Upload documents in the sidebar, or click **'⚡ Load Sample Paper'** to start.\n"
                "- 🎙️ Click the **microphone icon** to speak your questions out loud.\n"
                "- 🔊 Click the **speaker button (left end of response)** to hear answers spoken loud and clear!"
            ),
            "sources": []
        }
    ]

if "indexed_docs" not in st.session_state:
    st.session_state.indexed_docs = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# -----------------------------------------------------------------------------
# Sidebar: Document Management, Voice Settings & Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎙️ Voice Assistant Settings")
    auto_speak = st.toggle("⚡ Auto-Speak Responses", value=False, help="Automatically speak assistant responses loud upon generation")
    speech_rate = st.slider("🗣️ Speech Speed", min_value=0.8, max_value=1.3, value=1.0, step=0.05)
    speech_pitch = st.slider("🎵 Voice Pitch", min_value=0.8, max_value=1.2, value=1.0, step=0.05)

    st.markdown("---")
    st.markdown("## 📚 Document Hub")
    st.caption("Upload documents to build your local RAG knowledge base.")

    upload_tab, sample_tab, raw_tab = st.tabs(["📁 Upload", "📄 Sample", "✍️ Notes"])

    with upload_tab:
        uploaded_files = st.file_uploader(
            "Upload Documents",
            type=["pdf", "txt", "md", "csv", "docx"],
            accept_multiple_files=True,
            help="Supported: PDF, Text, Markdown, CSV, Word"
        )
        if st.button("🚀 Ingest Uploaded Documents", use_container_width=True, type="primary"):
            if uploaded_files:
                progress_bar = st.progress(0, text="Vectorizing documents...")
                total_files = len(uploaded_files)
                new_chunks = 0
                
                for idx, uf in enumerate(uploaded_files):
                    suffix = os.path.splitext(uf.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uf.read())
                        tmp_path = tmp.name

                    try:
                        res = pipeline.ingest(tmp_path)
                        processed_chunks = res.get("chunks_processed", 0)
                        new_chunks += processed_chunks
                        st.session_state.indexed_docs.append({
                            "name": uf.name,
                            "type": suffix.lstrip(".").upper(),
                            "chunks": processed_chunks
                        })
                    except Exception as e:
                        st.error(f"Error reading {uf.name}: {e}")
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)

                    progress_bar.progress((idx + 1) / total_files, text=f"Indexed {uf.name}")

                time.sleep(0.3)
                progress_bar.empty()
                st.success(f"Vectorized {new_chunks} chunks from {total_files} document(s)!")
            else:
                st.warning("Please select at least one document to upload.")

    with sample_tab:
        st.markdown("Load pre-built AI research document for immediate testing.")
        if st.button("⚡ Load Sample RAG Paper", use_container_width=True):
            with st.spinner("Generating and vectorizing sample document..."):
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
                    st.success(f"Sample PDF loaded with {res.get('chunks_processed', 0)} chunks!")
                except Exception as e:
                    st.error(f"Failed to load sample: {e}")

    with raw_tab:
        raw_title = st.text_input("Note Title", value="Notes.txt")
        raw_content = st.text_area("Paste raw text or notes", height=110)
        if st.button("📥 Index Text", use_container_width=True):
            if raw_content.strip():
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
                    tmp.write(raw_content)
                    tmp_path = tmp.name
                try:
                    res = pipeline.ingest(tmp_path)
                    st.session_state.indexed_docs.append({
                        "name": raw_title,
                        "type": "TXT",
                        "chunks": res.get("chunks_processed", 0)
                    })
                    st.success(f"Indexed {res.get('chunks_processed', 0)} chunks from notes!")
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

    st.markdown("---")
    st.markdown("## ⚙️ Model Settings")
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
        gemini_key = st.text_input("Gemini API Key", type="password")
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key

    elif model_type == "openai":
        openai_key = st.text_input("OpenAI API Key", type="password")
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key

    top_k = st.slider("Top K Retrieved Chunks", min_value=1, max_value=8, value=3)

    st.markdown("---")
    st.markdown("## 🧹 Controls")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": "Chat cleared. How can I help you today?", "sources": []}
            ]
            st.rerun()
    with c2:
        if st.button("⚠️ Reset DB", use_container_width=True):
            pipeline.reset()
            st.session_state.indexed_docs = []
            st.session_state.messages = [
                {"role": "assistant", "content": "Knowledge base reset. Upload new documents to start!", "sources": []}
            ]
            st.success("Vector store reset.")
            st.rerun()

# -----------------------------------------------------------------------------
# Main Dashboard Header & Metrics
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
# Quick Prompt Suggestion Pills
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
# Chatbot Message Feed (with ChatGPT-Style Left-End Speaker Toolbar)
# -----------------------------------------------------------------------------
def render_chatgpt_action_toolbar(content: str, msg_idx: int, sources: List[Any], auto_play: bool = False):
    """
    Renders ChatGPT-style action buttons aligned at the LEFT end of the assistant chat bubble:
    [ 🔊 Read Aloud ] [ ⏹️ Stop ] [ 📋 Copy ]
    """
    safe_text = json.dumps(content)
    audio_b64 = text_to_speech_base64(content)  # Generates real MP3 data URI if gTTS is present
    
    html_code = f"""
    <div style="margin-top: 10px; display: flex; align-items: center; justify-content: flex-start; gap: 8px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <button id="spk-{msg_idx}" onclick="handleSpeak_{msg_idx}()" 
            title="Read aloud (loud voice)"
            style="background: #282C34; color: #61AFEF; border: 1px solid #3E4451; border-radius: 6px; padding: 4px 12px; font-size: 13px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: all 0.2s;">
            <span style="font-size: 15px;">🔊</span> <b>Speak</b>
        </button>

        <button id="stp-{msg_idx}" onclick="handleStop_{msg_idx}()" 
            title="Stop speaking"
            style="background: #282C34; color: #E06C75; border: 1px solid #3E4451; border-radius: 6px; padding: 4px 10px; font-size: 13px; cursor: pointer; display: inline-flex; align-items: center; gap: 5px; transition: all 0.2s;">
            <span>⏹️</span> <b>Stop</b>
        </button>

        <button onclick="handleCopy_{msg_idx}()" 
            title="Copy response to clipboard"
            style="background: #282C34; color: #ABB2BF; border: 1px solid #3E4451; border-radius: 6px; padding: 4px 10px; font-size: 13px; cursor: pointer; display: inline-flex; align-items: center; gap: 5px; transition: all 0.2s;">
            <span>📋</span> <b>Copy</b>
        </button>

        <span id="stat-{msg_idx}" style="font-size: 12px; color: #98C379; margin-left: 6px;"></span>

        {"<audio id='aud-" + str(msg_idx) + "' src='" + audio_b64 + "' style='display:none;'></audio>" if audio_b64 else ""}
    </div>

    <script>
    var msgText_{msg_idx} = {safe_text};

    function handleSpeak_{msg_idx}() {{
        var pWindow = window.parent || window;
        var audioElem = document.getElementById('aud-{msg_idx}');
        var stat = document.getElementById('stat-{msg_idx}');
        var btn = document.getElementById('spk-{msg_idx}');

        stat.innerText = "🔊 Speaking loud...";
        btn.style.background = "#1D4ED8";
        btn.style.color = "#FFFFFF";

        // 1. Try real audio playback if gTTS generated MP3
        if (audioElem) {{
            audioElem.currentTime = 0;
            audioElem.volume = 1.0;
            audioElem.play().then(function() {{
                audioElem.onended = function() {{
                    stat.innerText = "";
                    btn.style.background = "#282C34";
                    btn.style.color = "#61AFEF";
                }};
                return;
            }}).catch(function(err) {{
                // Fallback to Web Speech API
                callWebSpeech_{msg_idx}();
            }});
        }} else {{
            // 2. Call Web Speech API directly in parent window
            callWebSpeech_{msg_idx}();
        }}
    }}

    function callWebSpeech_{msg_idx}() {{
        var pWindow = window.parent || window;
        var stat = document.getElementById('stat-{msg_idx}');
        var btn = document.getElementById('spk-{msg_idx}');

        if (pWindow.playLoudSpeech) {{
            pWindow.playLoudSpeech(msgText_{msg_idx}, {speech_rate}, {speech_pitch});
        }} else {{
            // Direct synthesis fallback
            var synth = window.speechSynthesis;
            if (synth) {{
                synth.cancel();
                synth.resume();
                var clean = msgText_{msg_idx}.replace(/[*#_>`\\[\\]]/g, ' ').replace(/https?:\\/\\/\\S+/g, '').replace(/\\s+/g, ' ');
                var u = new SpeechSynthesisUtterance(clean);
                u.volume = 1.0;
                u.rate = {speech_rate};
                u.pitch = {speech_pitch};
                synth.speak(u);
            }}
        }}

        setTimeout(function() {{
            stat.innerText = "";
            btn.style.background = "#282C34";
            btn.style.color = "#61AFEF";
        }}, 8000);
    }}

    function handleStop_{msg_idx}() {{
        var pWindow = window.parent || window;
        if (pWindow.stopLoudSpeech) pWindow.stopLoudSpeech();
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        var audioElem = document.getElementById('aud-{msg_idx}');
        if (audioElem) {{
            audioElem.pause();
            audioElem.currentTime = 0;
        }}
        document.getElementById('stat-{msg_idx}').innerText = "";
        document.getElementById('spk-{msg_idx}').style.background = "#282C34";
        document.getElementById('spk-{msg_idx}').style.color = "#61AFEF";
    }}

    function handleCopy_{msg_idx}() {{
        var pWindow = window.parent || window;
        if (pWindow.copyAnswerText) {{
            pWindow.copyAnswerText(msgText_{msg_idx});
        }} else {{
            navigator.clipboard.writeText(msgText_{msg_idx});
            alert("Copied to clipboard!");
        }}
    }}

    if ({'true' if auto_play else 'false'}) {{
        setTimeout(handleSpeak_{msg_idx}, 500);
    }}
    </script>
    """
    components.html(html_code, height=44)


for idx, msg in enumerate(st.session_state.messages):
    role = msg["role"]
    content = msg["content"]
    sources = msg.get("sources", [])

    with st.chat_message(role, avatar="🤖" if role == "assistant" else "👤"):
        st.markdown(content)

        # For assistant responses: Render ChatGPT-style left action bar (Speaker, Stop, Copy)
        if role == "assistant" and idx > 0:
            render_chatgpt_action_toolbar(content, msg_idx=idx, sources=sources, auto_play=False)

            # Context Inspector Expander
            if sources:
                with st.expander(f"🔍 Inspect Retrieved Sources ({len(sources)} Chunks)"):
                    for i, chunk in enumerate(sources, 1):
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
                            <div class="source-meta">📌 [Chunk {i}] • {source_doc} • Page {page} • <span style="color:#61AFEF;">{score_str}</span></div>
                            {text}
                        </div>
                        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Real-Time Voice Input Bar (Right-Side Microphone with Live Spoken Words Display)
# -----------------------------------------------------------------------------
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Interactive Speech-to-Text Widget where spoken words appear dynamically in real time
voice_box_col1, voice_box_col2 = st.columns([7, 3])
with voice_box_col2:
    components.html("""
    <div style="display: flex; align-items: center; justify-content: flex-end; gap: 8px; font-family: sans-serif;">
        <button id="btn-mic" onclick="toggleMicrophone()" 
            style="background: linear-gradient(135deg, #2B6CB0 0%, #1A365D 100%); color: #EBF8FF; border: 1px solid #4299E1; border-radius: 20px; padding: 7px 18px; font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 7px; transition: all 0.25s ease; box-shadow: 0 2px 6px rgba(0,0,0,0.2);">
            <span id="mic-icon" style="font-size: 15px;">🎙️</span> 
            <span id="mic-label">Speak Question</span>
        </button>
    </div>
    <div id="live-speech-box" style="margin-top: 6px; font-size: 12px; color: #90CDF4; font-family: monospace; text-align: right; min-height: 16px; font-style: italic;"></div>

    <script>
    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    var recognizer = null;
    var listening = false;
    var pWindow = window.parent || window;

    if (SpeechRecognition) {
        recognizer = new SpeechRecognition();
        recognizer.continuous = false;
        recognizer.interimResults = true; // Real-time interim results as words are spoken
        recognizer.lang = 'en-US';

        recognizer.onstart = function() {
            listening = true;
            document.getElementById('mic-icon').innerText = "🔴";
            document.getElementById('mic-label').innerText = "Listening...";
            document.getElementById('btn-mic').style.background = "linear-gradient(135deg, #C53030 0%, #742A2A 100%)";
            document.getElementById('live-speech-box').innerText = "Speak now... words will appear below";
        };

        recognizer.onresult = function(event) {
            var interim = "";
            var finalTranscript = "";

            for (var i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interim += event.results[i][0].transcript;
                }
            }

            var currentWords = finalTranscript || interim;
            // Display words dynamically in the live speech box
            document.getElementById('live-speech-box').innerText = '🎤 "' + currentWords + '"';

            // Also dynamically inject spoken words into Streamlit's chat input textarea!
            try {
                var pDoc = pWindow.document;
                var chatInput = pDoc.querySelector('textarea[data-testid="stChatInputTextArea"]') || pDoc.querySelector('textarea');
                if (chatInput) {
                    chatInput.value = currentWords;
                    chatInput.dispatchEvent(new Event('input', { bubbles: true }));
                }
            } catch(e) {}
        };

        recognizer.onerror = function(e) {
            document.getElementById('live-speech-box').innerText = "Mic error: " + e.error;
            resetMicUI();
        };

        recognizer.onend = function() {
            resetMicUI();
            // Trigger question submission if final speech was captured
            var pDoc = pWindow.document;
            var chatInput = pDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
            var submitBtn = pDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
            if (chatInput && chatInput.value.trim() && submitBtn) {
                setTimeout(function() {
                    submitBtn.click();
                }, 300);
            }
        };
    }

    function resetMicUI() {
        listening = false;
        document.getElementById('mic-icon').innerText = "🎙️";
        document.getElementById('mic-label').innerText = "Speak Question";
        document.getElementById('btn-mic').style.background = "linear-gradient(135deg, #2B6CB0 0%, #1A365D 100%)";
    }

    function toggleMicrophone() {
        if (!recognizer) {
            alert("Microphone recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge.");
            return;
        }
        if (listening) {
            recognizer.stop();
        } else {
            recognizer.start();
        }
    }
    </script>
    """, height=50)

# -----------------------------------------------------------------------------
# Chat Input & Response Generation
# -----------------------------------------------------------------------------
user_query = st.chat_input("Ask any question about your documents (or use the microphone on the right)...")

query_to_run = user_query or st.session_state.pending_prompt
st.session_state.pending_prompt = None

if query_to_run:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": query_to_run, "sources": []})
    with st.chat_message("user", avatar="👤"):
        st.markdown(query_to_run)

    # Generate assistant response
    with st.chat_message("assistant", avatar="🤖"):
        if total_chunks_in_db == 0:
            bot_reply = (
                "⚠️ **No Documents Indexed Yet!**\n\n"
                "🔹 Please upload a PDF or document using the sidebar.\n"
                "🔹 Or click **'⚡ Load Sample Paper'** to test immediately with sample research content."
            )
            st.warning(bot_reply)
            st.session_state.messages.append({"role": "assistant", "content": bot_reply, "sources": []})
        else:
            with st.spinner("Searching knowledge base and generating answer..."):
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

                    # Render the left-aligned action bar with the loud speaker button
                    new_idx = len(st.session_state.messages)
                    render_chatgpt_action_toolbar(
                        bot_reply,
                        msg_idx=new_idx,
                        sources=retrieved_chunks,
                        auto_play=auto_speak
                    )

                    # Show sources expander
                    if retrieved_chunks:
                        with st.expander(f"🔍 Inspect Retrieved Sources ({len(retrieved_chunks)} Chunks)"):
                            for i, chunk in enumerate(retrieved_chunks, 1):
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
                                    <div class="source-meta">📌 [Chunk {i}] • {source_doc} • Page {page} • <span style="color:#61AFEF;">{score_str}</span></div>
                                    {text}
                                </div>
                                """, unsafe_allow_html=True)

                    # Save to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": bot_reply,
                        "sources": retrieved_chunks
                    })

                except Exception as e:
                    err_msg = f"❌ Error while answering question: {e}"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg, "sources": []})

# -----------------------------------------------------------------------------
# Bottom Utilities: Export Conversation
# -----------------------------------------------------------------------------
if len(st.session_state.messages) > 1:
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
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
