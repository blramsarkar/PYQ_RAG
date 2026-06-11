import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="PYQ Intelligence",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Minimal dark aesthetic ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Background */
.stApp { background-color: #0d0d0d; color: #e0e0e0; }
section[data-testid="stSidebar"] { background-color: #111111; border-right: 1px solid #222; }

/* Hide default header */
#MainMenu, header, footer { visibility: hidden; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background-color: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    color: #e0e0e0 !important;
    border-radius: 6px !important;
}

/* Buttons */
.stButton > button {
    background-color: #1a1a1a;
    border: 1px solid #333;
    color: #e0e0e0;
    border-radius: 6px;
    font-size: 13px;
    padding: 8px 18px;
    transition: all 0.15s;
}
.stButton > button:hover {
    background-color: #252525;
    border-color: #555;
    color: #fff;
}

/* Primary accent button */
.stButton > button[kind="primary"] {
    background-color: #4f46e5;
    border-color: #4f46e5;
    color: #fff;
}
.stButton > button[kind="primary"]:hover {
    background-color: #4338ca;
}

/* Cards */
.card {
    background: #141414;
    border: 1px solid #222;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 10px;
}
.card:hover { border-color: #333; }

.tag {
    display: inline-block;
    background: #1e1e1e;
    border: 1px solid #2d2d2d;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    color: #888;
    margin-right: 6px;
}
.tag-accent { border-color: #4f46e5; color: #818cf8; }
.tag-green  { border-color: #16a34a; color: #4ade80; }
.tag-amber  { border-color: #b45309; color: #fbbf24; }
.tag-red    { border-color: #b91c1c; color: #f87171; }

.section-title {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #555;
    margin-bottom: 16px;
    margin-top: 8px;
}

.stat-box {
    background: #141414;
    border: 1px solid #222;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}
.stat-num {
    font-size: 28px;
    font-weight: 600;
    color: #e0e0e0;
    font-family: 'JetBrains Mono', monospace;
}
.stat-label { font-size: 11px; color: #555; margin-top: 4px; }

/* File uploader */
[data-testid="stFileUploader"] {
    background: #141414;
    border: 1px dashed #2a2a2a;
    border-radius: 8px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid #222;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #555;
    font-size: 13px;
    padding: 10px 20px;
    border: none;
    border-bottom: 2px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: #e0e0e0 !important;
    border-bottom: 2px solid #4f46e5 !important;
    background: transparent !important;
}

/* Divider */
hr { border-color: #1e1e1e !important; }

/* Expander */
.streamlit-expanderHeader {
    background: #141414 !important;
    border: 1px solid #222 !important;
    border-radius: 6px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0d0d0d; }
::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### PYQ Intelligence")
    st.markdown("<div style='color:#555;font-size:12px;margin-bottom:24px'>Previous Year Questions · RAG</div>", unsafe_allow_html=True)

    groq_key = st.text_input(
        "Groq API Key",
        type="password",
        value=os.getenv("GROQ_API_KEY", ""),
        placeholder="gsk_...",
    )
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key

    st.markdown("---")
    st.markdown("<div class='section-title'>Upload PYQs</div>", unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Drop PDF exam papers",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files and groq_key:
        if st.button("Process PDFs", use_container_width=True):
            from utils.pdf_parser import extract_text_from_pdf, parse_pyq_with_llm
            from utils.vector_store import add_questions

            progress = st.progress(0)
            total = len(uploaded_files)
            added = 0

            for i, f in enumerate(uploaded_files):
                with st.spinner(f"Parsing {f.name}..."):
                    try:
                        text = extract_text_from_pdf(f)
                        parsed = parse_pyq_with_llm(text, groq_key)
                        n = add_questions(parsed, f.name)
                        added += n
                        st.success(f"✓ {f.name} → {n} questions")
                    except Exception as e:
                        st.error(f"✗ {f.name}: {e}")
                progress.progress((i + 1) / total)

            st.info(f"Total indexed: {added} questions")
    elif uploaded_files and not groq_key:
        st.warning("Enter your Groq API key first.")

    st.markdown("---")

    from utils.vector_store import get_total_count, reset_collection

    # ── Auto-reset on new browser session ────────────────────────────────
    if "session_initialized" not in st.session_state:
        st.session_state["session_initialized"] = True
        try:
            reset_collection()
        except Exception:
            pass

    # ── Manual reset button ───────────────────────────────────────────────
    if st.button("🗑 Reset All Data", use_container_width=True):
        try:
            reset_collection()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("All data cleared.")
            st.rerun()
        except Exception as e:
            st.error(f"Reset failed: {e}")

    try:
        count = get_total_count()
    except Exception:
        count = 0

    st.markdown(f"""
    <div class='stat-box'>
        <div class='stat-num'>{count}</div>
        <div class='stat-label'>questions indexed</div>
    </div>
    """, unsafe_allow_html=True)


# ── Main tabs ─────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["  Question Bank  ", "  Exam Predictor  ", "  Practice Mode  "])

# ─── TAB 1: Question Bank ────────────────────────────────────────────────────
with tab1:
    from utils.vector_store import query_questions, get_distinct_values

    st.markdown("<div class='section-title'>Question Bank</div>", unsafe_allow_html=True)

    col_q, col_f = st.columns([3, 1])

    with col_q:
        query = st.text_input("Search questions", placeholder="e.g. explain TCP three-way handshake", label_visibility="collapsed")

    with col_f:
        n_results = st.selectbox("Results", [10, 20, 30, 50], label_visibility="collapsed")

    # Filters
    fc1, fc2, fc3, fc4 = st.columns(4)

    try:
        subjects = ["All"] + get_distinct_values("subject")
        exam_types = ["All"] + get_distinct_values("exam_type")
        topics = ["All"] + get_distinct_values("topic")
        difficulties = ["All", "Easy", "Medium", "Hard"]
    except Exception:
        subjects = exam_types = topics = difficulties = ["All"]

    with fc1:
        subj_f = st.selectbox("Subject", subjects, label_visibility="collapsed")
    with fc2:
        exam_f = st.selectbox("Exam type", exam_types, label_visibility="collapsed")
    with fc3:
        topic_f = st.selectbox("Topic", topics, label_visibility="collapsed")
    with fc4:
        diff_f = st.selectbox("Difficulty", difficulties, label_visibility="collapsed")

    if query or (subj_f != "All") or (exam_f != "All") or (topic_f != "All") or (diff_f != "All"):
        search_q = query if query else "university exam question"
        try:
            results = query_questions(
                search_q,
                subject_filter=subj_f,
                exam_type_filter=exam_f,
                topic_filter=topic_f,
                difficulty_filter=diff_f,
                n_results=n_results,
            )
        except Exception as e:
            results = []
            st.error(f"Search error: {e}")

        if results:
            st.markdown(f"<div style='color:#555;font-size:12px;margin:12px 0'>{len(results)} results</div>", unsafe_allow_html=True)
            for r in results:
                m = r["meta"]
                diff = m.get("difficulty", "Medium")
                diff_class = {"Easy": "tag-green", "Hard": "tag-red"}.get(diff, "tag-amber")
                marks_str = f"<span class='tag'>{m.get('marks','')} marks</span>" if m.get("marks") else ""
                st.markdown(f"""
                <div class='card'>
                    <div style='font-size:13px;color:#ccc;line-height:1.6;margin-bottom:10px'>{r['question']}</div>
                    <div>
                        <span class='tag tag-accent'>{m.get('subject','')}</span>
                        <span class='tag'>{m.get('year','')}</span>
                        <span class='tag'>{m.get('exam_type','')}</span>
                        <span class='tag'>{m.get('topic','')}</span>
                        <span class='tag {diff_class}'>{diff}</span>
                        {marks_str}
                        <span style='float:right;font-size:11px;color:#333;font-family:JetBrains Mono'>Q{m.get('question_number','')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#444;padding:40px;text-align:center'>No questions found. Try broadening your filters.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#333;padding:60px;text-align:center;font-size:13px'>Enter a search query or select filters above.</div>", unsafe_allow_html=True)


# ─── TAB 2: Exam Predictor ───────────────────────────────────────────────────
with tab2:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from utils.vector_store import get_all_metadata, get_distinct_values

    st.markdown("<div class='section-title'>Exam Predictor</div>", unsafe_allow_html=True)

    try:
        all_data = get_all_metadata()
    except Exception:
        all_data = []

    if not all_data:
        st.markdown("<div style='color:#444;padding:60px;text-align:center;font-size:13px'>Upload and process PYQs first.</div>", unsafe_allow_html=True)
    else:
        df = pd.DataFrame([{**d["meta"], "question": d["question"]} for d in all_data])

        # Subject filter
        subj_list = ["All"] + sorted(df["subject"].unique().tolist())
        pred_subj = st.selectbox("Filter by subject", subj_list, key="pred_subj")

        if pred_subj != "All":
            df_f = df[df["subject"] == pred_subj]
        else:
            df_f = df

        # ── Topic frequency ──────────────────────────────────────────────────
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("<div class='section-title' style='margin-top:20px'>Topic Frequency</div>", unsafe_allow_html=True)
            topic_counts = df_f["topic"].value_counts().reset_index()
            topic_counts.columns = ["topic", "count"]

            fig = px.bar(
                topic_counts.head(15),
                x="count", y="topic",
                orientation="h",
                color="count",
                color_continuous_scale=[[0, "#1e1e2e"], [1, "#4f46e5"]],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#888",
                showlegend=False,
                coloraxis_showscale=False,
                yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
                xaxis=dict(showgrid=True, gridcolor="#1a1a1a"),
                margin=dict(l=0, r=0, t=0, b=0),
                height=340,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.markdown("<div class='section-title' style='margin-top:20px'>Year Distribution</div>", unsafe_allow_html=True)
            year_counts = df_f["year"].value_counts().reset_index()
            year_counts.columns = ["year", "count"]

            fig2 = px.bar(
                year_counts,
                x="year", y="count",
                color="count",
                color_continuous_scale=[[0, "#1e2e1e"], [1, "#16a34a"]],
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#888",
                showlegend=False,
                coloraxis_showscale=False,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#1a1a1a"),
                margin=dict(l=0, r=0, t=0, b=0),
                height=340,
            )
            st.plotly_chart(fig2, use_container_width=True)

        # ── Gap Analysis + Prediction ────────────────────────────────────────
        st.markdown("<div class='section-title' style='margin-top:8px'>Prediction — Gap Analysis</div>", unsafe_allow_html=True)

        years = sorted(df_f["year"].unique(), reverse=True)
        latest_year = years[0] if years else "N/A"

        topic_year = df_f.groupby("topic")["year"].agg(
            lambda x: sorted(x.unique(), reverse=True)[0]
        ).reset_index()
        topic_year.columns = ["topic", "last_seen"]
        topic_freq = df_f["topic"].value_counts().reset_index()
        topic_freq.columns = ["topic", "total_count"]

        gap_df = topic_year.merge(topic_freq, on="topic")
        gap_df = gap_df.sort_values("last_seen")  # oldest first = highest priority

        # Stars: topics not seen in last year get more stars
        def star_rating(row):
            if row["last_seen"] < latest_year:
                return "★★★★★"
            freq = row["total_count"]
            if freq >= 8:
                return "★★★★☆"
            elif freq >= 5:
                return "★★★☆☆"
            return "★★☆☆☆"

        gap_df["prediction"] = gap_df.apply(star_rating, axis=1)
        gap_df = gap_df.sort_values("prediction", ascending=False)

        for _, row in gap_df.head(10).iterrows():
            color = "#4ade80" if row["last_seen"] < latest_year else "#888"
            st.markdown(f"""
            <div class='card' style='display:flex;justify-content:space-between;align-items:center'>
                <div>
                    <span style='font-size:13px;color:#ccc'>{row['topic']}</span>
                    <span class='tag' style='margin-left:8px'>last: {row['last_seen']}</span>
                    <span class='tag'>×{row['total_count']}</span>
                </div>
                <span style='color:{color};font-size:14px;letter-spacing:2px'>{row['prediction']}</span>
            </div>
            """, unsafe_allow_html=True)


# ─── TAB 3: Practice Mode ────────────────────────────────────────────────────
with tab3:
    from utils.vector_store import get_distinct_values, query_questions
    import random

    st.markdown("<div class='section-title'>Practice Mode</div>", unsafe_allow_html=True)

    if not groq_key:
        st.warning("Enter your Groq API key in the sidebar.")
    else:
        try:
            p_subjects = ["Any"] + get_distinct_values("subject")
            p_exams = ["Any"] + get_distinct_values("exam_type")
        except Exception:
            p_subjects = p_exams = ["Any"]

        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            p_subj = st.selectbox("Subject", p_subjects, key="p_subj")
        with pc2:
            p_exam = st.selectbox("Exam type", p_exams, key="p_exam")
        with pc3:
            p_diff = st.selectbox("Difficulty", ["Any", "Easy", "Medium", "Hard"], key="p_diff")
        with pc4:
            p_n = st.selectbox("No. of questions", [5, 10, 15, 20], key="p_n")

        if st.button("Generate Practice Set", use_container_width=True):
            try:
                results = query_questions(
                    "university exam question",
                    subject_filter=p_subj if p_subj != "Any" else None,
                    exam_type_filter=p_exam if p_exam != "Any" else None,
                    difficulty_filter=p_diff if p_diff != "Any" else None,
                    n_results=50,
                )
                if results:
                    selected = random.sample(results, min(p_n, len(results)))
                    st.session_state["practice_set"] = selected
                    st.session_state["practice_answers"] = {}
                    st.session_state["practice_checked"] = False
                else:
                    st.warning("No questions found for these filters.")
            except Exception as e:
                st.error(f"Error: {e}")

        # ── Show practice set ────────────────────────────────────────────────
        if "practice_set" in st.session_state and st.session_state["practice_set"]:
            st.markdown("---")

            from groq import Groq
            client = Groq(api_key=groq_key)

            for i, r in enumerate(st.session_state["practice_set"]):
                m = r["meta"]
                diff = m.get("difficulty", "Medium")
                diff_class = {"Easy": "tag-green", "Hard": "tag-red"}.get(diff, "tag-amber")

                st.markdown(f"""
                <div class='card'>
                    <div style='font-size:11px;color:#555;margin-bottom:8px'>
                        Q{i+1} &nbsp;·&nbsp; <span class='tag {diff_class}'>{diff}</span>
                        <span class='tag'>{m.get('topic','')}</span>
                        <span class='tag'>{m.get('subject','')}</span>
                    </div>
                    <div style='font-size:14px;color:#ddd;line-height:1.6'>{r['question']}</div>
                </div>
                """, unsafe_allow_html=True)

                ans_key = f"ans_{i}"
                st.text_area(
                    "Your answer",
                    key=ans_key,
                    placeholder="Write your answer here...",
                    label_visibility="collapsed",
                    height=80,
                )

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Get AI Feedback", use_container_width=True):
                for i, r in enumerate(st.session_state["practice_set"]):
                    user_ans = st.session_state.get(f"ans_{i}", "").strip()
                    if not user_ans:
                        continue

                    with st.spinner(f"Evaluating Q{i+1}..."):
                        try:
                            resp = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[{
                                    "role": "user",
                                    "content": f"""Question: {r['question']}

Student Answer: {user_ans}

Give brief feedback (3-4 sentences): what's correct, what's missing, and a key point they should remember. Be concise and constructive."""
                                }],
                                max_tokens=300,
                                temperature=0.3,
                            )
                            feedback = resp.choices[0].message.content.strip()
                            st.markdown(f"""
                            <div class='card' style='border-color:#1a2a1a'>
                                <div style='font-size:11px;color:#4ade80;margin-bottom:6px'>Feedback · Q{i+1}</div>
                                <div style='font-size:13px;color:#aaa;line-height:1.6'>{feedback}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Q{i+1} feedback error: {e}")
