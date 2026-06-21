import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
import sys
import os
from ai_email_service import run_auto_reply, send_emails_to_leads, get_unread_emails

# Fix path BEFORE any local imports
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from services.gmail_service import send_email, reply_to_email, get_recent_emails
# Ensure chatbot_server can be safely missed if tested standalone
try:
    import chatbot_server
except ImportError:
    pass

st.set_page_config(
    page_title="AutoPilot AI CRM",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CLEANED AND FIX STYLE OVERRIDES
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;600;700;800&display=swap');

/* Target app containers and basic typography instead of '*' */
.stApp, h1, h2, h3, h4, h5, h6, p, label, span, button, div[data-testid="stMetricValue"] { 
    font-family: 'Inter', sans-serif !important; 
}

.stApp { background: #0F0E2A !important; }

/* Safely position the top header bar without breaking icon fonts */
header[data-testid="stHeader"] { 
    background-color: transparent !important;
    z-index: 999;
}

/* Ensure the sidebar collapse toggle remains clickable, visible, and uses its native font */
button[data-testid="collapsedControl"] {
    color: white !important;
}

.block-container { padding-top: 2rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }

/* SIDEBAR - Styled safely without destroying native structures */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D0B24 0%, #1A1744 50%, #2D2A6E 100%) !important;
    border-right: 1px solid rgba(99,102,241,0.3) !important;
}

/* NAV LINK HOVERS */
.nav-link {
    transition: all 0.25s ease !important;
}
.nav-link:hover {
    transform: translateX(5px) !important;
}

/* KPI CARDS */
div[data-testid="column"]:nth-child(1) [data-testid="metric-container"] {
    background: linear-gradient(135deg,#4338CA,#6366F1) !important;
    border-radius: 20px !important; padding: 24px !important; border: none !important;
    box-shadow: 0 8px 28px rgba(67,56,202,0.55) !important;
    transition: all 0.35s cubic-bezier(0.34,1.56,0.64,1) !important;
}
div[data-testid="column"]:nth-child(2) [data-testid="metric-container"] {
    background: linear-gradient(135deg,#C2410C,#F97316) !important;
    border-radius: 20px !important; padding: 24px !important; border: none !important;
    box-shadow: 0 8px 28px rgba(194,65,12,0.55) !important;
    transition: all 0.35s cubic-bezier(0.34,1.56,0.64,1) !important;
}
div[data-testid="column"]:nth-child(3) [data-testid="metric-container"] {
    background: linear-gradient(135deg,#065F46,#10B981) !important;
    border-radius: 20px !important; padding: 24px !important; border: none !important;
    box-shadow: 0 8px 28px rgba(6,95,70,0.55) !important;
    transition: all 0.35s cubic-bezier(0.34,1.56,0.64,1) !important;
}
div[data-testid="column"]:nth-child(4) [data-testid="metric-container"] {
    background: linear-gradient(135deg,#6D28D9,#A78BFA) !important;
    border-radius: 20px !important; padding: 24px !important; border: none !important;
    box-shadow: 0 8px 28px rgba(109,40,217,0.55) !important;
    transition: all 0.35s cubic-bezier(0.34,1.56,0.64,1) !important;
}
[data-testid="metric-container"]:hover { transform: translateY(-10px) scale(1.04) !important; filter: brightness(1.12) !important; }
[data-testid="stMetricLabel"] { color: rgba(255,255,255,0.85) !important; font-size: 12px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 1px !important; }
[data-testid="stMetricValue"] { color: white !important; font-size: 36px !important; font-weight: 800 !important; }
[data-testid="stMetricDelta"] { color: rgba(255,255,255,0.9) !important; }

[data-testid="stPlotlyChart"] {
    background: #1A1744 !important; border-radius: 24px !important; padding: 20px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    transition: all 0.3s ease !important;
}
[data-testid="stPlotlyChart"]:hover { box-shadow: 0 20px 56px rgba(99,102,241,0.3) !important; transform: translateY(-6px) !important; border-color: #6366F1 !important; }
[data-testid="stDataFrame"] { background: #1A1744 !important; border-radius: 20px !important; padding: 12px !important; border: 1px solid rgba(99,102,241,0.25) !important; }
[data-testid="stAlert"] { border-radius: 14px !important; border: none !important; transition: all 0.25s ease !important; }
[data-testid="stAlert"]:hover { transform: translateX(8px) !important; }
h2, h3 { color: white !important; }
p, li { color: rgba(255,255,255,0.85) !important; }
hr { border-color: rgba(99,102,241,0.2) !important; }
.stButton button { background: linear-gradient(135deg,#6366F1,#8B5CF6) !important; color: white !important; border: none !important; border-radius: 14px !important; font-weight: 700 !important; transition: all 0.3s ease !important; box-shadow: 0 4px 16px rgba(99,102,241,0.4) !important; }
.stButton button:hover { transform: translateY(-3px) !important; box-shadow: 0 10px 28px rgba(99,102,241,0.55) !important; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background: linear-gradient(#6366F1,#8B5CF6); border-radius: 10px; }
#chatbot-frame { position: fixed !important; bottom: 0 !important; right: 16px !important; width: 380px !important; height: 630px !important; border: none !important; z-index: 99999 !important; background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# DATABASE CONNECTION (Fallback added for schema differences if tested empty)
try:
    conn = sqlite3.connect("leads.db")
    df = pd.read_sql_query("SELECT * FROM leads", conn)
except Exception:
    # Fallback dummy data structure if database isn't built yet locally
    df = pd.DataFrame(columns=["id", "estimated_value", "lead_type", "status", "created_at", "customer_email", "customer_message", "lead_score"])

total_revenue = df["estimated_value"].astype(float).sum() if not df.empty else 0
hot_leads = len(df[df["lead_type"] == "Hot"]) if not df.empty else 0
total_leads = len(df)
new_leads = len(df[df["status"] == "New"]) if not df.empty else 0

CHART_BG = "#1A1744"
CHART_GRID = "rgba(99,102,241,0.15)"
FONT_COLOR = "#C4B5FD"
COLORS = ["#6366F1","#8B5CF6","#A78BFA","#4F46E5","#3730A3"]

def chart_layout(fig, title=""):
    fig.update_layout(
        plot_bgcolor=CHART_BG, paper_bgcolor=CHART_BG,
        font=dict(family="Inter", size=13, color=FONT_COLOR),
        title=dict(text=title, font=dict(size=17, color="white")),
        xaxis=dict(showgrid=False, tickfont=dict(color=FONT_COLOR), linecolor="rgba(99,102,241,0.2)"),
        yaxis=dict(gridcolor=CHART_GRID, tickfont=dict(color=FONT_COLOR), linecolor="rgba(99,102,241,0.2)"),
        margin=dict(l=10, r=10, t=50, b=10),
        hoverlabel=dict(bgcolor="#4F46E5", font_color="white", bordercolor="#6366F1"),
        legend=dict(font=dict(color=FONT_COLOR))
    )
    return fig

# SIDEBAR
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:16px 0 8px;">
        <span style="font-size:20px;font-weight:800;color:white;">🚀 AutoPilot AI</span>
    </div>
    """, unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712109.png", width=100)
    st.markdown("<hr style='border-color:rgba(99,102,241,0.3);margin:8px 0 12px;'>", unsafe_allow_html=True)
    
    selected = option_menu(
        menu_title=None,
        options=["Dashboard","Leads","Agents","Analytics","Alerts","Settings","Gmail"],
        icons=["house-fill","people-fill","robot","bar-chart-fill","bell-fill","gear-fill","envelope-fill"],
        default_index=0,
        styles={
            "container": {"background-color": "transparent", "padding": "0"},
            "icon": {"color": "white", "font-size": "15px"},
            "nav-link": {
                "color": "white", "font-size": "14px", "font-weight": "600",
                "border-radius": "12px", "margin": "3px 0", "padding": "10px 16px",
                "background-color": "rgba(99,102,241,0.2)",
                "border": "1px solid rgba(99,102,241,0.3)",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg,#6366F1,#8B5CF6)",
                "color": "white", "font-weight": "700", "border": "none",
                "box-shadow": "0 4px 16px rgba(99,102,241,0.5)",
            },
        }
    )

# DASHBOARD
if selected == "Dashboard":
    st.markdown("""
    <div style="background:linear-gradient(135deg,#4338CA 0%,#7C3AED 55%,#6D28D9 100%);
    padding:36px 44px;border-radius:24px;color:white;margin-bottom:28px;
    box-shadow:0 16px 56px rgba(67,56,202,0.5);display:flex;align-items:center;gap:22px;
    position:relative;overflow:hidden;">
        <div style="position:absolute;top:-40px;right:-40px;width:220px;height:220px;background:rgba(255,255,255,0.06);border-radius:50%;"></div>
        <div style="position:absolute;bottom:-60px;right:100px;width:170px;height:170px;background:rgba(255,255,255,0.04);border-radius:50%;"></div>
        <div style="font-size:60px;z-index:1;">🚀</div>
        <div style="z-index:1;">
            <div style="display:inline-block;background:rgba(255,255,255,0.18);padding:4px 14px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:3px;margin-bottom:10px;">AI-POWERED CRM PLATFORM</div>
            <h1 style="margin:0;color:white;font-size:40px;font-weight:800;letter-spacing:-1.5px;">AutoPilot AI CRM</h1>
            <p style="margin:10px 0 0;font-size:15px;opacity:0.8;">Lead Management &nbsp;•&nbsp; AI Automation &nbsp;•&nbsp; Real-time Analytics</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1,col2,col3,col4 = st.columns(4)
    with col1: st.metric("📨 Total Leads", total_leads)
    with col2: st.metric("🔥 Hot Leads", hot_leads)
    with col3: st.metric("💰 Revenue", f"${total_revenue:,}")
    with col4: st.metric("🤖 AI Accuracy", "96%")

    st.markdown("---")
    st.subheader("⚡ AI Performance")
    col1,col2,col3,col4 = st.columns(4)
    with col1: st.metric("Response Time","1.4s","-0.3s")
    with col2: st.metric("Emails Generated","248","+18")
    with col3: st.metric("Lead Accuracy","96%","+2%")
    with col4: st.metric("Agents Online","4/4","+1")

    st.markdown("---")
    col1,col2 = st.columns(2)
    with col1:
        st.subheader("🤖 Active AI Agents")
        st.info("📧 Email Responder - Active")
        st.info("🔥 Lead Qualifier - Active")
        st.info("💬 AI Sales Coach - Active")
        st.warning("📊 Analytics Bot - Idle")
    with col2:
        st.subheader("📈 Workflow Analytics")
        wf = pd.DataFrame({"Workflow":["Lead Scoring","Email Replies","CRM Updates","Sales Coach"],"Performance":[92,88,95,90]})
        fig = px.bar(wf,x="Workflow",y="Performance",color="Performance",color_continuous_scale=["#4338CA","#6366F1","#818CF8"])
        fig.update_traces(marker_line_width=0,marker_cornerradius=10)
        fig = chart_layout(fig,"📈 Workflow Performance")
        fig.update_layout(coloraxis_showscale=False,height=340)
        st.plotly_chart(fig,use_container_width=True)

    st.markdown("---")
    st.subheader("📡 Live Activity Feed")
    for item in ["📧 Email Responder replied to client","🔥 Lead Qualifier scored new lead","🤖 AI Sales Coach generated proposal","📊 Analytics Bot updated dashboard"]:
        st.info(item)

    st.markdown("---")
    col1,col2 = st.columns(2)
    with col1:
        if not df.empty and "created_at" in df.columns:
            lg = df.groupby("created_at").size().reset_index(name="count")
            fig = px.area(lg,x="created_at",y="count",color_discrete_sequence=["#818CF8"])
            fig.update_traces(fill='tozeroy',fillcolor='rgba(99,102,241,0.2)',line=dict(color="#818CF8",width=3),mode='lines+markers',marker=dict(size=8,color="#6366F1",line=dict(color="#C4B5FD",width=2)))
            fig = chart_layout(fig,"📈 Lead Growth Trend")
            fig.update_layout(height=380)
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.info("No timeline data to map trends.")
    with col2:
        if not df.empty and "status" in df.columns:
            sc = df["status"].value_counts().reset_index()
            sc.columns = ["Status","Count"]
            fig2 = px.pie(sc,names="Status",values="Count",hole=0.55,color_discrete_sequence=COLORS)
            fig2.update_traces(textposition='outside',textinfo='percent+label',textfont=dict(color="white"),marker=dict(line=dict(color=CHART_BG,width=3)),pull=[0.06,0,0,0])
            fig2 = chart_layout(fig2,"🥧 Lead Status Distribution")
            fig2.update_layout(height=380,legend=dict(font=dict(color=FONT_COLOR),orientation="h",y=-0.15))
            st.plotly_chart(fig2,use_container_width=True)
        else:
            st.info("No lead data to display distributions.")

    st.markdown("---")
    rd = pd.DataFrame({"Month":["Jan","Feb","Mar","Apr","May","Jun"],"Revenue":[5000,8000,12000,15000,18000,20000]})
    fig = px.bar(rd,x="Month",y="Revenue",color="Revenue",color_continuous_scale=["#3730A3","#4F46E5","#6366F1","#818CF8","#C4B5FD"])
    fig.update_traces(marker_line_width=0,marker_cornerradius=12)
    fig = chart_layout(fig,"💰 Revenue Growth")
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig,use_container_width=True)

    st.markdown("---")
    st.subheader("🏆 Top Priority Leads")
    if not df.empty and "lead_score" in df.columns:
        st.dataframe(df.sort_values(by="lead_score",ascending=False).head(5),use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Sales Pipeline Funnel")
    pf = pd.DataFrame({"Stage":["New Leads","Qualified","Proposal Sent","Negotiation","Won Deal"],"Count":[20,15,10,5,2]})
    fig = px.funnel(pf,x="Count",y="Stage")
    fig.update_traces(marker=dict(color=["#3730A3","#4F46E5","#6366F1","#818CF8","#C4B5FD"],line=dict(color=CHART_BG,width=2)))
    fig = chart_layout(fig,"🎯 Lead Conversion Funnel")
    st.plotly_chart(fig,use_container_width=True)

elif selected == "Leads":
    st.markdown("""<div style="background:linear-gradient(135deg,#1D4ED8,#4F46E5);padding:28px 36px;border-radius:24px;color:white;margin-bottom:24px;box-shadow:0 10px 36px rgba(29,78,216,0.4);"><h1 style="margin:0;color:white;font-size:32px;font-weight:800;">👥 Lead Management</h1><p style="margin:8px 0 0;opacity:0.8;">Manage and track customer leads</p></div>""", unsafe_allow_html=True)
    col1,col2,col3,col4 = st.columns(4)
    with col1: st.metric("Total Leads","125","+12")
    with col2: st.metric("Qualified","78","+8")
    with col3: st.metric("Won","45","+6")
    with col4: st.metric("Revenue","$21K","+14%")
    search = st.text_input("🔍 Search Lead")
    filtered_df = df.copy()
    if search and not df.empty:
        filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(search,case=False)).any(axis=1)]
    st.subheader("📋 Lead Database")
    st.dataframe(filtered_df,use_container_width=True)
    st.subheader("🕒 Recent Activity")
    st.success("Lead John Doe moved to Qualified")
    st.info("Proposal sent to ABC Company")
    st.warning("Follow-up pending for Rahul")
    st.markdown("---")
    if not df.empty:
        col1,col2 = st.columns(2)
        with col1: selected_id = st.selectbox("📌 Select Lead",df["id"].tolist())
        with col2: selected_status = st.selectbox("🚀 Change Status",["New","Contacted","Qualified","Converted"])
        if st.button("✅ Update Lead Status"):
            c = sqlite3.connect("leads.db")
            c.cursor().execute("UPDATE leads SET status=? WHERE id=?",(selected_status,selected_id))
            c.commit(); c.close()
            st.success(f"Lead #{selected_id} updated to {selected_status}")
        row = df[df["id"]==selected_id]
        if not row.empty:
            r = row.iloc[0]
            st.info(f"📧 {r['customer_email']}  |  📌 {r['status']}  |  📅 {r['created_at']}")
    st.markdown("---")
    def score(m):
        return min(sum(15 for w in ["price","pricing","cost","demo","service","automation","business"] if w in str(m).lower()),100)
    
    if not df.empty:
        df["Lead Score"] = df["customer_message"].apply(score)
        st.dataframe(df[["id","customer_email","status","Lead Score"]],use_container_width=True)
        df.to_excel("leads_export.xlsx",index=False)
        with open("leads_export.xlsx","rb") as f:
            st.download_button("📥 Download Excel",f,file_name="leads.xlsx")

elif selected == "Agents":
    st.markdown("""<div style="background:linear-gradient(135deg,#5B21B6,#7C3AED);padding:28px 36px;border-radius:24px;color:white;margin-bottom:24px;"><h1 style="margin:0;color:white;font-size:32px;font-weight:800;">🤖 AI Agents</h1></div>""", unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.metric("Active Agents","3/4","+1")
        st.info("📧 Email Responder - Active")
        st.info("🔥 Lead Qualifier - Active")
        st.info("💬 AI Sales Coach - Active")
        st.warning("📊 Analytics Bot - Idle")
    with col2:
        ad = pd.DataFrame({"Agent":["Email Responder","Lead Qualifier","Sales Coach","Analytics Bot"],"Tasks":[248,189,95,0]})
        fig = px.bar(ad,x="Agent",y="Tasks",color="Tasks",color_continuous_scale=["#3730A3","#6366F1","#A78BFA"])
        fig.update_traces(marker_cornerradius=10,marker_line_width=0)
        fig = chart_layout(fig,"Agent Performance")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig,use_container_width=True)

elif selected == "Analytics":
    st.markdown("""<div style="background:linear-gradient(135deg,#0F172A,#1E1B4B);padding:28px 36px;border-radius:24px;color:white;margin-bottom:24px;"><h1 style="margin:0;color:white;font-size:32px;font-weight:800;">📊 Analytics</h1></div>""", unsafe_allow_html=True)
    col1,col2,col3,col4 = st.columns(4)
    with col1: st.metric("Total Leads",total_leads)
    with col2: st.metric("Hot Leads",hot_leads)
    with col3: st.metric("Revenue",f"${total_revenue:,}")
    with col4: st.metric("Conversion","36%","+4%")
    col1,col2 = st.columns(2)
    with col1:
        if not df.empty:
            lg = df.groupby("created_at").size().reset_index(name="count")
            fig = px.area(lg,x="created_at",y="count",color_discrete_sequence=["#818CF8"])
            fig.update_traces(fill='tozeroy',fillcolor='rgba(99,102,241,0.2)',line=dict(color="#818CF8",width=3))
            fig = chart_layout(fig,"📈 Lead Growth")
            st.plotly_chart(fig,use_container_width=True)
    with col2:
        if not df.empty:
            sc = df["status"].value_counts().reset_index()
            sc.columns = ["Status","Count"]
            fig2 = px.pie(sc,names="Status",values="Count",hole=0.5,color_discrete_sequence=COLORS)
            fig2.update_traces(marker=dict(line=dict(color=CHART_BG,width=3)),textfont=dict(color="white"))
            fig2 = chart_layout(fig2,"Lead Status")
            st.plotly_chart(fig2,use_container_width=True)

elif selected == "Alerts":
    st.markdown("""<div style="background:linear-gradient(135deg,#991B1B,#DC2626);padding:28px 36px;border-radius:24px;color:white;margin-bottom:24px;"><h1 style="margin:0;color:white;font-size:32px;font-weight:800;">🔔 Alerts</h1></div>""", unsafe_allow_html=True)
    st.warning("⚠️ 3 leads need follow-up today")
    st.error("🔴 Analytics Bot is idle")
    st.success("✅ All emails sent successfully")
    st.info("ℹ️ New lead from client@example.com")

elif selected == "Settings":
    st.markdown("""<div style="background:linear-gradient(135deg,#1F2937,#374151);padding:28px 36px;border-radius:24px;color:white;margin-bottom:24px;"><h1 style="margin:0;color:white;font-size:32px;font-weight:800;">⚙️ Settings</h1></div>""", unsafe_allow_html=True)
    st.text_input("Company Name","AutoPilot AI")
    st.text_input("Admin Email","admin@autopilot.ai")
    st.selectbox("Timezone",["IST (UTC+5:30)","UTC","EST"])
    if st.button("💾 Save Settings"):
        st.success("✅ Settings saved!")
# ─────────────────────────────────────────────────────────────────────────────
# ADD THIS IMPORT at the top of app.py (after existing imports):
# from ai_email_service import run_auto_reply, send_emails_to_leads, get_unread_emails
# ─────────────────────────────────────────────────────────────────────────────

elif selected == "Gmail":
    st.markdown("""
        <div style='background:linear-gradient(135deg,#EA4335 0%,#FBBC05 33%,#34A853 66%,#4285F4 100%);
                    padding:3px; border-radius:24px; margin-bottom:1.5rem'>
            <div style='background:#0f1117; border-radius:22px; padding:28px 36px'>
                <h1 style='color:white; margin:0; font-size:32px; font-weight:800'>📧 Gmail AI</h1>
                <p style='color:rgba(255,255,255,0.7); margin:8px 0 0'>AI-powered email automation for your CRM</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── KPI row ───────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("🤖 Auto-Reply", "Active" if st.session_state.get("auto_reply_on") else "Off")
    with col2: st.metric("📨 Replies Sent", st.session_state.get("total_replies", 0))
    with col3: st.metric("📬 Lead Emails", st.session_state.get("total_lead_emails", 0))

    st.markdown("---")

    # ── 3 Tabs ────────────────────────────────────────────────────────────────
    tab_auto, tab_leads, tab_inbox = st.tabs([
        "🤖 AI Auto-Reply", "📨 Email Leads", "📥 Inbox"
    ])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — AI AUTO-REPLY
    # ════════════════════════════════════════════════════════════════════════
    with tab_auto:
        st.markdown("### 🤖 AI Auto-Reply Engine")
        st.info("Claude reads your unread emails and sends professional AI-generated replies automatically.")

        col1, col2 = st.columns(2)
        with col1:
            interval = st.selectbox("⏱ Check every", [2, 5, 10, 15, 30], index=1, 
                                     format_func=lambda x: f"{x} minutes")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            auto_on = st.toggle("🟢 Enable Auto-Reply", 
                                value=st.session_state.get("auto_reply_on", False))
            st.session_state["auto_reply_on"] = auto_on

        if auto_on:
            st.success(f"✅ Auto-reply is ON — checking every {interval} minutes")
            
            # Check if it's time to run
            import time as time_module
            last_run = st.session_state.get("last_auto_reply_time", 0)
            now = time_module.time()
            seconds_since = now - last_run
            next_run_in = max(0, (interval * 60) - seconds_since)
            
            st.caption(f"⏳ Next check in: {int(next_run_in // 60)}m {int(next_run_in % 60)}s")

            # Auto-trigger if interval passed
            if seconds_since >= interval * 60:
                with st.spinner("🤖 AI is checking and replying to emails..."):
                    results = run_auto_reply()
                    st.session_state["last_auto_reply_time"] = time_module.time()
                    st.session_state["total_replies"] = (
                        st.session_state.get("total_replies", 0) + results["replied"]
                    )
                    st.session_state["last_auto_results"] = results
                st.rerun()

        # Manual trigger button
        st.markdown("---")
        st.markdown("#### 🔘 Manual Run")
        if st.button("▶️ Run Auto-Reply Now", use_container_width=True):
            with st.spinner("🤖 AI reading and replying to unread emails..."):
                results = run_auto_reply()
                st.session_state["total_replies"] = (
                    st.session_state.get("total_replies", 0) + results["replied"]
                )
                st.session_state["last_auto_results"] = results

        # Show last run results
        if "last_auto_results" in st.session_state:
            r = st.session_state["last_auto_results"]
            st.markdown("#### 📊 Last Run Results")
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Emails Checked", r["checked"])
            with col2: st.metric("Replies Sent", r["replied"])
            with col3: st.metric("Errors", len(r["errors"]))
            
            if r["details"]:
             st.markdown("##### 📋 Details")
    for d in r["details"]:
        is_success = "Replied" in d["status"]
        label = f"{'Sent' if is_success else 'Failed'}: {d['to']} — {d['subject']}"
        with st.expander(label, icon="✅" if is_success else "❌"):
            st.write(f"**Status:** {d['status']}")
            if d.get("reply_preview"):
                st.write(f"**Reply preview:** {d['reply_preview']}")
            
                        
            if r["errors"]:
                for err in r["errors"]:
                    st.error(err)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — EMAIL LEADS
    # ════════════════════════════════════════════════════════════════════════
    with tab_leads:
        st.markdown("### 📨 Send Personalized Emails to Leads")
        st.info("Claude generates a unique, personalized email for each lead based on their profile and message.")

        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox(
                "📌 Which leads to email?",
                ["All", "New", "Contacted", "Qualified", "Converted"]
            )
        with col2:
            # Preview count
            try:
                c = sqlite3.connect("leads.db")
                if status_filter == "All":
                    count = c.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
                else:
                    count = c.execute(
                        "SELECT COUNT(*) FROM leads WHERE status=?", (status_filter,)
                    ).fetchone()[0]
                c.close()
                st.metric("📊 Leads selected", count)
            except:
                st.metric("📊 Leads selected", "?")

        custom_context = st.text_area(
            "✏️ What should the email focus on?",
            placeholder="e.g. 'Offer a free 30-min demo', 'Follow up on their pricing inquiry', 'Promote our new AI features'...",
            height=100,
        )

        # Preview one AI email before sending all
        if st.button("👁️ Preview AI Email for First Lead", use_container_width=False):
            try:
                c = sqlite3.connect("leads.db")
                c.row_factory = sqlite3.Row
                if status_filter == "All":
                    lead = dict(c.execute("SELECT * FROM leads LIMIT 1").fetchone())
                else:
                    lead = dict(c.execute(
                        "SELECT * FROM leads WHERE status=? LIMIT 1", (status_filter,)
                    ).fetchone())
                c.close()
                with st.spinner("Generating preview..."):
                    from ai_email_service import generate_lead_email
                    preview = generate_lead_email(lead, custom_context)
                st.success("✅ Preview generated!")
                st.markdown(f"**Subject:** {preview['subject']}")
                st.text_area("Body preview", preview['body'], height=200, disabled=True)
            except Exception as e:
                st.error(f"Preview failed: {e}")

        st.markdown("---")
        confirm = st.checkbox(f"✅ I confirm — send personalized emails to **{count if 'count' in dir() else 'all selected'}** leads")

        if st.button("🚀 Send AI Emails to Leads", use_container_width=True, 
                      disabled=not confirm):
            progress = st.progress(0, text="Starting...")
            status_box = st.empty()
            sent_count = [0]

            def update_status(msg):
                status_box.info(msg)

            with st.spinner("📨 Sending personalized AI emails to leads..."):
                results = send_emails_to_leads(
                    custom_context=custom_context,
                    status_filter=status_filter,
                    status_callback=update_status,
                )
                st.session_state["total_lead_emails"] = (
                    st.session_state.get("total_lead_emails", 0) + results["sent"]
                )

            progress.progress(100, text="Done!")
            st.success(f"✅ Sent: {results['sent']}  |  ❌ Failed: {results['failed']}")

            if results["details"]:
                st.markdown("##### 📋 Email Log")
                for d in results["details"]:
                    with st.expander(f"{d['status']} → {d['email']}"):
                        if d.get("subject"):
                            st.write(f"**Subject:** {d['subject']}")
                        if d.get("preview"):
                            st.write(f"**Preview:** {d['preview']}")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3 — INBOX
    # ════════════════════════════════════════════════════════════════════════
    with tab_inbox:
        st.markdown("### 📥 Unread Inbox")
        col1, col2 = st.columns([3, 1])
        with col1:
            n = st.slider("Emails to load", 5, 30, 10)
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            load = st.button("🔄 Refresh", use_container_width=True)

        if load:
            with st.spinner("Fetching unread emails..."):
                emails = get_unread_emails(max_results=n)
            if not emails:
                st.success("🎉 Inbox is empty — no unread emails!")
            else:
                st.warning(f"📬 {len(emails)} unread email(s)")
                for email in emails:
                    with st.expander(f"📧 {email['subject']} — from {email['from']}"):
                        st.write(f"**Date:** {email['date']}")
                        st.write(f"**Snippet:** {email['snippet']}")
                        if email.get("body"):
                            st.text_area("Body", email["body"][:500], height=120, 
                                        disabled=True, key=email["id"])

try:
    conn.close()
except Exception:
    pass


st.markdown("""
<style>
#chatbot-frame { 
    display: none !important;
}
</style>
""", unsafe_allow_html=True)