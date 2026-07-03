# Shared theme constants and CSS for CUAP Finance Portal

CUAP_LOGO = "https://cuap.ac.in/wp-content/uploads/2025/05/cu_logo_mod.png"
CUAP_FULL  = "Central University of Andhra Pradesh"
CUAP_SHORT = "CUAP"
CUAP_ADDR  = "'Jnana Seema', Ananthapuramu, Andhra Pradesh – 515701"
CUAP_VC    = "Prof. S A Kori"
CUAP_WEB   = "https://cuap.ac.in"
CUAP_EST   = "2018"

# Brand colors
PRIMARY   = "#003366"   # CUAP navy blue
SECONDARY = "#F4A41C"   # CUAP gold
SUCCESS   = "#1a7a4a"
DANGER    = "#c0392b"
WARNING   = "#d4700a"
LIGHT_BG  = "#f5f7fa"

ENTERPRISE_CSS = """
<style>
/* ── Reset & Base ─────────────────────────────────────── */
[data-testid="stAppViewContainer"] { background: #f0f2f6; }
[data-testid="stSidebar"] { background: #003366 !important; }
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] a { color: #F4A41C !important; }
[data-testid="stSidebarNav"] a { border-radius: 8px; margin: 2px 0; padding: 8px 12px; }
[data-testid="stSidebarNav"] a:hover { background: rgba(244,164,28,0.15) !important; }
[data-testid="stSidebarNav"] a[aria-selected="true"] {
    background: rgba(244,164,28,0.25) !important;
    border-left: 3px solid #F4A41C;
}
.main .block-container { padding-top: 1rem; max-width: 1400px; }

/* ── Top Header Banner ────────────────────────────────── */
.cuap-header {
    background: linear-gradient(135deg, #003366 0%, #00509e 100%);
    border-radius: 12px;
    padding: 16px 24px;
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0,51,102,0.3);
}
.cuap-header-text h1 {
    color: #ffffff; font-size: 1.6rem; font-weight: 700; margin: 0; line-height: 1.2;
}
.cuap-header-text p { color: #b8d4f0; font-size: 0.85rem; margin: 4px 0 0 0; }
.cuap-badge {
    background: #F4A41C; color: #003366; padding: 4px 12px;
    border-radius: 20px; font-size: 0.75rem; font-weight: 700;
    display: inline-block; margin-top: 6px;
}

/* ── KPI Cards ────────────────────────────────────────── */
.kpi-card {
    background: white;
    border-radius: 12px;
    padding: 20px 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    border-left: 5px solid #003366;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.12); }
.kpi-card::after {
    content: ''; position: absolute; right: -20px; top: -20px;
    width: 80px; height: 80px; border-radius: 50%;
    background: rgba(0,51,102,0.05);
}
.kpi-label { font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }
.kpi-value { font-size: 1.9rem; font-weight: 800; color: #003366; margin: 6px 0 2px; line-height: 1; }
.kpi-sub   { font-size: 0.78rem; color: #9ca3af; }
.kpi-card.green  { border-left-color: #1a7a4a; }
.kpi-card.green  .kpi-value { color: #1a7a4a; }
.kpi-card.red    { border-left-color: #c0392b; }
.kpi-card.red    .kpi-value { color: #c0392b; }
.kpi-card.gold   { border-left-color: #F4A41C; }
.kpi-card.gold   .kpi-value { color: #d4700a; }
.kpi-card.purple { border-left-color: #7c3aed; }
.kpi-card.purple .kpi-value { color: #7c3aed; }
.kpi-trend-up   { color: #1a7a4a; font-size: 0.78rem; font-weight: 600; }
.kpi-trend-down { color: #c0392b; font-size: 0.78rem; font-weight: 600; }

/* ── Section Headers ──────────────────────────────────── */
.section-header {
    display: flex; align-items: center; gap: 10px;
    padding: 12px 0 8px;
    border-bottom: 2px solid #003366;
    margin-bottom: 16px;
}
.section-header h3 { color: #003366; font-size: 1.1rem; font-weight: 700; margin: 0; }
.section-pill {
    background: #F4A41C; color: #003366;
    padding: 2px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 700;
}

/* ── Alert Banners ────────────────────────────────────── */
.alert-critical {
    background: #fef2f2; border: 1px solid #fecaca; border-left: 4px solid #c0392b;
    border-radius: 8px; padding: 10px 16px; margin: 8px 0;
    color: #7f1d1d; font-size: 0.88rem;
}
.alert-warning {
    background: #fffbeb; border: 1px solid #fde68a; border-left: 4px solid #F4A41C;
    border-radius: 8px; padding: 10px 16px; margin: 8px 0;
    color: #78350f; font-size: 0.88rem;
}
.alert-info {
    background: #eff6ff; border: 1px solid #bfdbfe; border-left: 4px solid #003366;
    border-radius: 8px; padding: 10px 16px; margin: 8px 0;
    color: #1e3a5f; font-size: 0.88rem;
}
.alert-success {
    background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #1a7a4a;
    border-radius: 8px; padding: 10px 16px; margin: 8px 0;
    color: #14532d; font-size: 0.88rem;
}

/* ── Status Badges ────────────────────────────────────── */
.badge { padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; display: inline-block; }
.badge-green  { background: #dcfce7; color: #166534; }
.badge-red    { background: #fee2e2; color: #991b1b; }
.badge-orange { background: #ffedd5; color: #9a3412; }
.badge-blue   { background: #dbeafe; color: #1e40af; }
.badge-gray   { background: #f3f4f6; color: #374151; }

/* ── Data Table ───────────────────────────────────────── */
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; box-shadow: 0 1px 8px rgba(0,0,0,0.08); }

/* ── Tabs ─────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tab"] { font-weight: 600; font-size: 0.9rem; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #003366 !important;
    border-bottom-color: #003366 !important;
}

/* ── Quick stats bar ──────────────────────────────────── */
.quick-stat { text-align:center; padding: 8px; }
.quick-stat .qs-val { font-size: 1.4rem; font-weight: 800; color: #003366; }
.quick-stat .qs-lbl { font-size: 0.72rem; color: #6b7280; text-transform: uppercase; }

/* ── Live indicator ───────────────────────────────────── */
.live-dot {
    display:inline-block; width:8px; height:8px; background:#1a7a4a;
    border-radius:50%; margin-right:5px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(26,122,74,0.4); }
    70%  { box-shadow: 0 0 0 6px rgba(26,122,74,0); }
    100% { box-shadow: 0 0 0 0 rgba(26,122,74,0); }
}

/* ── Footer ───────────────────────────────────────────── */
.cuap-footer {
    text-align: center; padding: 16px; color: #9ca3af;
    font-size: 0.78rem; border-top: 1px solid #e5e7eb; margin-top: 32px;
}

/* ── Scrollbar ────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #f1f1f1; }
::-webkit-scrollbar-thumb { background: #003366; border-radius: 3px; }
</style>
"""

