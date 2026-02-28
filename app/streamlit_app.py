import asyncio
import streamlit as st
from pathlib import Path

from core.logging_config import configure_logging
from database.engine import init_db
from auth.middleware import require_auth, login_user, logout_user
from auth.session_store import save_session, load_session, delete_session
from services.auth_service import authenticate_user
from services.analysis_service import (
    process_analysis,
    get_user_analyses,
    delete_analysis_by_id,
    get_candidates_by_analysis,
)
from services.user_service import (
    change_password,
    create_user,
    list_users,
    delete_user,
)

from core.config import config

configure_logging()

st.set_page_config(
    page_title="NeuralCV",
    layout="wide",
)

# ---------------- Async Helper ----------------
def run_async(coro):
    """Robust async runner for Streamlit's threaded environment."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    else:
        return loop.run_until_complete(coro)


# ---------------- Init DB ----------------
if "db_initialized" not in st.session_state:
    run_async(init_db())
    st.session_state.db_initialized = True


# -------- SESSION RECOVERY (file-based, runs at top level) --------
if not st.session_state.get("authenticated"):
    sid = st.query_params.get("sid")
    if sid:
        data = load_session(sid)
        if data:
            st.session_state["jwt_access"]  = data["access"]
            st.session_state["jwt_refresh"] = data["refresh"]
            st.session_state["user"]        = data["user"]
            st.session_state["authenticated"] = True
            st.session_state["session_id"]  = sid


# ============================================================
# LOGIN PAGE (NOT WIDE)
# ============================================================

async def show_login():

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("NeuralCV Login")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                user, error = await authenticate_user(username, password)

                if user:
                    access, refresh = login_user(user)

                    # Persist session to file & URL
                    sid = save_session(user, access, refresh)
                    st.session_state["session_id"] = sid
                    st.query_params["sid"] = sid

                    if user.get("must_change_password"):
                        st.session_state.page = "change_password"

                    st.rerun()
                else:
                    st.error(error)


# ============================================================
# NAVIGATION
# ============================================================

def sidebar_navigation(user):

    pages = ["Dashboard", "New Analysis", "Change Password"]

    if user["is_admin"]:
        pages.append("Admin Panel")
        pages.append("Debug Dashboard")
        pages.append("DB Viewer")

    choice = st.sidebar.radio("Navigation", pages)

    st.sidebar.divider()
    st.sidebar.markdown(
        f"👤 **{user['username']}**  \n"
        f"{'Privileges → Admin' if user['is_admin'] else 'Privileges → User'}"
    )

    if st.sidebar.button("Logout"):
        sid = st.session_state.get("session_id")
        if sid:
            delete_session(sid)
        logout_user()
        st.query_params.clear()
        st.rerun()

    return choice


# ============================================================
# DASHBOARD
# ============================================================

async def show_dashboard(user):
    import sqlite3
    import pandas as pd

    st.markdown(f"""
    ## 😎 Welcome back, **{user['username']}**!
    """)

    analyses = await get_user_analyses(user["user_id"])

    try:
        conn = sqlite3.connect("neuralcv.db")
        total_analyses = len(analyses) if analyses else 0
        total_candidates = pd.read_sql(
            "SELECT COUNT(*) as c FROM candidate", conn
        ).iloc[0]['c'] if total_analyses > 0 else 0
        completed = sum(1 for a in analyses if a['status'] == 'completed') if analyses else 0
        conn.close()
    except Exception:
        total_candidates = 0
        completed = 0
        total_analyses = 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📁 Total Analyses", total_analyses)
    c2.metric("✅ Completed", completed)
    c3.metric("⏳ Pending", total_analyses - completed)
    c4.metric("👥 Candidates Processed", total_candidates)

    st.divider()

    if not analyses:
        st.info("🚀 No analyses yet. Click **New Analysis** in the sidebar to get started!")
        return

    st.subheader("📋 Your Analyses")

    for analysis in analyses:
        status = analysis.get("status", "unknown")

        # Status styling
        status_icons = {
            "completed": "🟢",
            "stage1_completed": "🟡",
            "pending": "🔵",
            "failed": "🔴",
        }
        icon = status_icons.get(status, "⚪")

        with st.container(border=True):
            row1, row2, row3 = st.columns([5, 1, 1])

            with row1:
                st.markdown(f"### {analysis['analysis_name']}")
                st.caption(f"{icon} **{status.upper().replace('_', ' ')}**  •  Created: {analysis.get('created_at', 'N/A')}")

            with row2:
                if st.button("📊 View", key=f"view_{analysis['analysis_id']}", use_container_width=True):
                    st.session_state.selected_analysis = analysis["analysis_id"]
                    st.rerun()

            with row3:
                if st.button("🗑️ Delete", key=f"del_{analysis['analysis_id']}", use_container_width=True):
                    await delete_analysis_by_id(analysis["analysis_id"])
                    st.rerun()



async def show_analysis_results():

    st.title("📈 Analysis Results")

    analysis_id = st.session_state.get("selected_analysis")

    if not analysis_id:
        st.warning("No analysis selected.")
        return

    candidates = await get_candidates_by_analysis(analysis_id)

    if not candidates:
        st.warning("No candidates found.")
        if st.button("⬅ Back"):
            st.session_state.selected_analysis = None
            st.rerun()
        return

    import pandas as pd

    # --- Data Prep ---
    all_rows = []
    for c in candidates:
        b = c["breakdown"]
        o = b.get("overall_score", 0) * 100
        all_rows.append({
            "name": c["name"], "summary": c.get("summary", ""),
            "skill": b.get("skill_match", 0), "exp": b.get("exp_match", 0),
            "edu": b.get("education_match", 0), "score": o,
            "rank": b.get("rank"), "justification": b.get("justification", ""),
            "filename": c.get("filename", "")
        })

    # --- Threshold Filter ---
    THRESHOLD = 80.0
    qualified = [r for r in all_rows if r["score"] >= THRESHOLD]
    hidden = len(all_rows) - len(qualified)

    c1, c2, c3 = st.columns([1, 1, 1])
    c1.metric("Total Processed", len(all_rows))
    c2.metric("Qualified (≥80%)", len(qualified))
    
    export_df = pd.DataFrame([{
        "Name": r["name"],
        "Skill Match (%)": f"{r['skill']*100:.1f}",
        "Experience Match (%)": f"{r['exp']*100:.1f}",
        "Education Match (%)": f"{r['edu']*100:.1f}",
        "Overall Score (%)": f"{r['score']:.1f}",
        "Rank": r["rank"] if r["rank"] else "N/A",
        "Justification": r["justification"] if r["justification"] else "Stage 2 not performed",
        "File": r["filename"]
    } for r in sorted(all_rows, key=lambda x: x["score"], reverse=True)])
    
    csv = export_df.to_csv(index=False).encode('utf-8')
    with c3:
        st.write("")
        st.download_button(
            label="📥 Download Results (CSV)",
            data=csv,
            file_name=f"analysis_export_{analysis_id[:8]}.csv",
            mime="text/csv",
            use_container_width=True
        )

    if not qualified:
        st.warning("No candidates scored above 80%.")
        if st.button("⬅ Back"):
            st.session_state.selected_analysis = None
            st.rerun()
        return

    st.divider()

    # ═══════ TOP RANKED (Stage 2) ═══════
    ranked = sorted([r for r in qualified if r["rank"]], key=lambda x: x["rank"])

    if ranked:
        st.subheader("🏆 Top Ranked Candidates")
        for r in ranked:
            with st.container(border=True):
                left, right = st.columns([3, 1])
                left.markdown(f"**#{r['rank']}  {r['name']}**")
                right.markdown(f"**{r['score']:.0f}%** overall")
                if r["justification"]:
                    st.caption(r["justification"])
    else:
        st.info("Stage 2 ranking not complete yet.")

    st.divider()

    # ═══════ ALL QUALIFIED — Sortable Table ═══════
    st.subheader("📊 All Qualified Candidates")

    df = pd.DataFrame([{
        "Name": r["name"],
        "Skills": f"{r['skill']*100:.0f}%",
        "Experience": f"{r['exp']*100:.0f}%",
        "Education": f"{r['edu']*100:.0f}%",
        "Score": f"{r['score']:.0f}%",
        "File": r["filename"]
    } for r in sorted(qualified, key=lambda x: x["score"], reverse=True)])

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    # ═══════ DETAILED PROFILES ═══════
    st.subheader("🔍 Profiles")
    for r in sorted(qualified, key=lambda x: x["score"], reverse=True):
        label = f"#{r['rank']} " if r["rank"] else ""
        with st.expander(f"{label}{r['name']}  —  {r['score']:.0f}%"):
            p1, p2 = st.columns([1, 2])
            with p1:
                st.progress(r["skill"], text=f"Skills {r['skill']*100:.0f}%")
                st.progress(r["exp"], text=f"Experience {r['exp']*100:.0f}%")
                st.progress(r["edu"], text=f"Education {r['edu']*100:.0f}%")
            with p2:
                if r["justification"]:
                    st.success(f"**LLM Analysis:** {r['justification']}")
                if r["summary"]:
                    st.caption(r["summary"])

    st.divider()
    if st.button("⬅ Back to Dashboard", use_container_width=True):
        st.session_state.selected_analysis = None
        st.rerun()


# ============================================================
# NEW ANALYSIS
# ============================================================

async def show_new_analysis(user):

    st.title("🚀 New Analysis")

    col1, col2 = st.columns(2)
    analysis_name = col1.text_input("Analysis Name", help="Give this run a meaningful name")
    model_choice = col2.selectbox(
        "Model", options=config.available_models,
        index=config.available_models.index(config.default_model)
            if config.default_model in config.available_models else 0
    )

    st.divider()

    # --- JD ---
    jd_tab1, jd_tab2 = st.tabs(["📄 Upload JD", "✏️ Paste JD"])
    jd_file = jd_tab1.file_uploader("Upload JD", type=["pdf", "docx", "txt"])
    jd_text = jd_tab2.text_area("Paste JD text here", height=150)

    st.divider()

    # --- Resumes ---
    res_tab1, res_tab2 = st.tabs(["📎 Upload Files", "📂 Folder Path"])
    resume_files = res_tab1.file_uploader("Upload Resumes", type=["pdf", "docx", "txt"], accept_multiple_files=True)
    resume_folder = res_tab2.text_input("Folder Path", help="e.g. C:/Resumes")

    resume_paths = []
    if resume_files:
        st.success(f"📎 {len(resume_files)} file(s) selected")
    if resume_folder:
        from utils.file_handling import scan_resume_folder
        try:
            scanned = scan_resume_folder(resume_folder)
            st.success(f"📂 {len(scanned)} resume(s) found in folder")
        except Exception as e:
            st.error(f"Folder error: {e}")

    st.divider()

    if st.button("🚀 Run Analysis", use_container_width=True, type="primary"):

        # Handle JD
        from processing.resume_text_extractor import extract_text
        import shutil
        import uuid

        # Create a unique temp folder for this specific run to avoid collisions
        run_id = str(uuid.uuid4())
        temp_dir = Path("temp_uploads") / run_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            if jd_file:
                temp_jd = temp_dir / jd_file.name
                temp_jd.write_bytes(jd_file.getbuffer())
                jd_text = extract_text(temp_jd)

            # Handle resumes
            if resume_files:
                for f in resume_files:
                    p = temp_dir / f.name
                    p.write_bytes(f.getbuffer())
                    resume_paths.append(p)
            elif resume_folder:
                from utils.file_handling import scan_resume_folder
                resume_paths = scan_resume_folder(resume_folder)
            else:
                st.warning("Upload resumes or provide a folder.")
                return

            if not resume_paths:
                st.warning("No valid resumes found.")
                return

            # ---------- LIVE PROGRESS ----------
            progress_bar = st.progress(0, text="Initializing...")
            status_box = st.empty()

            def on_progress(phase, current, total, message):
                if phase == "stage1":
                    pct = current / total if total > 0 else 0
                    progress_bar.progress(pct, text=f"Stage 1 — {current}/{total} resumes")
                    status_box.caption(message)
                elif phase == "stage2":
                    progress_bar.progress(0.95, text="Stage 2 — Expert ranking")
                    status_box.caption(message)
                elif phase == "done":
                    progress_bar.progress(1.0, text="✅ Complete!")
                    status_box.caption(message)

            result = await process_analysis(
                analysis_name, jd_text, resume_paths,
                user["user_id"], model=model_choice,
                progress_callback=on_progress
            )

            if result.get("status") == "cached":
                progress_bar.empty()
                st.warning("⚠ Identical analysis already exists — showing cached results.")
                st.session_state.selected_analysis = result["analysis_id"]
                st.rerun()

            st.balloons()
            st.session_state.selected_analysis = result["analysis_id"]
            st.rerun()

        except Exception as e:
            st.error(f"Analysis failed: {e}")
        finally:
            # CLEANUP: Delete the unique temp folder for this run
            if temp_dir.exists():
                shutil.rmtree(temp_dir)


# ============================================================
# CHANGE PASSWORD
# ============================================================

async def show_change_password(user):

    st.title("🔑 Change Password")

    with st.form("change_pwd"):
        current = st.text_input("Current Password", type="password")
        new = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm New Password", type="password")

        submitted = st.form_submit_button("Update")

        if submitted:
            if new != confirm:
                st.error("Passwords do not match.")
            else:
                success, error = await change_password(
                    user["user_id"], current, new
                )
                if success:
                    st.success("Password updated.")
                else:
                    st.error(error)


# ============================================================
# ADMIN PANEL
# ============================================================

async def show_admin_panel():

    st.title("Admin Panel")

    with st.expander("Create User"):
        with st.form("create_user"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            is_admin = st.checkbox("Admin")
            submitted = st.form_submit_button("Create")

            if submitted:
                user_id, error = await create_user(
                    username, password, is_admin
                )
                if user_id:
                    st.success("User created.")
                else:
                    st.error(error)

    st.divider()

    users = await list_users()

    for u in users:
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(u["username"])
        col2.write("Admin" if u["is_admin"] else "User")

        if col3.button("Delete", key=u["user_id"]):
            await delete_user(u["user_id"])
            st.rerun()


# ============================================================
# DEBUG DASHBOARD (Admin Only)
# ============================================================

async def show_debug_dashboard():
    import sqlite3
    import pandas as pd

    st.title("🛠 Debug Dashboard")
    st.caption("LLM calls vs Cache hits")

    try:
        conn = sqlite3.connect("neuralcv.db")

        total = pd.read_sql("SELECT COUNT(*) as c FROM candidate", conn).iloc[0]['c']
        llm = pd.read_sql("SELECT COUNT(*) as c FROM candidate WHERE was_cached = 0", conn).iloc[0]['c']
        cached = pd.read_sql("SELECT COUNT(*) as c FROM candidate WHERE was_cached = 1", conn).iloc[0]['c']

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Candidates", total)
        c2.metric("LLM Calls", llm)
        c3.metric("Cache Hits", cached)

        st.divider()
        st.subheader("📁 Per-Analysis Breakdown")
        query = """
        SELECT a.analysis_name,
               COUNT(c.candidate_id) as total,
               SUM(CASE WHEN c.was_cached=1 THEN 1 ELSE 0 END) as hits,
               SUM(CASE WHEN c.was_cached=0 THEN 1 ELSE 0 END) as calls
        FROM analysis a
        LEFT JOIN candidate c ON a.analysis_id = c.analysis_id
        GROUP BY a.analysis_id ORDER BY a.created_at DESC
        """
        st.dataframe(pd.read_sql(query, conn), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("📄 LLM Logs")
        log_path = Path("logs/debug_llm.txt")
        if log_path.exists():
            st.text_area("Last 5000 chars", log_path.read_text(encoding="utf-8")[-5000:], height=300)
        else:
            st.info("No logs yet.")

        conn.close()
    except Exception as e:
        st.error(f"DB error: {e}")


# ============================================================
# DB VIEWER (Admin Only)
# ============================================================

async def show_db_viewer():
    import sqlite3
    import pandas as pd

    st.title("🗄 Database Viewer")

    try:
        conn = sqlite3.connect("neuralcv.db")
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()

        if not tables:
            st.warning("No tables found.")
            return

        selected = st.selectbox("Select Table", tables)
        conn = sqlite3.connect("neuralcv.db")
        df = pd.read_sql(f"SELECT * FROM {selected}", conn)
        conn.close()

        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"{len(df)} rows")
    except Exception as e:
        st.error(f"DB error: {e}")


# ============================================================
# MAIN
# ============================================================

async def main():

    if not require_auth():
        await show_login()
        return

    user = st.session_state["user"]

    # Internal view routing
    if st.session_state.get("selected_analysis"):

        await show_analysis_results()
        return

    page = sidebar_navigation(user)

    if page == "Dashboard":
        await show_dashboard(user)

    elif page == "New Analysis":
        await show_new_analysis(user)

    elif page == "Change Password":
        await show_change_password(user)

    elif page == "Admin Panel" and user["is_admin"]:
        await show_admin_panel()

    elif page == "Debug Dashboard" and user["is_admin"]:
        await show_debug_dashboard()

    elif page == "DB Viewer" and user["is_admin"]:
        await show_db_viewer()


run_async(main())