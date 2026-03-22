"""
Streamlit Dashboard App - Run via: streamlit run agent/dashboard_app.py
"""

import sys
import json
import sqlite3
import pandas as pd
from pathlib import Path

# Make sure project root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="Job Application Tracker",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Styles ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background: #0f1117;
        border: 1px solid #1e2130;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
    }
    .metric-value { font-size: 2.2rem; font-weight: 600; color: #7dd3fc; }
    .metric-label { font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
    .status-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 99px;
        font-size: 0.75rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# ── Data ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=5)
def load_data():
    db_path = Path("applications.db")
    if not db_path.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(str(db_path))
    df = pd.read_sql("SELECT * FROM applications ORDER BY created_at DESC", conn)
    conn.close()
    return df


STATUS_COLORS = {
    "applied":     ("#22c55e", "✅"),
    "interview":   ("#a855f7", "🎤"),
    "offer":       ("#f59e0b", "🎉"),
    "rejected":    ("#ef4444", "❌"),
    "dry_run":     ("#94a3b8", "🧪"),
    "failed":      ("#f97316", "⚠️"),
    "in_progress": ("#3b82f6", "⏳"),
    "pending":     ("#64748b", "📋"),
    "skipped":     ("#334155", "⏭️"),
}


def color_status(status: str) -> str:
    color, icon = STATUS_COLORS.get(status, ("#64748b", "•"))
    return f'<span class="status-badge" style="background:{color}22;color:{color}">{icon} {status}</span>'


def score_color(score):
    if score >= 85:
        return "🟢"
    elif score >= 70:
        return "🟡"
    else:
        return "🔴"


# ── Layout ───────────────────────────────────────────────────────────────────

st.title("💼 Job Application Tracker")

df = load_data()

if df.empty:
    st.info("No applications yet. Run `python main.py auto` to start applying!")
    st.stop()

# ── KPI Metrics ──────────────────────────────────────────────────────────────

total       = len(df)
applied     = len(df[df.status.isin(["applied", "interview", "offer"])])
interviews  = len(df[df.status == "interview"])
offers      = len(df[df.status == "offer"])
response_rate = f"{(interviews / max(applied, 1) * 100):.0f}%"

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{total}</div><div class="metric-label">Total</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#22c55e">{applied}</div><div class="metric-label">Applied</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#a855f7">{interviews}</div><div class="metric-label">Interviews</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#f59e0b">{offers}</div><div class="metric-label">Offers</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#7dd3fc">{response_rate}</div><div class="metric-label">Response Rate</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Sidebar Filters ───────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Filters")
    status_filter = st.multiselect(
        "Status", options=df.status.unique().tolist(), default=df.status.unique().tolist()
    )
    score_min = st.slider("Min Match Score", 0, 100, 0)
    search_text = st.text_input("Search company/title")

    st.markdown("---")
    st.subheader("Update Status")
    selected_url = st.selectbox("Job URL", options=df.job_url.tolist(), format_func=lambda x: x[:50])
    new_status = st.selectbox("New Status", options=list(STATUS_COLORS.keys()))
    notes = st.text_area("Notes")
    if st.button("Update", use_container_width=True):
        conn = sqlite3.connect("applications.db")
        conn.execute("UPDATE applications SET status=?, notes=? WHERE job_url=?", (new_status, notes, selected_url))
        conn.commit()
        conn.close()
        st.success("Updated!")
        st.cache_data.clear()
        st.rerun()

# ── Filtered Table ────────────────────────────────────────────────────────────

filtered = df[df.status.isin(status_filter)]
if score_min > 0:
    filtered = filtered[filtered.match_score >= score_min]
if search_text:
    mask = (
        filtered.company.str.contains(search_text, case=False, na=False) |
        filtered.job_title.str.contains(search_text, case=False, na=False)
    )
    filtered = filtered[mask]

st.subheader(f"Applications ({len(filtered)})")

# Build display table
rows_html = ""
for _, row in filtered.iterrows():
    score_icon = score_color(row.match_score or 0)
    status_html = color_status(row.status)
    link = f'<a href="{row.job_url}" target="_blank" style="color:#7dd3fc">{row.job_title}</a>'
    rows_html += f"""
    <tr>
        <td>{link}</td>
        <td>{row.company}</td>
        <td>{row.location or '—'}</td>
        <td>{score_icon} {row.match_score or '—'}%</td>
        <td>{status_html}</td>
        <td style="color:#64748b;font-size:0.8rem">{str(row.applied_at or '')[:10]}</td>
        <td style="color:#64748b;font-size:0.8rem">{row.notes or ''}</td>
    </tr>
    """

table_html = f"""
<table style="width:100%;border-collapse:collapse;font-size:0.9rem">
  <thead>
    <tr style="border-bottom:1px solid #1e2130;color:#64748b;text-transform:uppercase;font-size:0.75rem">
      <th style="text-align:left;padding:8px 6px">Title</th>
      <th style="text-align:left;padding:8px 6px">Company</th>
      <th style="text-align:left;padding:8px 6px">Location</th>
      <th style="text-align:left;padding:8px 6px">Score</th>
      <th style="text-align:left;padding:8px 6px">Status</th>
      <th style="text-align:left;padding:8px 6px">Date</th>
      <th style="text-align:left;padding:8px 6px">Notes</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>
"""

st.markdown(table_html, unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
c1, c2 = st.columns(2)

with c1:
    st.subheader("Applications by Status")
    status_counts = df.status.value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    st.bar_chart(status_counts.set_index("Status"))

with c2:
    st.subheader("Match Score Distribution")
    score_data = df[df.match_score > 0].match_score
    if not score_data.empty:
        st.bar_chart(score_data.value_counts().sort_index())
    else:
        st.info("No score data yet.")

# ── Top Companies ─────────────────────────────────────────────────────────────

st.subheader("Companies Applied To")
company_counts = df.company.value_counts().head(15).reset_index()
company_counts.columns = ["Company", "Applications"]
st.dataframe(company_counts, use_container_width=True, hide_index=True)