def kpi_card(label, value, sub="", color="", icon=""):
    cls = f"kpi-card {color}".strip()
    return f"""
<div class="{cls}">
  <div class="kpi-label">{icon} {label}</div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-sub">{sub}</div>
</div>"""

def section_header(title, pill=""):
    pill_html = f'<span class="section-pill">{pill}</span>' if pill else ""
    return f"""
<div class="section-header">
  <h3>{title}</h3>{pill_html}
</div>"""

def alert(msg, kind="info"):
    return f'<div class="alert-{kind}">{"⚠️" if kind=="warning" else "🔴" if kind=="critical" else "ℹ️" if kind=="info" else "✅"} {msg}</div>'

def cuap_header(subtitle="Finance & Accounts Portal"):
    return f"""
<div class="cuap-header">
  <img src="{CUAP_LOGO}" style="height:64px; width:64px; object-fit:contain; flex-shrink:0;">
  <div class="cuap-header-text" style="flex:1;">
    <h1>{CUAP_FULL}</h1>
    <p>{CUAP_ADDR} &nbsp;|&nbsp; VC: {CUAP_VC} &nbsp;|&nbsp; Est. {CUAP_EST}</p>
    <span class="cuap-badge">🔒 On-Premise · Secure · {subtitle}</span>
  </div>
</div>"""
