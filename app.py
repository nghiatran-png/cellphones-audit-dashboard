import base64
import gzip
import hashlib
import hmac
import html
import io
import json
import math
import numbers
import re
import secrets
import threading
import time
import traceback
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CellphoneS Audit Platform", page_icon="📱",
                   layout="wide", initial_sidebar_state="auto")

APP_VERSION = "5.6.0"
CPS_ITEMS = ["Demo", "Tủ máy", "Vách/Đảo", "CellphoneS"]
DTV_ITEMS = ["Trade Audit DTV"]
PLUS_ITEMS = [f"Plus {i}" for i in range(1, 6)]

_ver = tuple(int(p) for p in st.__version__.split(".")[:2] if p.isdigit())
STRETCH = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}

STATUS_LABEL = {"DONE": "✅ Hoàn thành", "REJECT": "❌ Bị từ chối", "WAIT_QC": "🕓 Chờ QC duyệt",
                "NOT_FIELD": "⏳ Chưa Field xong", "NONE": "— Chưa có plan"}
STATUS_COLOR = {STATUS_LABEL["DONE"]: "#12b76a", STATUS_LABEL["WAIT_QC"]: "#f79009", STATUS_LABEL["REJECT"]: "#f04438",
                STATUS_LABEL["NOT_FIELD"]: "#98a2b3", STATUS_LABEL["NONE"]: "#d0d5dd"}
REASON = {"WAIT_QC": "đã Field xong, chờ QC duyệt", "NOT_FIELD": "Field chưa hoàn thành", "NONE": "chưa có plan"}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--brand:#d70018;--brand2:#9b0012;--line:#e4e7ec;--ink:#101828;--muted:#667085;--bg:#f4f5f7;
--ok:#12b76a;--warn:#f79009;--bad:#f04438}
.stApp{background:var(--bg)}
.stApp,.stApp p,.stApp label,.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp button,.stApp input,.stApp textarea,
[data-testid="stMetric"] *{font-family:'Inter','Segoe UI',Arial,sans-serif}
.block-container{max-width:1680px;padding-top:2.2rem;padding-bottom:3rem}
#MainMenu,footer,.stAppDeployButton,[data-testid="stDeployButton"]{visibility:hidden;display:none}
header[data-testid="stHeader"]{background:transparent}
.hero{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:22px 28px;border-radius:18px;color:#fff;
background:radial-gradient(1200px 300px at 90% -40%,rgba(255,255,255,.18),transparent),linear-gradient(135deg,var(--brand),var(--brand2));
box-shadow:0 14px 32px rgba(215,0,24,.18);margin-bottom:18px}
.hero-title{font-size:26px;font-weight:800;letter-spacing:-.3px}.hero-sub{font-size:13px;opacity:.88;margin-top:4px}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{display:inline-block;padding:6px 12px;border-radius:999px;font-size:12px;font-weight:600;background:rgba(255,255,255,.16);color:#fff;white-space:nowrap}
.chip.dark{background:#f2f4f7;color:#344054;border:1px solid var(--line)}
.chip.ok{background:#ecfdf3;color:#067647;border:1px solid #abefc6}
.chip.warn{background:#fffaeb;color:#b54708;border:1px solid #fedf89}
.sec{margin:26px 0 10px}.sec .t{font-size:17px;font-weight:700;color:var(--ink)}.sec .s{font-size:12.5px;color:var(--muted);margin-top:2px}
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin-bottom:6px}
.kpi{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:0 1px 2px rgba(16,24,40,.05)}
.kpi .kl{font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.4px}
.kpi .kv{font-size:30px;font-weight:800;color:var(--ink);line-height:1.15;margin-top:6px}
.kpi .ks{font-size:12px;color:var(--muted);margin-top:2px}
.kpi.bad .kv{color:var(--bad)}
.kbar,.mbar{height:7px;background:#eaecf0;border-radius:99px;overflow:hidden;margin-top:10px}
.kbar span,.mbar span{display:block;height:100%;border-radius:99px}
.kpct{font-size:12px;font-weight:700;margin-top:6px}
.lead-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
.lcard{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 20px;box-shadow:0 1px 2px rgba(16,24,40,.05)}
.lname{font-size:15px;font-weight:700;color:var(--ink)}
.lpct{font-size:40px;font-weight:800;line-height:1.1;margin-top:8px}.lsub{font-size:12px;color:var(--muted);margin-bottom:10px}
.mrow{display:grid;grid-template-columns:62px 1fr 64px;align-items:center;gap:8px;margin-top:8px;font-size:12.5px}
.mrow .mn{color:#475467;font-weight:600}.mrow .mv{text-align:right;color:var(--ink);font-weight:600}
.mrow .mbar{margin-top:0}
div[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-left:4px solid var(--brand);border-radius:12px;padding:14px 16px;box-shadow:0 1px 2px rgba(16,24,40,.05)}
div[data-testid="stMetricLabel"]{color:var(--muted)!important;font-weight:600}
div[data-testid="stMetricValue"]{font-weight:800;color:var(--ink)}
.stTabs [data-baseweb="tab-list"],.stTabs [role="tablist"]{gap:2px;background:transparent;border-bottom:1px solid var(--line);padding:0;flex-wrap:wrap}
.stTabs [data-baseweb="tab"],.stTabs [role="tab"]{height:46px;padding:0 16px;font-weight:600;color:#475467;background:transparent;border-radius:8px 8px 0 0}
.stTabs [data-baseweb="tab"]:hover,.stTabs [role="tab"]:hover{background:#fff;color:var(--ink)}
.stTabs [aria-selected="true"]{color:var(--brand)!important;border-bottom:3px solid var(--brand)}
.stTabs [data-baseweb="tab-highlight"]{background-color:var(--brand);height:3px}
.stTabs [data-baseweb="tab-border"]{background-color:var(--line)}
div[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#fff}
div[data-testid="stPlotlyChart"]{background:#fff;border:1px solid var(--line);border-radius:14px;padding:6px 6px 0;box-shadow:0 1px 2px rgba(16,24,40,.05);overflow:hidden}
.stDownloadButton button{border-radius:10px;border:1px solid var(--brand);color:var(--brand);font-weight:600;background:#fff}
.stDownloadButton button:hover{background:var(--brand);color:#fff;border-color:var(--brand)}
section[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:12px;margin:4px 0 14px}
.logo{width:40px;height:40px;border-radius:11px;background:linear-gradient(135deg,var(--brand),var(--brand2));color:#fff;font-weight:800;font-size:20px;display:flex;align-items:center;justify-content:center}
.bn{font-weight:800;color:var(--ink);font-size:15px;line-height:1.1}.bs{font-size:11.5px;color:var(--muted)}
.sbt{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;margin:14px 0 6px}
.welcome{background:#fff;border:1px dashed #d0d5dd;border-radius:18px;padding:34px 38px;max-width:760px;margin:30px auto}
.welcome .wt{font-size:22px;font-weight:800;color:var(--ink)}.welcome .ws{color:var(--muted);margin:6px 0 16px}
.welcome ol{color:#344054;line-height:1.9;margin:0;padding-left:20px}
.st-key-bell_alert,.st-key-bell_ok{position:fixed;top:10px;right:96px;z-index:1000;width:auto!important}
.st-key-bell_alert button,.st-key-bell_ok button{border-radius:999px;font-weight:800;padding:6px 16px;box-shadow:0 6px 18px rgba(16,24,40,.18)}
.st-key-bell_alert button{background:#d92d20;color:#fff;border:2px solid #fff;animation:ring 1.6s infinite}
.st-key-bell_alert button:hover{background:#b42318;color:#fff;border-color:#fff}
.st-key-bell_ok button{background:#fff;color:#475467;border:1px solid var(--line)}
section[data-testid="stSidebar"] .chip{white-space:normal;line-height:1.35}
[data-testid="stForm"]{border:0!important;padding:0!important}
.st-key-bell_warn{position:fixed;top:10px;right:96px;z-index:1000;width:auto!important}
.st-key-bell_warn button{border-radius:999px;font-weight:800;padding:6px 16px;box-shadow:0 6px 18px rgba(16,24,40,.18);background:#f79009;color:#fff;border:2px solid #fff}
.st-key-bell_warn button:hover{background:#dc6803;color:#fff;border-color:#fff}
.kpi-row.compact{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}
.fbanner{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin-bottom:14px;box-shadow:0 1px 2px rgba(16,24,40,.05)}
.fbanner .ft{font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.fbanner .fv{font-size:40px;font-weight:800;color:var(--ink);line-height:1.15;margin:4px 0 2px}
.fbanner .fv span{font-size:16px;font-weight:600;color:var(--muted)}
.fbanner .fm{font-size:14px;color:#344054;margin-top:10px;font-weight:600}
.sgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px;margin:10px 0}
.scard{background:#fff;border:1px solid var(--line);border-left:5px solid #98a2b3;border-radius:12px;padding:14px 16px;box-shadow:0 1px 2px rgba(16,24,40,.05)}
.scard.ok{border-left-color:var(--ok)}.scard.bad{border-left-color:var(--bad)}.scard.warn{border-left-color:var(--warn)}
.shead{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
.scode{font-weight:800;color:var(--ink);font-size:14px;word-break:break-all}
.sbadge{font-size:12px;font-weight:700;padding:3px 10px;border-radius:99px;background:#f2f4f7;color:#475467;white-space:nowrap}
.sbadge.ok{background:#ecfdf3;color:#067647}.sbadge.bad{background:#fef3f2;color:#b42318}.sbadge.warn{background:#fffaeb;color:#b54708}
.saddr{font-size:12px;color:var(--muted);margin-top:4px}
.schips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.sc{font-size:12px;font-weight:600;padding:4px 9px;border-radius:8px;background:#f2f4f7;color:#475467}
.sc.ok{background:#ecfdf3;color:#067647}.sc.bad{background:#fef3f2;color:#b42318}.sc.warn{background:#fffaeb;color:#b54708}
.splus{font-size:12px;color:#475467;margin-top:8px}
.smiss{font-size:12.5px;color:#b42318;margin-top:8px;font-weight:600}.smiss.ok{color:#067647}
.sother{font-size:12px;color:var(--muted);margin-top:6px}
@keyframes ring{0%,100%{box-shadow:0 0 0 0 rgba(217,45,32,.55)}50%{box-shadow:0 0 0 12px rgba(217,45,32,0)}}
</style>
""", unsafe_allow_html=True)


# =====================================================================
# Helpers
# =====================================================================
def norm(v):
    if pd.isna(v):
        return ""
    s = str(v).replace("\u200b", "").replace("\ufeff", "").replace("\xa0", " ").strip().lower()
    s = s.replace("đ", "d")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


def norm_code(v):
    return "" if pd.isna(v) else re.sub(r"\s+", "", str(v)).upper()


def digits(v):
    return "" if pd.isna(v) else re.sub(r"\D", "", str(v)).lstrip("0")


def rounded_score(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else int(math.floor(f + 0.5))


def eval_pct(p, thr):
    r = rounded_score(p)
    if r is None:
        return "CHƯA CÓ ĐIỂM"
    return "ĐẠT" if r >= thr else f"CHƯA ĐẠT (<{thr}%) – TRẢ BÀI ĐỢT 2"


LEAD_KEYS = {"canh": "Ngô Tuấn Cảnh", "nam": "Vũ Hoài Nam", "nghia": "Trần Trung Nghĩa",
             "tien": "Đỗ Quang Tiến", "huy": "Giang Văn Huy"}


def canon_leader(v):
    s = norm(v)
    if not s or s == "nan":
        return ""
    return LEAD_KEYS.get(s.split()[-1], str(v).strip())


DONE_QC = {"done", "pass", "passed", "approved", "approve", "ok", "dat", "qc done", "completed",
           "hoan thanh", "da duyet"}
DONE_FIELD = {"done", "hoan thanh", "completed", "complete", "finished"}


def classify_qc(v):
    s = norm(v)
    if not s or s in {"nan", "none"}:
        return "NONE"
    if any(k in s for k in ["rework", "ycbs", "yeu cau bo sung", "bo sung", "thieu"]):
        return "REWORK"
    if any(k in s for k in ["reject", "refus", "fail", "khong dat", "invalid", "tu choi"]):
        return "REJECT"
    if "pending_review" in s or "pending review" in s:
        return "PENDING_REVIEW"
    if any(k in s for k in ["pending", "cho duyet", "waiting"]):
        return "PENDING"
    return "DONE" if s in DONE_QC else "UNKNOWN"


QC_LABEL = {"DONE": "Đã duyệt", "REJECT": "Từ chối", "REWORK": "Yêu cầu bổ sung", "PENDING": "Chờ duyệt",
            "PENDING_REVIEW": "Chờ duyệt", "NONE": "Chưa QC", "UNKNOWN": "Khác"}


def text_filter(df, cols, q):
    q = norm(q)
    if not q or df is None or df.empty:
        return df
    mask = pd.Series(False, index=df.index)
    for c in cols:
        if c in df.columns:
            mask |= df[c].apply(norm).str.contains(q, regex=False)
    return df[mask]


def pct(a, b):
    return round(100 * a / b, 1) if b else np.nan


def _cell_style(v):
    if not isinstance(v, str):
        return ""
    if v.startswith("✅") or v == "ĐẠT":
        return "background-color:#ecfdf3;color:#067647;font-weight:600"
    if v.startswith("❌") or v.startswith("CHƯA ĐẠT") or v.startswith("🚨"):
        return "background-color:#fef3f2;color:#b42318;font-weight:600"
    if v.startswith("🕓"):
        return "background-color:#fffaeb;color:#b54708;font-weight:600"
    if v.startswith("⏳") or v.startswith("— Chưa"):
        return "background-color:#f2f4f7;color:#475467"
    return ""


def show_df(df, height=None, **kw):
    args = {"hide_index": True, **STRETCH, **kw}
    if height:
        args["height"] = height
    data = df
    try:
        if 0 < len(df) <= 2000 and any(df[c].dtype == object or str(df[c].dtype).startswith("str") for c in df.columns):
            sty = df.style
            data = (sty.map if hasattr(sty, "map") else sty.applymap)(_cell_style)
    except Exception:
        data = df
    try:
        st.dataframe(data, **args)
    except Exception:  # Styler lỗi -> hiện bảng thường
        st.dataframe(df, **args)


PALETTE = ["#2e90fa", "#7a5af8", "#f79009", "#06aed4", "#12b76a", "#ee46bc", "#667085", "#d70018"]
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = PALETTE


SERIES_COLORS = {
    "Bị từ chối": "#f04438", "Hoàn thành (Field + QC)": "#12b76a", "Hoàn thành": "#12b76a", "Hoàn tất": "#12b76a",
    "Field xong": "#2e90fa", "QC duyệt xong": "#7a5af8", "Tổng plan": "#98a2b3", "Giao": "#98a2b3",
    "Đã đủ": "#12b76a", "Chưa đủ": "#f04438", "Tổng": "#98a2b3",
    "Đã duyệt": "#12b76a", "Từ chối": "#f04438", "Chưa chấm": "#f79009",
    "CPS (cửa hàng)": "#b2ddff", "CPS hoàn thành": "#2e90fa", "DTV (cửa hàng)": "#d9d6fe", "DTV hoàn thành": "#7a5af8",
    "Mystery (giao)": "#fedf89", "Mystery hoàn tất": "#f79009",
    "% CPS": "#2e90fa", "% DTV": "#7a5af8", "% Mystery": "#f79009", "% Plus": "#06aed4",
    "% KPI tổng (CPS+DTV+Mystery)": "#d70018", **STATUS_COLOR,
}


def _wrap_label(v):
    if isinstance(v, str) and len(v.split()) >= 3 and "<br>" not in v:
        w = v.split()
        return " ".join(w[:2]) + "<br>" + " ".join(w[2:])
    return v


def show_chart(fig):
    fig.update_layout(
        font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=13, color="#344054"),
        title=dict(font=dict(size=15, color="#101828"), x=0.01, xanchor="left"),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5, title_text=""),
        margin=dict(l=16, r=16, t=56, b=76))
    fig.update_xaxes(showgrid=False, linecolor="#d0d5dd", title_text=None, tickangle=0)
    fig.update_yaxes(gridcolor="#eaecf0", zeroline=False)
    for tr in fig.data:
        if tr.type == "bar":
            if tr.name in SERIES_COLORS:
                tr.marker.color = SERIES_COLORS[tr.name]
            if tr.x is not None and len(tr.x) and isinstance(tr.x[0], str):
                tr.x = [_wrap_label(v) for v in tr.x]
    st.plotly_chart(fig, **STRETCH)


def tone(p):
    if p is None or pd.isna(p):
        return "#98a2b3"
    return "#12b76a" if p >= 80 else "#f79009" if p >= 50 else "#f04438"


def section(title, sub=""):
    st.markdown(f'<div class="sec"><div class="t">{title}</div>' + (f'<div class="s">{sub}</div>' if sub else "") +
                '</div>', unsafe_allow_html=True)


def kpi_card(label, value, sub="", p=None, bad=False):
    bar = ""
    if p is not None and not pd.isna(p):
        c = tone(p)
        bar = (f'<div class="kbar"><span style="width:{min(max(p, 0), 100)}%;background:{c}"></span></div>'
               f'<div class="kpct" style="color:{c}">{p:.0f}%</div>')
    return (f'<div class="kpi{" bad" if bad else ""}"><div class="kl">{html.escape(str(label))}</div>'
            f'<div class="kv">{value}</div><div class="ks">{html.escape(str(sub))}</div>{bar}</div>')


def lead_cards(ls):
    cards = []
    for _, r in ls.iterrows():
        overall = r["% KPI tổng (CPS+DTV+Mystery)"]
        c = tone(overall)
        rows = ""
        for name, done, tot, p in [("CPS", r["CPS hoàn thành"], r["CPS (cửa hàng)"], r["% CPS"]),
                                   ("DTV", r["DTV hoàn thành"], r["DTV (cửa hàng)"], r["% DTV"]),
                                   ("Mystery", r["Mystery hoàn tất"], r["Mystery (giao)"], r["% Mystery"]),
                                   ("Plus", r["Plus hoàn thành"], r["Plus (plan)"], r["% Plus"])]:
            if not tot:
                continue
            rows += (f'<div class="mrow"><span class="mn">{name}</span><div class="mbar"><span style="width:{min(max(p, 0), 100):.0f}%;'
                     f'background:{tone(p)}"></span></div><span class="mv">{int(done)}/{int(tot)}</span></div>')
        big = "—" if pd.isna(overall) else f"{overall:.0f}%"
        cards.append(f'<div class="lcard"><div class="lname">{html.escape(str(r["Lead"]))}</div>'
                     f'<div class="lpct" style="color:{c}">{big}</div><div class="lsub">KPI tổng (CPS + DTV + Mystery)</div>{rows}</div>')
    st.markdown('<div class="lead-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)


def chip(text, kind="dark"):
    return f'<span class="chip {kind}">{html.escape(str(text))}</span>'


def welcome(label):
    st.markdown(f"""<div class="welcome"><div class="wt">Chưa có dữ liệu {label}</div>
<div class="ws">Nạp file raw data để bắt đầu theo dõi tiến độ.</div>
<ol><li>Mở thanh bên trái (biểu tượng ›› ở góc trên nếu đang ẩn).</li>
<li>Ở mục <b>Dữ liệu</b>, chọn file Excel xuất từ hệ thống audit cho {label}.</li>
<li>App tự lưu file, lần sau mở lại sẽ thấy ngay dữ liệu.</li></ol></div>""", unsafe_allow_html=True)


def bar_chart(df, x, ys, title, barmode="group", **kw):
    fig = px.bar(df, x=x, y=ys, barmode=barmode, title=title, text_auto=True, **kw)
    fig.update_traces(textangle=0)
    fig.update_yaxes(title_text="Số lượng")
    show_chart(fig)


def pie_chart(names, values, title, colors=None):
    fig = px.pie(names=names, values=values, title=title, hole=0.45,
                 color=names, color_discrete_map=colors or {})
    fig.update_traces(texttemplate="%{value}<br>%{percent:.0%}", textposition="inside")
    fig.update_layout(height=380)
    show_chart(fig)


PCT_CFG = lambda cols: {c: st.column_config.ProgressColumn(c, min_value=0, max_value=100, format="%.0f%%")
                        for c in cols}


# =====================================================================
# Store master (Mã cửa hàng -> địa chỉ, Lead, cờ Mystery / L2)
# =====================================================================
def find_file(name):
    """Tìm file dữ liệu cạnh app.py (hoặc thư mục con) để không bị lệch vị trí khi upload GitHub."""
    base = Path(__file__).parent
    for p in (base / name, Path.cwd() / name):
        if p.exists():
            return p
    stem, ext = name.rsplit(".", 1)
    try:
        hits = [h for h in base.rglob(f"{stem}*.{ext}") if ".git" not in h.parts and "data" not in h.parts]
        return sorted(hits, key=lambda h: len(h.parts))[0] if hits else None
    except OSError:
        return None


DATA_DIR = Path(__file__).parent / "data"
STORE_FILE = find_file("store_master.csv")
_EMBEDDED_STORES = """
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
4jQ53eQmAujPv9oczv8DQLcHxQp9AAA=
"""
STORE_COLS = ["Mã cửa hàng", "Hệ thống", "Miền", "Địa chỉ cửa hàng", "Lead", "Mystery", "L2"]


def _empty_stores():
    return pd.DataFrame(columns=STORE_COLS)


@st.cache_data(show_spinner=False)
def parse_store_master(file_bytes, name=""):
    try:
        if str(name).lower().endswith((".xlsx", ".xls")):
            raw = pd.read_excel(io.BytesIO(file_bytes), header=None, dtype=str)
        else:
            raw = pd.read_csv(io.BytesIO(file_bytes), header=None, dtype=str)
    except Exception:
        return _empty_stores()
    hdr = next((i for i in range(min(10, len(raw)))
                if {"don vi", "ma cua hang"} & {norm(c) for c in raw.iloc[i]}), None)
    if hdr is None:
        return _empty_stores()
    cols = [norm(c) for c in raw.iloc[hdr]]
    seen, uniq = {}, []
    for c in cols:
        seen[c] = seen.get(c, 0) + 1
        uniq.append(c if seen[c] == 1 else f"{c}__{seen[c]}")
    raw.columns = uniq
    raw = raw.iloc[hdr + 1:]

    def pick(pred):
        return next((c for c in raw.columns if c and pred(c)), None)

    c_code = pick(lambda c: c in ("don vi", "ma cua hang"))
    if c_code is None:
        return _empty_stores()
    c_addr = pick(lambda c: c.startswith("dia chi"))
    c_lead = pick(lambda c: c == "lead")
    c_sys = pick(lambda c: c == "he thong")
    c_reg = pick(lambda c: c == "mien")
    c_mys = pick(lambda c: c == "mystery")
    c_l2 = pick(lambda c: c == "l2")

    def col(c, default=""):
        return raw[c].fillna("").astype(str).str.strip() if c else default

    out = pd.DataFrame({
        "Mã cửa hàng": raw[c_code].apply(norm_code),
        "Hệ thống": col(c_sys).astype(str).str.upper() if c_sys else "",
        "Miền": col(c_reg), "Địa chỉ cửa hàng": col(c_addr),
        "Lead": col(c_lead).apply(canon_leader) if c_lead else "",
        "Mystery": col(c_mys) if c_mys else np.nan,
        "L2": col(c_l2) if c_l2 else np.nan,
    })
    out = out[out["Mã cửa hàng"].ne("")].drop_duplicates("Mã cửa hàng").reset_index(drop=True)
    miss_sys = out["Hệ thống"].eq("")
    out.loc[miss_sys, "Hệ thống"] = out.loc[miss_sys, "Mã cửa hàng"].str.split("-").str[0]
    return out


def store_signature():
    """Đổi khi store_master.csv được cập nhật -> cache tự làm mới."""
    try:
        stt = STORE_FILE.stat()
        return f"{stt.st_mtime_ns}-{stt.st_size}"
    except (OSError, AttributeError):
        return "missing"


@st.cache_data(show_spinner=False)
def load_default_stores(sig=""):
    """Ưu tiên store_master.csv trên GitHub (nếu đủ cột Mystery/L2); không có hoặc là bản cũ thì dùng bản tích hợp sẵn."""
    df = _empty_stores()
    if STORE_FILE is not None and STORE_FILE.exists():
        df = parse_store_master(STORE_FILE.read_bytes(), STORE_FILE.name)
        if not df.empty and bool((df["Mystery"] == "Có").any()):
            return df, f"file {STORE_FILE.name}"
    emb = parse_store_master(gzip.decompress(base64.b64decode("".join(_EMBEDDED_STORES.split()))), "store_master.csv")
    return emb, "bản tích hợp sẵn"


def merge_flags(stores, default):
    """Bảng nạp thủ công thiếu cờ Mystery / L2 -> lấy từ bảng mặc định."""
    s = stores.copy()
    flags = default.set_index("Mã cửa hàng")[["Mystery", "L2"]] if not default.empty else None
    for c in ["Mystery", "L2"]:
        if s[c].isna().all():
            s[c] = s["Mã cửa hàng"].map(flags[c]) if flags is not None else "Không"
        s[c] = s[c].fillna("Không")
    return s


# =====================================================================
# Raw data loading
# =====================================================================
BASE_COLS = ["Tên Plan", "Chấm", "Hệ thống", "Mã cửa hàng", "Tên Leader", "Tên nhân viên thực hiện",
             "Ngày update", "Status Plan", "QC Status", "Ngày thực hiện", "Hạng mục", "QC note", "Tên Auditor", "QC Manager Check"]
PLUS_COLS = BASE_COLS + ["MSNV", "Mã câu hỏi", "Câu trả lời", "Trả lời ngay", "Trả lời Phụ",
                         "Trả lời có tài liệu", "Có xem tài liệu", "Thang điểm", "Thực đạt"]
USECOLS = {"Mystery Audit": BASE_COLS, "Trade Audit": BASE_COLS, "Trade Audit Plus": PLUS_COLS}


def canon_sheet(name):
    n = norm(name)
    if "mystery" in n:
        return "Mystery Audit"
    if "trade" in n and "plus" in n:
        return "Trade Audit Plus"
    return "Trade Audit" if "trade" in n else None


NOTE_WORDS = ("note", "ghi chu", "ly do", "nhan xet", "feedback", "comment", "reject")


def is_note_col(name):
    """Cột có vẻ chứa ghi chú / lý do (để không bỏ sót ghi chú QC nằm ở cột tên khác)."""
    n = norm(name)
    return n != "qc note" and "khong co diem" not in n and any(w in n for w in NOTE_WORDS)


@st.cache_data(show_spinner="Đang đọc file Excel...", max_entries=3)
def load_report(file_bytes, ver=""):
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    out = {}
    for s in xls.sheet_names:
        key = canon_sheet(s)
        if key is None or key in out:
            continue
        want = {norm(c): c for c in USECOLS[key]}
        df = pd.read_excel(xls, sheet_name=s, usecols=lambda c, w=want: norm(c) in w or is_note_col(c))
        df.columns = [want.get(norm(c), c) for c in df.columns]
        out[key] = df
    return out


def round_number(v):
    m = re.search(r"(\d+)", norm(v))
    return int(m.group(1)) if m else None


def filter_round(df, label):
    if df is None or df.empty or "Chấm" not in df.columns:
        return pd.DataFrame()
    return df[df["Chấm"].apply(round_number).eq(round_number(label))].copy()


def available_rounds(sheets):
    vals = set()
    for df in sheets.values():
        if "Chấm" in df.columns:
            vals |= {str(v) for v in df["Chấm"].dropna().unique()}
    return sorted(vals)


def join_notes(s):
    seen = []
    for v in s.astype(str):
        v = v.strip()
        if v and norm(v) not in {"nan", "none"} and v not in seen:
            seen.append(v)
    return " | ".join(seen)[:400]


def _notes_by_plan(x, col):
    nn = x[x[col].notna() & x[col].astype(str).str.strip().ne("")]
    if nn.empty:
        return pd.Series(dtype=str)
    return nn.groupby("Tên Plan")[col].agg(join_notes)


def plan_level(df):
    """1 dòng / plan (dòng mới nhất) + gộp ghi chú QC của plan (cột 'QC note'; nếu trống thì lấy cột ghi chú khác)."""
    if df is None or df.empty or "Tên Plan" not in df.columns:
        return pd.DataFrame()
    x = df[df["Tên Plan"].notna()].copy()
    x["Tên Plan"] = x["Tên Plan"].astype(str).str.strip()
    x = x[x["Tên Plan"].ne("")]
    performed = (x["Ngày thực hiện"].notna().groupby(x["Tên Plan"]).any()
                 if "Ngày thực hiện" in x.columns else pd.Series(dtype=bool))
    th_date = (pd.to_datetime(x["Ngày thực hiện"], errors="coerce", dayfirst=True).groupby(x["Tên Plan"]).max()
               if "Ngày thực hiện" in x.columns else pd.Series(dtype="datetime64[ns]"))
    notes = _notes_by_plan(x, "QC note") if "QC note" in x.columns else pd.Series(dtype=str)
    others = {c: _notes_by_plan(x, c) for c in x.columns if c != "QC note" and is_note_col(c)}
    if "Ngày update" in x.columns:
        x["_dt"] = pd.to_datetime(x["Ngày update"], errors="coerce", dayfirst=True)
        x = x.sort_values("_dt", na_position="first", kind="stable").drop(columns="_dt")
    x = x.drop_duplicates("Tên Plan", keep="last").reset_index(drop=True)
    final = x["Tên Plan"].map(notes).fillna("")
    for c, ser in others.items():  # ghi chú từ cột khác, gắn tên cột để biết nguồn
        extra = x["Tên Plan"].map(ser).fillna("")
        final = final.where(final.ne("") | extra.eq(""), "[" + c + "] " + extra)
    x["Ghi chú QC"] = final
    x["Đã thực hiện"] = x["Tên Plan"].map(performed.to_dict()).fillna(False).astype(bool)
    x["Ngày TH"] = pd.to_datetime(x["Tên Plan"].map(th_date.to_dict()), errors="coerce")
    return x


# =====================================================================
# Plan table (một bảng thống nhất: Trade / Plus / Mystery)
# =====================================================================
def system_of(code, ht, plan="", kw="CAMPUS"):
    h = norm(ht).upper()
    key = norm(kw).upper() or "CAMPUS"
    if key in f"{code} {h} {norm(plan).upper()}":
        return "CAMPUS"
    if code.startswith("DTV") or h == "DTV":
        return "DTV"
    if code.startswith("CPS") or h == "CPS":
        return "CPS"
    return h or "KHÁC"


def mystery_scn(plan):
    t = norm(plan)
    if "macbook" in t or "ipad" in t:
        return "MACBOOK-IPAD"
    if "iphone cu" in t or "likenew" in t:
        return "IPHONE CŨ"
    if "iphone 17" in t or "17 pro max" in t:
        return "IPHONE 17 PRO MAX"
    if "android" in t:
        return "ANDROID"
    if "laptop" in t:
        return "LAPTOP"
    return "Chưa rõ"


def classify_item(kind, plan, hm):
    hm_s = "" if pd.isna(hm) else str(hm).strip()
    text = norm(f"{hm_s} {plan}")
    if kind == "Plus":
        # số Plus lấy từ TÊN PLAN (…_Trade Audit Plus 3). Cột Hạng mục thật ghi "Plus 10/2026" nên không dùng trước.
        nums = re.findall(r"plus\s*(\d+)(?!\d|/)", norm(plan)) or re.findall(r"plus\s*(\d+)(?!\d|/)", norm(hm_s))
        return f"Plus {nums[-1]}" if nums else "Plus ?"
    if kind == "Mystery":
        return hm_s if hm_s else mystery_scn(plan)
    if "dtv" in text:
        return "Trade Audit DTV"
    if "demo" in text:
        return "Demo"
    if re.search(r"tu may|tumay|\btu\b", text):
        return "Tủ máy"
    if re.search(r"vach|\bdao\b", text):
        return "Vách/Đảo"
    if "cellphones" in text:
        return "CellphoneS"
    return hm_s or "Trade khác"


P_COLS = ["Nghiệp vụ", "Tên Plan", "store", "Hệ thống", "Hạng mục", "Lead", "Địa chỉ", "QC", "Field done",
          "QC done", "Hoàn thành", "Bị từ chối", "_st", "Ghi chú QC", "Ngày update", "Field name",
          "lead_raw", "status_raw", "auditor", "QM", "Chờ QM", "th_date"]


def build_plans(sheets, label, stores, campus_kw="CAMPUS"):
    lead_map = stores.set_index("Mã cửa hàng")["Lead"].to_dict() if not stores.empty else {}
    addr_map = stores.set_index("Mã cửa hàng")["Địa chỉ cửa hàng"].to_dict() if not stores.empty else {}
    frames = []
    for key, kind in [("Trade Audit", "Trade"), ("Trade Audit Plus", "Plus"), ("Mystery Audit", "Mystery")]:
        df = sheets.get(key)
        if df is None or df.empty:
            continue
        if kind != "Mystery":  # Mystery là luồng riêng, không lọc theo L1/L2
            df = filter_round(df, label)
        p = plan_level(df)
        if p.empty:
            continue

        def g(c, p=p):
            return p[c] if c in p.columns else pd.Series("", index=p.index)

        out = pd.DataFrame({
            "Nghiệp vụ": kind, "Tên Plan": p["Tên Plan"],
            "store": g("Mã cửa hàng").apply(norm_code),
            "lead_raw": g("Tên Leader").apply(canon_leader),
            "status_raw": g("Status Plan"),
            "performed": g("Đã thực hiện").astype(bool) if "Đã thực hiện" in p.columns else False,
            "auditor": g("Tên Auditor").fillna("").astype(str).str.strip(),
            "qm_raw": g("QC Manager Check"),
            "th_date": pd.to_datetime(g("Ngày TH"), errors="coerce") if "Ngày TH" in p.columns else pd.NaT,
            "Ghi chú QC": g("Ghi chú QC").fillna(""),
            "Ngày update": pd.to_datetime(g("Ngày update"), errors="coerce", dayfirst=True),
            "Field name": g("Tên nhân viên thực hiện"),
            "QC": g("QC Status").apply(classify_qc),
        })
        out["Hệ thống"] = [system_of(c, h, pl, campus_kw) for c, h, pl in zip(out["store"], g("Hệ thống"), out["Tên Plan"])]
        out["Hạng mục"] = [classify_item(kind, pl, hm) for pl, hm in zip(out["Tên Plan"], g("Hạng mục"))]
        frames.append(out)
    if not frames:
        return pd.DataFrame(columns=P_COLS)
    P = pd.concat(frames, ignore_index=True)
    # Field xong khi: Status Plan = done, hoặc dạng n/n (5/5); riêng Plus, Status Plan chỉ là tiến độ "k/5"
    # nên Field xong khi plan đã có ngày thực hiện (đã được chấm).
    st_norm = P["status_raw"].apply(norm)
    frac = st_norm.str.extract(r"^(\d+)\s*/\s*(\d+)$")
    P["Field done"] = (st_norm.isin(DONE_FIELD) | (frac[0].notna() & frac[0].eq(frac[1]))
                       | ((P["Nghiệp vụ"] == "Plus") & P["performed"].astype(bool)))
    P["QC done"] = P["QC"].eq("DONE")
    P["Hoàn thành"] = P["Field done"] & P["QC done"]
    P["Bị từ chối"] = P["QC"].isin(["REJECT", "REWORK"])
    P["QM"] = P["qm_raw"].apply(classify_qc)
    P["Chờ QM"] = P["QC done"] & P["QM"].isin(["PENDING", "PENDING_REVIEW", "NONE"])  # QC viên đã duyệt, Manager chưa duyệt
    P["_st"] = np.select([P["Hoàn thành"], P["Bị từ chối"], P["Field done"]],
                         ["DONE", "REJECT", "WAIT_QC"], "NOT_FIELD")
    lead = P["store"].map(lead_map)
    P["Lead"] = lead.where(lead.notna() & lead.ne(""), P["lead_raw"]).replace("", "Chưa gán")
    P["Địa chỉ"] = P["store"].map(addr_map).fillna("")
    return P


def build_interviews(sheets, label, stores, default_max):
    plus = filter_round(sheets.get("Trade Audit Plus", pd.DataFrame()), label)
    if plus.empty or not {"Mã câu hỏi", "Tên Plan"}.issubset(plus.columns):
        return pd.DataFrame()
    x = plus[plus["Tên Plan"].notna()].copy()
    x["Tên Plan"] = x["Tên Plan"].astype(str).str.strip()
    plan = x["Tên Plan"]

    def boolish(v):
        if pd.isna(v):
            return False
        if isinstance(v, (bool, numbers.Number)):
            return bool(v)
        return norm(v) in {"true", "1", "yes", "y", "x", "co", "ok"}

    answered = pd.Series(False, index=x.index)
    for c in ["Trả lời ngay", "Trả lời Phụ", "Trả lời có tài liệu", "Có xem tài liệu"]:
        if c in x.columns:
            answered = answered | x[c].apply(boolish)
    pts = pd.to_numeric(x["Thang điểm"], errors="coerce").fillna(0) if "Thang điểm" in x.columns else None
    thuc = pd.to_numeric(x["Thực đạt"], errors="coerce") if "Thực đạt" in x.columns else None
    if thuc is not None and thuc.notna().any():
        score = thuc.groupby(plan).sum(min_count=1)
    elif pts is not None:
        score = pts.where(answered, 0).groupby(plan).sum()
    else:
        score = pd.Series(dtype=float)
    maxs = pts.groupby(plan).sum() if pts is not None else pd.Series(dtype=float)

    tt1 = x[x["Mã câu hỏi"].astype(str).str.strip().str.upper().eq("TT1")].copy()
    if tt1.empty:
        return pd.DataFrame()

    def col(n):
        return tt1[n].fillna("").astype(str).str.strip() if n in tt1.columns else ""

    lead_map = stores.set_index("Mã cửa hàng")["Lead"].to_dict() if not stores.empty else {}
    out = pd.DataFrame({
        "plan_name": tt1["Tên Plan"],
        "store_code": tt1["Mã cửa hàng"].apply(norm_code) if "Mã cửa hàng" in tt1.columns else "",
        "lead_raw": tt1["Tên Leader"].apply(canon_leader) if "Tên Leader" in tt1.columns else "",
        "field_name": col("Tên nhân viên thực hiện"), "employee_id": col("MSNV"),
        "employee_name": col("Câu trả lời"),
        "qc_status": tt1["QC Status"].apply(classify_qc) if "QC Status" in tt1.columns else "NONE",
        "updated_at": pd.to_datetime(tt1["Ngày update"], errors="coerce", dayfirst=True)
        if "Ngày update" in tt1.columns else pd.NaT,
    })
    # Field xong: Status Plan = done / n/n, hoặc plan đã có ngày thực hiện (Plus chỉ ghi tiến độ dạng "k/5")
    st_n = tt1["Status Plan"].apply(norm) if "Status Plan" in tt1.columns else pd.Series("", index=tt1.index)
    fr = st_n.str.extract(r"^(\d+)\s*/\s*(\d+)$")
    performed = tt1["Ngày thực hiện"].notna() if "Ngày thực hiện" in tt1.columns else pd.Series(False, index=tt1.index)
    out["field_done"] = (st_n.isin(DONE_FIELD) | (fr[0].notna() & fr[0].eq(fr[1])) | performed).values
    out["plus_item"] = [classify_item("Plus", pl, "") for pl in out["plan_name"]]
    lead = out["store_code"].map(lead_map)
    out["Lead"] = lead.where(lead.notna() & lead.ne(""), out["lead_raw"]).replace("", "Chưa gán")
    out["score"] = out["plan_name"].map(score)
    mx = out["plan_name"].map(maxs)
    out["max_score"] = mx.where(mx.notna() & (mx > 0), float(default_max))
    out["pct"] = out["score"] / out["max_score"] * 100
    out = out[out["employee_name"].apply(norm).ne("")]
    out = out.sort_values("updated_at", na_position="first", kind="stable")
    return out.drop_duplicates("plan_name", keep="last").reset_index(drop=True)


@st.cache_data(show_spinner="Đang tính toán...", max_entries=6)
def compute_all(file_bytes, label, stores, default_max, campus_kw, ver):
    sheets = load_report(file_bytes, ver)
    return {"P": build_plans(sheets, label, stores, campus_kw),
            "IV": build_interviews(sheets, label, stores, default_max),
            "rounds": available_rounds(sheets), "sheets": list(sheets)}


# =====================================================================
# Analytics
# =====================================================================
def pick_best(df):
    """Mỗi (cửa hàng, hạng mục) chỉ lấy 1 plan: ưu tiên đã hoàn thành, sau đó mới nhất."""
    if df.empty:
        return df
    d = df.copy()
    d["_dt"] = pd.to_datetime(d["Ngày update"], errors="coerce")
    d = d.sort_values(["Hoàn thành", "_dt"], na_position="first", kind="stable")
    return d.drop_duplicates(["store", "Hạng mục"], keep="last")


def store_matrix(P, stores, system, items, only_l2=False):
    base_cols = ["Lead", "Mã cửa hàng", "Địa chỉ cửa hàng"] + items + \
                ["Số HM đạt", "Thiếu hạng mục", "Ghi chú", "_done"]
    s = stores[stores["Hệ thống"] == system] if not stores.empty else stores
    if only_l2 and not s.empty and (s["L2"] == "Có").any():
        s = s[s["L2"] == "Có"]
    t = P[(P["Nghiệp vụ"] == "Trade") & (P["Hệ thống"] == system)]
    best = pick_best(t)
    key = best.set_index(["store", "Hạng mục"]) if not best.empty else None
    st_map = key["_st"].to_dict() if key is not None else {}
    note_map = key["Ghi chú QC"].to_dict() if key is not None else {}
    known = set(stores["Mã cửa hàng"]) if not stores.empty else set()
    info = stores.set_index("Mã cửa hàng") if not stores.empty else None
    lead_raw = t.drop_duplicates("store").set_index("store")["Lead"].to_dict()
    codes = list(s["Mã cửa hàng"]) + sorted(set(t["store"]) - known)
    rows = []
    for code in codes:
        in_m = info is not None and code in info.index
        row = {"Lead": info.at[code, "Lead"] if in_m else lead_raw.get(code, "Chưa gán"),
               "Mã cửa hàng": code, "Địa chỉ cửa hàng": info.at[code, "Địa chỉ cửa hàng"] if in_m else ""}
        missing, notes = [], []
        for it in items:
            stt = st_map.get((code, it), "NONE")
            row[it] = STATUS_LABEL[stt]
            if stt != "DONE":
                missing.append(it)
                if stt == "REJECT":
                    notes.append(f"{it}: bị từ chối – {note_map.get((code, it), '') or 'chưa có ghi chú QC'}")
                else:
                    notes.append(f"{it}: {REASON[stt]}")
        row["Số HM đạt"] = f"{len(items) - len(missing)}/{len(items)}"
        row["Thiếu hạng mục"] = ", ".join(missing)
        row["Ghi chú"] = " | ".join(notes)
        row["_done"] = not missing
        rows.append(row)
    return pd.DataFrame(rows, columns=base_cols) if rows else pd.DataFrame(columns=base_cols)


def _group_matrix(t, codes, info, label_fn=None):
    """Tổng hợp theo cửa hàng cho Mystery / CAMPUS."""
    agg = {}
    for code, g in t.groupby("store"):
        rej = g[g["Bị từ chối"]]
        agg[code] = {
            "plans": len(g), "done": int(g["Hoàn thành"].sum()), "field": int(g["Field done"].sum()),
            "rej": len(rej), "lead": g["Lead"].iloc[0],
            "note": " | ".join(f"{r['Hạng mục']}: {r['Ghi chú QC'] or 'chưa có ghi chú QC'}"
                               for _, r in rej.iterrows()),
        }
    rows = []
    for code in codes:
        a = agg.get(code, {"plans": 0, "done": 0, "field": 0, "rej": 0, "note": "", "lead": ""})
        in_m = info is not None and code in info.index
        lead = info.at[code, "Lead"] if in_m else (a["lead"] or "Chưa gán")
        if a["plans"] == 0:
            stt, note = "— Chưa có plan", "Chưa có plan trong raw data"
        elif a["done"] == a["plans"]:
            stt, note = "✅ Hoàn tất", ""
        elif a["rej"] > 0:
            stt, note = "❌ Có plan bị từ chối", a["note"]
        else:
            stt, note = "🕓 Đang thực hiện", f"{a['plans'] - a['done']}/{a['plans']} plan chưa xong (Field xong {a['field']}/{a['plans']})"
        rows.append({"Lead": lead, "Mã cửa hàng": code,
                     "Địa chỉ cửa hàng": info.at[code, "Địa chỉ cửa hàng"] if in_m else "",
                     "Số plan": a["plans"], "Plan hoàn thành": a["done"], "Plan bị từ chối": a["rej"],
                     "Trạng thái": stt, "Ghi chú": note, "_done": stt == "✅ Hoàn tất"})
    cols = ["Lead", "Mã cửa hàng", "Địa chỉ cửa hàng", "Số plan", "Plan hoàn thành", "Plan bị từ chối",
            "Trạng thái", "Ghi chú", "_done"]
    return pd.DataFrame(rows, columns=cols)


def mystery_matrix(P, stores):
    t = P[(P["Nghiệp vụ"] == "Mystery") & (P["Hệ thống"] != "CAMPUS")]
    has_flag = (not stores.empty) and bool((stores["Mystery"] == "Có").any())
    info = stores.set_index("Mã cửa hàng") if not stores.empty else None
    if has_flag:
        tgt = list(stores.loc[stores["Mystery"] == "Có", "Mã cửa hàng"])
        extra = sorted(set(t["store"]) - set(tgt))
        codes = tgt + extra
    else:  # chưa có cờ Mystery -> coi mọi cửa hàng có plan Mystery là cửa hàng được giao
        extra, codes = [], sorted(set(t["store"]))
    m = _group_matrix(t, codes, info)
    m["Ngoài DS giao"] = m["Mã cửa hàng"].isin(extra)
    return m


def campus_matrix(P):
    t = P[P["Hệ thống"] == "CAMPUS"]
    return _group_matrix(t, sorted(t["store"].unique()), None)


def lead_summary(P, stores, cps_m, dtv_m, my_m):
    names = (set(stores["Lead"]) if not stores.empty else set()) | set(cps_m["Lead"]) | \
        set(dtv_m["Lead"]) | set(my_m["Lead"]) | set(P["Lead"])
    leads = sorted(l for l in names if l)
    plus = P[P["Nghiệp vụ"] == "Plus"]
    rows = []
    for ld in leads:
        c, d, m, p = (cps_m[cps_m["Lead"] == ld], dtv_m[dtv_m["Lead"] == ld],
                      my_m[(my_m["Lead"] == ld) & ~my_m["Ngoài DS giao"]], plus[plus["Lead"] == ld])
        cd, dd, md, pd_ = int(c["_done"].sum()), int(d["_done"].sum()), int(m["_done"].sum()), int(p["Hoàn thành"].sum())
        tot, tdone = len(c) + len(d) + len(m), cd + dd + md
        rows.append({"Lead": ld, "CPS (cửa hàng)": len(c), "CPS hoàn thành": cd, "% CPS": pct(cd, len(c)),
                     "DTV (cửa hàng)": len(d), "DTV hoàn thành": dd, "% DTV": pct(dd, len(d)),
                     "Mystery (giao)": len(m), "Mystery hoàn tất": md, "% Mystery": pct(md, len(m)),
                     "Plus (plan)": len(p), "Plus hoàn thành": pd_, "% Plus": pct(pd_, len(p)),
                     "% KPI tổng (CPS+DTV+Mystery)": pct(tdone, tot)})
    return pd.DataFrame(rows)


def to_excel_multi(sheets):
    """Xuất nhiều sheet cùng định dạng (tiêu đề đỏ, tự giãn cột, ngắt dòng cho cột dài, lọc, cố định dòng đầu)."""
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as w:
        wb = w.book
        hf = wb.add_format({"bold": True, "font_color": "white", "bg_color": "#D70018", "border": 1,
                            "align": "center", "valign": "vcenter", "text_wrap": True})
        ok = wb.add_format({"bg_color": "#D1E7DD", "font_color": "#0F5132", "bold": True})
        bad = wb.add_format({"bg_color": "#F8D7DA", "font_color": "#842029", "bold": True})
        wrap = wb.add_format({"text_wrap": True, "valign": "top"})
        for name, df in sheets.items():
            nm = str(name)[:31]
            d = df[[c for c in df.columns if not str(c).startswith("_")]]
            d.to_excel(w, index=False, sheet_name=nm)
            ws = w.sheets[nm]
            for i, n in enumerate(d.columns):
                ws.write(0, i, n, hf)
                body = int(d[n].astype(str).str.len().fillna(0).quantile(.90)) + 2 if len(d) else 12
                ws.set_column(i, i, min(max(len(str(n)) + 2, body), 60), wrap if body > 45 else None)
            last = max(len(d), 1)
            for cand in ["Kết luận", "Đánh giá", "Kết quả L2"]:
                if cand in d.columns:
                    c = d.columns.get_loc(cand)
                    ws.conditional_format(1, c, last, c, {"type": "cell", "criteria": "==", "value": '"ĐẠT"', "format": ok})
                    ws.conditional_format(1, c, last, c, {"type": "text", "criteria": "begins with", "value": "CHƯA ĐẠT", "format": bad})
            ws.freeze_panes(1, 0)
            ws.autofilter(0, 0, len(d), max(len(d.columns) - 1, 0))
    return out.getvalue()


def to_excel(df, sheet):
    return to_excel_multi({sheet: df})


def dl_button(df, sheet, fname, key):
    st.download_button(f"📥 Xuất Excel – {sheet}", data=to_excel(df, sheet), file_name=fname, key=key,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# =====================================================================
# Danh sách nhân sự -> kiểm tra đối tượng phỏng vấn Plus
# =====================================================================
STAFF_FILE = find_file("nhan_su.csv")
STAFF_COLS = ["id", "pos", "store", "status"]
DEFAULT_ALLOWED = "bán hàng, trưởng cửa hàng, quản lý cửa hàng, trợ lý cửa hàng, aio"


def norm_id(v):
    return "" if pd.isna(v) else re.sub(r"[^A-Z0-9]", "", str(v).upper())


def _pick_col(cols, names):
    return next((c for c in cols if norm(c) in names), None)


@st.cache_data(show_spinner="Đang đọc danh sách nhân sự...", max_entries=3)
def parse_staff(file_bytes, name=""):
    empty = pd.DataFrame(columns=STAFF_COLS)
    try:
        if str(name).lower().endswith((".xlsx", ".xls")):
            xls = pd.ExcelFile(io.BytesIO(file_bytes))
            sheets = sorted([s for s in xls.sheet_names if "nhan su" in norm(s)], key=lambda s: "danh sach" not in norm(s))
            raws = [pd.read_excel(xls, sheet_name=s, dtype=str) for s in sheets]
        else:
            raws = [pd.read_csv(io.BytesIO(file_bytes), dtype=str)]
    except Exception:
        return empty
    frames = []
    for r in raws:
        c_id = _pick_col(r.columns, {"ma nhan vien", "id nhan vien"})
        c_pos = _pick_col(r.columns, {"vi tri cong viec"})
        if c_id is None or c_pos is None:
            continue
        c_st = _pick_col(r.columns, {"don vi cong tac", "ma cua hang"})
        c_sta = _pick_col(r.columns, {"trang thai lam viec", "trang thai cong viec"})

        def col(c, r=r):
            return r[c].fillna("").astype(str).str.strip() if c else ""

        frames.append(pd.DataFrame({"id": r[c_id].apply(norm_id), "pos": col(c_pos), "store": col(c_st), "status": col(c_sta)}))
    if not frames:
        return empty
    d = pd.concat(frames, ignore_index=True)
    d = d[d["id"] != ""].replace("", np.nan)
    return d.groupby("id", as_index=False).first().fillna("")


def staff_signature():
    try:
        stt = STAFF_FILE.stat()
        return f"{stt.st_mtime_ns}-{stt.st_size}"
    except (OSError, AttributeError):
        return "missing"


@st.cache_data(show_spinner=False)
def load_default_staff(sig=""):
    if STAFF_FILE is None or not STAFF_FILE.exists():
        return pd.DataFrame(columns=STAFF_COLS)
    return parse_staff(STAFF_FILE.read_bytes(), STAFF_FILE.name)


def check_audience(IV, staff, allowed_kw):
    """Gắn cờ bài Plus sai đối tượng: MSNV không thuộc vị trí được phép phỏng vấn."""
    if IV is None or IV.empty:
        return IV
    d = IV.copy()
    d["Vị trí (nhân sự)"], d["Trạng thái làm việc"] = "", ""
    d["Kiểm tra đối tượng"], d["Sai đối tượng"] = "Chưa kiểm tra", False
    kws = [norm(k) for k in str(allowed_kw).split(",") if norm(k)]
    if staff is None or staff.empty or not kws:
        return d
    sm = staff.set_index("id")
    key = d["employee_id"].apply(norm_id)
    pos, stat = key.map(sm["pos"]), key.map(sm["status"])
    miss = pos.isna() & key.ne("")
    if miss.any():  # MSNV trong bài không có tiền tố chữ -> so khớp theo phần số (chỉ khi duy nhất)
        sdg = staff.assign(dg=staff["id"].str.replace(r"\D", "", regex=True).str.lstrip("0"))
        uniq = sdg[~sdg["dg"].duplicated(keep=False) & sdg["dg"].ne("")].set_index("dg")
        dk = key.str.replace(r"\D", "", regex=True).str.lstrip("0")
        pos = pos.where(~miss, dk.map(uniq["pos"]))
        stat = stat.where(~miss, dk.map(uniq["status"]))
    known = pos.notna()
    ok = pos.apply(lambda p: isinstance(p, str) and any(k in norm(p) for k in kws))
    reason = pd.Series(np.select(
        [key.eq(""), ~known, known & pos.astype(str).str.strip().eq(""), ~ok],
        ["Bài thiếu MSNV", "MSNV không có trong danh sách nhân sự", "Danh sách nhân sự chưa ghi vị trí",
         "Vị trí không thuộc đối tượng phỏng vấn"], ""), index=d.index)
    d["Vị trí (nhân sự)"], d["Trạng thái làm việc"] = pos.fillna(""), stat.fillna("")
    d["Sai đối tượng"] = reason.ne("")
    d["Kiểm tra đối tượng"] = np.where(d["Sai đối tượng"], "🚨 SAI ĐỐI TƯỢNG – " + reason, "✅ Đúng đối tượng")
    return d


def alert_table(alerts):
    return pd.DataFrame({
        "Lead": alerts["Lead"], "Nhân viên (trong bài)": alerts["employee_name"], "MSNV": alerts["employee_id"],
        "Mã cửa hàng": alerts["store_code"], "Plus": alerts["plus_item"],
        "Vị trí (theo danh sách nhân sự)": alerts["Vị trí (nhân sự)"].replace("", "— không có trong danh sách —"),
        "Trạng thái làm việc": alerts["Trạng thái làm việc"],
        "Lý do": alerts["Kiểm tra đối tượng"].str.replace("🚨 SAI ĐỐI TƯỢNG – ", "", regex=False)})


_dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)


def low_table(low):
    return pd.DataFrame({
        "Lead": low["Lead"], "Nhân viên được phỏng vấn": low["employee_name"], "MSNV": low["employee_id"],
        "Mã cửa hàng": low["store_code"], "Plus": low["plus_item"], "% điểm": low["pct"].round(1),
        "Người chấm (Field)": low["field_name"]}).sort_values("% điểm")


def split_notices(IVc):
    """Tách thông báo: bài sai đối tượng và nhân viên phỏng vấn dưới ngưỡng cần follow."""
    if IVc is None or IVc.empty:
        e = pd.DataFrame()
        return e, e
    wrong = IVc[IVc["Sai đối tượng"].astype(bool)] if "Sai đối tượng" in IVc.columns else IVc.iloc[0:0]
    low = IVc[IVc["pct"].apply(lambda v: eval_pct(v, THR)).str.startswith("CHƯA ĐẠT")]
    return wrong, low


def _notices_body(wrong, low):
    if len(wrong):
        st.error(f"🚨 {len(wrong)} bài Plus phỏng vấn SAI ĐỐI TƯỢNG. Chỉ nhận bài của nhân viên bán hàng, "
                 "trưởng/quản lý cửa hàng, trợ lý cửa hàng và các vị trí AIO.")
        t = alert_table(wrong)
        show_df(t, height=min(60 + 36 * len(t), 300))
        dl_button(t, "Sai_doi_tuong", "Bai_Plus_sai_doi_tuong.xlsx", "dl_alert_dialog")
    if len(low):
        st.warning(f"⚠️ {len(low)} nhân viên phỏng vấn dưới {THR}% điểm: cần follow và trả bài ở kỳ tiếp theo.")
        t2 = low_table(low)
        show_df(t2, height=min(60 + 36 * len(t2), 300),
                column_config={"% điểm": st.column_config.NumberColumn(format="%.1f%%")})
        dl_button(t2, "Duoi_nguong_can_follow", "Nhan_vien_duoi_nguong_can_follow.xlsx", "dl_low_dialog")


show_notices = _dialog("🔔 Thông báo cần xử lý", width="large")(_notices_body) if _dialog else None


def bell(wrong, low, tag):
    """Chuông thông báo: đỏ nhấp nháy khi có bài sai đối tượng, cam khi chỉ có nhân viên dưới ngưỡng cần follow.
    Chỉ hiện nội dung liên quan tới người đăng nhập (admin thấy toàn bộ). Tự bật popup 1 lần khi có thông báo mới."""
    n1, n2 = len(wrong), len(low)
    if n1 and n2:
        label = f"🔔 {n1} sai đối tượng · {n2} dưới {THR}%"
    elif n1:
        label = f"🔔 {n1} bài sai đối tượng"
    elif n2:
        label = f"🔔 {n2} nhân viên dưới {THR}% cần follow"
    else:
        label = "🔔 Không có thông báo"
    clicked = st.button(label, key="bell_alert" if n1 else "bell_warn" if n2 else "bell_ok",
                        help="Thông báo: bài phỏng vấn sai đối tượng, nhân viên phỏng vấn dưới ngưỡng cần follow")
    sig = f"{tag}|{n1}|{n2}"
    auto = (n1 + n2) > 0 and st.session_state.get("bell_seen") != sig
    if auto:
        st.session_state["bell_seen"] = sig
    if (n1 + n2) and (clicked or auto):
        if show_notices:
            show_notices(wrong, low)
        else:
            _notices_body(wrong, low)


# =====================================================================
# Đăng nhập và phân quyền (admin / lead / field)
# =====================================================================
_EMBEDDED_USERS = """
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
OAAA
"""

USERS_FILE = find_file("users.csv")
USERS_LIVE = DATA_DIR / "users_live.csv"  # bản chỉnh sửa của Admin trên máy chủ (ưu tiên hơn users.csv)
PBKDF2_ITER = 200_000
ROLE_LABEL = {"admin": "Quản trị", "lead": "Lead", "field": "Field"}
USER_COLS = ["email", "role", "display_name", "lead", "field_names", "salt", "hash", "key", "active"]


def hash_pw(pw, salt_hex):
    return hashlib.pbkdf2_hmac("sha256", str(pw).encode(), bytes.fromhex(salt_hex), PBKDF2_ITER).hex()


def users_source():
    """Ưu tiên: bản Admin chỉnh sửa trên máy chủ > users.csv trên GitHub > bản tích hợp sẵn trong app (None)."""
    if USERS_LIVE.exists():
        return USERS_LIVE
    return USERS_FILE if (USERS_FILE is not None and USERS_FILE.exists()) else None


def users_signature():
    try:
        p = users_source()
        if p is None:
            return "embedded"
        stt = p.stat()
        return f"{p.name}-{stt.st_mtime_ns}-{stt.st_size}"
    except OSError:
        return "missing"


@st.cache_data(show_spinner=False)
def load_users(sig=""):
    p = users_source()
    raw = p.read_bytes() if p is not None else gzip.decompress(base64.b64decode("".join(_EMBEDDED_USERS.split())))
    d = pd.read_csv(io.BytesIO(raw), dtype=str).fillna("")
    if "active" not in d.columns:
        d["active"] = "1"
    d["active"] = d["active"].replace("", "1")  # mặc định: đang hoạt động
    d["key"] = d["email"].str.strip().str.lower()
    return d


@st.cache_resource
def _login_fails():
    return {}


def verify_login(email, pw):
    """Trả về (user, thông báo lỗi). Khóa 15 phút sau 5 lần sai; so sánh hằng thời gian."""
    users = load_users(users_signature())
    key = str(email).strip().lower()
    fails = _login_fails()
    n, ts = fails.get(key, (0, 0.0))
    if n >= 5 and time.time() - ts < 900:
        return None, "Tài khoản tạm khóa 15 phút do nhập sai nhiều lần."
    row = users[users["key"] == key]
    found = len(row) > 0
    salt = row.iloc[0]["salt"] if found else "00" * 16
    expect = row.iloc[0]["hash"] if found else "0" * 64
    ok = hmac.compare_digest(hash_pw(pw, salt), expect) and found
    if ok:
        fails.pop(key, None)
        r = row.iloc[0]
        if str(r.get("active", "1")) == "0":
            return None, "Tài khoản đã bị khóa. Liên hệ quản trị dashboard."
        return {k: r[k] for k in ("email", "role", "display_name", "lead", "field_names")}, ""
    if len(fails) > 2000:
        fails.clear()
    fails[key] = ((n + 1) if time.time() - ts < 900 else 1, time.time())
    return None, "Sai tài khoản hoặc mật khẩu."


def login_screen():
    st.markdown('<div class="brand" style="justify-content:center;margin-top:60px"><div class="logo">C</div><div>'
                '<div class="bn">CellphoneS Audit</div><div class="bs">Đăng nhập để xem dashboard</div></div></div>',
                unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        notice = st.session_state.pop("login_msg", None)
        if notice:
            st.warning(notice)
        with st.container(border=True):
            with st.form("login_form"):
                email = st.text_input("Email / tên đăng nhập", key="login_email")
                pw = st.text_input("Mật khẩu", type="password", key="login_pw")
                go = st.form_submit_button("Đăng nhập", type="primary")
            if go:
                user, msg = verify_login(email, pw)
                if user:
                    st.session_state["user"] = user
                    st.rerun()
                st.error(msg)
        st.caption("Chưa có tài khoản hoặc quên mật khẩu: liên hệ quản trị dashboard.")


AUTH_ON = True  # luôn bật đăng nhập (không còn chế độ mở)
if AUTH_ON:
    USER = st.session_state.get("user")
    if not USER:
        login_screen()
        st.stop()
    _u = load_users(users_signature())
    _r = _u[_u["key"] == str(USER["email"]).strip().lower()]
    if _r.empty or str(_r.iloc[0].get("active", "1")) == "0":  # tài khoản bị xóa hoặc bị khóa -> buộc đăng xuất
        st.session_state.pop("user", None)
        st.session_state["login_msg"] = "Tài khoản đã bị khóa hoặc không còn tồn tại. Liên hệ quản trị dashboard."
        st.rerun()
    USER = {k: _r.iloc[0][k] for k in ("email", "role", "display_name", "lead", "field_names")}  # cập nhật theo chỉnh sửa mới nhất
    st.session_state["user"] = USER
else:  # chưa có users.csv -> chạy chế độ mở như trước (có cảnh báo)
    USER = {"email": "", "role": "admin", "display_name": "Chưa bật đăng nhập", "lead": "", "field_names": ""}
ROLE = USER["role"]
IS_ADMIN = ROLE == "admin"
MY_LEAD = USER.get("lead", "") if ROLE == "lead" else ""
MY_NAMES = {norm(n) for n in (str(USER.get("field_names", "")).split("|") + [USER.get("display_name", "")]) if norm(n)}
if ROLE == "lead" and not MY_LEAD:
    st.error("Tài khoản Lead chưa được gán tên Lead. Liên hệ quản trị.")
    st.stop()

# =====================================================================
# Yêu cầu bổ sung (Lead -> nhân sự Field). Lưu trong data/requests.json trên máy chủ.
# =====================================================================
REQ_FILE = DATA_DIR / "requests.json"


@st.cache_resource
def _req_lock():
    return threading.Lock()


def now_str():
    return pd.Timestamp.now(tz="Asia/Ho_Chi_Minh").strftime("%d/%m %H:%M")


def load_requests():
    try:
        return json.loads(REQ_FILE.read_text("utf-8")) if REQ_FILE.exists() else []
    except Exception:  # noqa: BLE001
        return []


def _save_requests(items):
    DATA_DIR.mkdir(exist_ok=True)
    tmp = REQ_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=1), "utf-8")
    tmp.replace(REQ_FILE)


def add_requests(new_items):
    """Thêm yêu cầu; bỏ qua plan đang có yêu cầu 'Mở'. Trả về (số đã thêm, số bỏ qua)."""
    with _req_lock():
        items = load_requests()
        open_plans = {r["plan"] for r in items if r.get("status") == "Mở"}
        added = skipped = 0
        for it in new_items:
            if it["plan"] in open_plans:
                skipped += 1
                continue
            it["id"] = f"r{int(time.time() * 1000)}{secrets.token_hex(2)}"
            items.append(it)
            open_plans.add(it["plan"])
            added += 1
        _save_requests(items)
    return added, skipped


def update_request(rid, **fields):
    with _req_lock():
        items = load_requests()
        for r in items:
            if r.get("id") == rid:
                r.update(fields)
        _save_requests(items)


def name_email_map():
    m = {}
    for _, r in load_users(users_signature()).iterrows():
        for n in str(r["field_names"]).split("|"):
            if norm(n):
                m.setdefault(norm(n), r["email"])
    return m


VALID_ROLES = ("admin", "lead", "field")
PW_ALPHABET = "abcdefghjkmnpqrstuvwxyzACDEFGHJKLMNPQRTUVWXYZ2346789"


def gen_password(n=10):
    return "".join(secrets.choice(PW_ALPHABET) for _ in range(n))


def _clean(v):
    return "" if pd.isna(v) else str(v).strip()


def apply_user_edits(orig, edited, me_id, known_leads):
    """Áp dụng bảng chỉnh sửa tài khoản. Giữ nguyên mật khẩu (salt/hash) của tài khoản cũ, cấp mật khẩu mới cho dòng mới.
    Trả về (bảng users mới | None, danh sách mật khẩu mới, danh sách lỗi)."""
    orig = orig.reset_index(drop=True)
    errors, rows, new_pw, seen, used = [], [], [], {}, {}
    for pos, r in edited.reset_index(drop=True).iterrows():
        email, role, name, lead, names = (_clean(r.get(c)) for c in ("email", "role", "display_name", "lead", "field_names"))
        if not any([email, role, name, lead, names]):
            continue
        active = "0" if _clean(r.get("status")).lower() in ("đã khóa", "da khoa", "khóa", "khoa", "locked", "0") else "1"
        line = f"Dòng {pos + 1}"
        key = email.lower()
        if not email or " " in email:
            errors.append(f"{line}: tài khoản trống hoặc có khoảng trắng.")
            continue
        if key in seen:
            errors.append(f"{line}: tài khoản '{email}' bị trùng với dòng {seen[key] + 1}.")
            continue
        seen[key] = pos
        if role not in VALID_ROLES:
            errors.append(f"{line} ({email}): vai trò phải là admin, lead hoặc field.")
            continue
        if role == "lead" and lead not in known_leads:
            errors.append(f"{line} ({email}): vai trò Lead cần chọn đúng tên Lead ({', '.join(known_leads)}).")
            continue
        oid = r.get("_id")
        base = None
        if pd.notna(oid) and int(oid) in range(len(orig)) and int(oid) not in used:
            base = orig.loc[int(oid)]
            used[int(oid)] = (role, active)
        if base is not None:
            salt, hh = base["salt"], base["hash"]
        else:
            pw = gen_password()
            salt = secrets.token_hex(16)
            hh = hash_pw(pw, salt)
            new_pw.append({"Tài khoản": email, "Vai trò": role, "Tên": name or email, "Lead": lead, "Mật khẩu ban đầu": pw})
        rows.append({"email": email, "role": role, "display_name": name or email, "lead": lead,
                     "field_names": names, "salt": salt, "hash": hh, "active": active})
    if not any(x["role"] == "admin" and x["active"] == "1" for x in rows):
        errors.append("Phải còn ít nhất một tài khoản Quản trị (admin) đang hoạt động.")
    if me_id is not None:
        if me_id not in used:
            errors.append("Không thể xóa tài khoản đang đăng nhập.")
        elif used[me_id][0] != "admin":
            errors.append("Không thể tự hạ quyền Quản trị của chính mình.")
        elif used[me_id][1] == "0":
            errors.append("Không thể tự khóa tài khoản đang đăng nhập.")
    return (None if errors else pd.DataFrame(rows)), new_pw, errors


def reset_passwords(users, keys):
    u = users.reset_index(drop=True).copy()
    out = []
    for i, r in u.iterrows():
        if r["email"].strip().lower() in keys:
            pw = gen_password()
            salt = secrets.token_hex(16)
            u.loc[i, "salt"], u.loc[i, "hash"] = salt, hash_pw(pw, salt)
            out.append({"Tài khoản": r["email"], "Vai trò": r["role"], "Tên": r["display_name"], "Lead": r["lead"],
                        "Mật khẩu ban đầu": pw})
    return u, out


USER_SAVE_COLS = ["email", "role", "display_name", "lead", "field_names", "salt", "hash", "active"]


def save_users(df):
    with _req_lock():
        DATA_DIR.mkdir(exist_ok=True)
        tmp = USERS_LIVE.with_suffix(".tmp")
        df[USER_SAVE_COLS].to_csv(tmp, index=False, encoding="utf-8")
        tmp.replace(USERS_LIVE)


def base_users():
    """Danh sách tài khoản gốc (users.csv trên GitHub hoặc bản tích hợp), không tính chỉnh sửa trên máy chủ."""
    if USERS_FILE is not None and USERS_FILE.exists():
        raw = USERS_FILE.read_bytes()
    else:
        raw = gzip.decompress(base64.b64decode("".join(_EMBEDDED_USERS.split())))
    d = pd.read_csv(io.BytesIO(raw), dtype=str).fillna("")
    if "active" not in d.columns:
        d["active"] = "1"
    d["active"] = d["active"].replace("", "1")
    d["key"] = d["email"].str.strip().str.lower()
    return d


def check_new_password(old, new, confirm):
    """Trả về thông báo lỗi (rỗng nếu hợp lệ)."""
    if not old or not new or not confirm:
        return "Vui lòng nhập đủ 3 ô."
    if new != confirm:
        return "Mật khẩu mới nhập lại không khớp."
    if len(new) < 8:
        return "Mật khẩu mới phải có ít nhất 8 ký tự."
    if not (re.search(r"[A-Za-z]", new) and re.search(r"\d", new)):
        return "Mật khẩu mới cần có cả chữ và số."
    if new == old:
        return "Mật khẩu mới phải khác mật khẩu hiện tại."
    return ""


def change_password(email, old, new):
    """Tự đổi mật khẩu. Trả về thông báo lỗi (rỗng nếu thành công). Khóa 15 phút sau 5 lần nhập sai mật khẩu hiện tại."""
    key = str(email).strip().lower()
    fails = _login_fails()
    n, ts = fails.get("pw:" + key, (0, 0.0))
    if n >= 5 and time.time() - ts < 900:
        return "Đã nhập sai nhiều lần, tạm khóa đổi mật khẩu 15 phút."
    users = load_users(users_signature()).reset_index(drop=True)
    idx = users.index[users["key"] == key]
    if len(idx) == 0:
        return "Không tìm thấy tài khoản."
    r = users.loc[idx[0]]
    if not hmac.compare_digest(hash_pw(old, r["salt"]), r["hash"]):
        fails["pw:" + key] = ((n + 1) if time.time() - ts < 900 else 1, time.time())
        return "Mật khẩu hiện tại không đúng."
    fails.pop("pw:" + key, None)
    salt = secrets.token_hex(16)
    users.loc[idx[0], "salt"], users.loc[idx[0], "hash"] = salt, hash_pw(new, salt)
    save_users(users)
    return ""


def pw_xlsx_bytes(rows):
    buf = io.BytesIO()
    pd.DataFrame(rows).to_excel(buf, index=False)
    return buf.getvalue()


# =====================================================================
# Sidebar
# =====================================================================
DATA_DIR = Path(__file__).parent / "data"


def saved_file(pre):
    for ext in ("xlsx", "xls"):
        p = DATA_DIR / f"raw_{pre}.{ext}"
        if p.exists():
            return p
    return None


def save_raw(pre, data):
    try:
        DATA_DIR.mkdir(exist_ok=True)
        for ext in ("xlsx", "xls"):
            (DATA_DIR / f"raw_{pre}.{ext}").unlink(missing_ok=True)
        (DATA_DIR / f"raw_{pre}.xlsx").write_bytes(data)
        return True
    except OSError:
        return False


for _pre in ("l1", "l2"):
    st.session_state.setdefault(f"{_pre}_bytes", None)
    st.session_state.setdefault(f"{_pre}_name", None)
    st.session_state.setdefault(f"{_pre}_saved", None)
    p = saved_file(_pre)
    if st.session_state[f"{_pre}_bytes"] is None and p is not None:  # mở lại app -> tự nạp file đã lưu
        st.session_state[f"{_pre}_bytes"] = p.read_bytes()
        st.session_state[f"{_pre}_name"] = p.name
        st.session_state[f"{_pre}_saved"] = pd.Timestamp(p.stat().st_mtime, unit="s", tz="UTC") \
            .tz_convert("Asia/Ho_Chi_Minh").strftime("%d/%m %H:%M")

default_stores, store_src = load_default_stores(store_signature())

with st.sidebar:
    st.markdown('<div class="brand"><div class="logo">C</div><div><div class="bn">CellphoneS Audit</div>'
                '<div class="bs">Màn hình điều hành</div></div></div>', unsafe_allow_html=True)
    if AUTH_ON:
        st.markdown('<div class="sbt">Tài khoản</div>', unsafe_allow_html=True)
        st.markdown(chip(f"👤 {USER.get('display_name') or USER['email']} · {ROLE_LABEL[ROLE]}", "ok"), unsafe_allow_html=True)
        if st.button("Đăng xuất", key="logout"):
            st.session_state.pop("user", None)
            st.rerun()
        with st.expander("🔑 Đổi mật khẩu"):
            with st.form("pw_form", clear_on_submit=True):
                p_old = st.text_input("Mật khẩu hiện tại", type="password", key="pw_old")
                p_new = st.text_input("Mật khẩu mới (từ 8 ký tự, có chữ và số)", type="password", key="pw_new")
                p_cf = st.text_input("Nhập lại mật khẩu mới", type="password", key="pw_cf")
                go_pw = st.form_submit_button("Đổi mật khẩu")
            if go_pw:
                err_pw = check_new_password(p_old, p_new, p_cf) or change_password(USER["email"], p_old, p_new)
                if err_pw:
                    st.error(err_pw)
                else:
                    st.success("Đã đổi mật khẩu. Lần đăng nhập sau dùng mật khẩu mới.")
    else:
        st.markdown(chip("⚠️ Chưa bật đăng nhập (thiếu users.csv)", "warn"), unsafe_allow_html=True)
    st.markdown('<div class="sbt">Chế độ xem</div>', unsafe_allow_html=True)
    view = st.radio("Chế độ", ["📌 LẦN 1", "📌 LẦN 2"] + (["📊 CEO VIEW"] if IS_ADMIN else []), index=0,
                    label_visibility="collapsed")
    st.markdown('<div class="sbt">Dữ liệu</div>', unsafe_allow_html=True)
    for lbl, pre in [("Raw Data Lần 1", "l1"), ("Raw Data Lần 2", "l2")]:
        up = st.file_uploader(lbl, type=["xlsx", "xls"], key=f"up_{pre}") if IS_ADMIN else None
        if up:
            data = up.getvalue()
            if data != st.session_state[f"{pre}_bytes"]:
                st.session_state[f"{pre}_bytes"], st.session_state[f"{pre}_name"] = data, up.name
                ok = save_raw(pre, data)
                st.session_state[f"{pre}_saved"] = pd.Timestamp.now(tz="Asia/Ho_Chi_Minh").strftime("%d/%m %H:%M") if ok else None
        if st.session_state[f"{pre}_bytes"] is not None:
            when = st.session_state[f"{pre}_saved"]
            st.markdown(chip(f"{pre.upper()} · {st.session_state[f'{pre}_name']}" + (f" · {when}" if when else ""),
                             "ok" if when else "warn"), unsafe_allow_html=True)
    st.markdown('<div class="sbt">Bộ lọc</div>', unsafe_allow_html=True)
    stores_all = default_stores
    leaders = sorted(set(stores_all["Lead"]) - {""}) if not stores_all.empty else []
    if ROLE == "lead":
        selected_leader = MY_LEAD
        st.markdown(chip(f"Lead: {MY_LEAD}", "dark"), unsafe_allow_html=True)
    elif ROLE == "field":
        selected_leader = "Tất cả"
    else:
        selected_leader = st.selectbox("Lead", ["Tất cả"] + leaders)
    search = st.text_input("Tìm cửa hàng / NV / MSNV", "")
    THR, DEFAULT_MAX, ALLOWED_KW, CAMPUS_KW, u3, u4 = 80, 100, DEFAULT_ALLOWED, "CAMPUS", None, None
    if IS_ADMIN:
        with st.expander("⚙️ Thiết lập"):
            THR = st.slider("Ngưỡng điểm trả bài (%)", 50, 100, 80, 5)
            DEFAULT_MAX = st.number_input("Điểm tối đa (khi raw thiếu 'Thang điểm')", 1, 1000, 100)
            ALLOWED_KW = st.text_input("Vị trí được phép phỏng vấn Plus (từ khóa, cách nhau bằng dấu phẩy)", DEFAULT_ALLOWED,
                                       help="Bài Plus của MSNV có vị trí không chứa từ khóa nào ở đây sẽ bị báo SAI ĐỐI TƯỢNG.")
            u4 = st.file_uploader("Danh sách nhân sự mới (Excel/CSV)", type=["xlsx", "xls", "csv"], key="up_staff")
            CAMPUS_KW = st.text_input("Từ khóa nhận diện CAMPUS", "CAMPUS",
                                      help="App xếp plan vào CAMPUS khi từ khóa này có trong Mã cửa hàng, Hệ thống hoặc Tên plan.")
            u3 = st.file_uploader("DS cửa hàng thay thế (CSV/Excel)", type=["csv", "xlsx", "xls"], key="up_store")
    stores = default_stores
    if u3:
        parsed = parse_store_master(u3.getvalue(), u3.name)
        if parsed.empty:
            st.warning("Không đọc được DS cửa hàng vừa nạp, dùng bảng mặc định.")
        else:
            stores = merge_flags(parsed, default_stores)
    try:
        DATA_DIR.mkdir(exist_ok=True)
    except OSError:
        pass
    if u4:
        try:
            for ext in (".xlsx", ".xls", ".csv"):
                (DATA_DIR / f"nhan_su_upload{ext}").unlink(missing_ok=True)
            (DATA_DIR / f"nhan_su_upload{Path(u4.name).suffix.lower()}").write_bytes(u4.getvalue())
        except OSError:
            pass
    _sp = next((p for ext in (".xlsx", ".xls", ".csv") if (p := DATA_DIR / f"nhan_su_upload{ext}").exists()), None)
    staff = parse_staff(_sp.read_bytes(), _sp.name) if _sp else pd.DataFrame(columns=STAFF_COLS)
    if staff.empty:
        staff = load_default_staff(staff_signature())
    FLAGS_OK = (not stores.empty) and bool((stores["Mystery"] == "Có").any())
    st.markdown(chip(f"DS cửa hàng: {len(stores)} shop ({'file đã nạp' if u3 and stores is not default_stores else store_src})"
                     if len(stores) else "⚠️ Thiếu danh sách cửa hàng",
                     "dark" if len(stores) else "warn"), unsafe_allow_html=True)
    st.markdown(chip(f"Danh sách nhân sự: {len(staff):,} người" if len(staff) else "⚠️ Chưa có danh sách nhân sự (nhan_su.csv)",
                     "dark" if len(staff) else "warn"), unsafe_allow_html=True)
    if len(stores) and not FLAGS_OK:
        st.markdown(chip("⚠️ store_master.csv là bản cũ (thiếu cột Mystery/L2)", "warn"), unsafe_allow_html=True)

VIEW_TITLE = {"📌 LẦN 1": "Đợt audit Lần 1", "📌 LẦN 2": "Đợt audit Lần 2", "📊 CEO VIEW": "Tổng quan điều hành"}
_p = "l2" if view == "📌 LẦN 2" else "l1"
_chips = []
if view != "📊 CEO VIEW":
    _nm, _when = st.session_state.get(f"{_p}_name"), st.session_state.get(f"{_p}_saved")
    _chips.append(chip(f"📄 {_nm}" + (f" · {_when}" if _when else "") if _nm else "Chưa nạp dữ liệu", ""))
if selected_leader != "Tất cả":
    _chips.append(chip(f"Lead: {selected_leader}", ""))
if AUTH_ON:
    _chips.append(chip(f"👤 {USER.get('display_name') or USER['email']} · {ROLE_LABEL[ROLE]}", ""))
_chips.append(chip(f"v{APP_VERSION}", ""))
st.markdown(
    f'<div class="hero"><div><div class="hero-title">CellphoneS Audit Control Tower</div>'
    f'<div class="hero-sub">{VIEW_TITLE[view]} · Trade CPS/DTV · Plus · Mystery · CAMPUS · Trả bài · QC</div></div>'
    f'<div class="chips">{"".join(_chips)}</div></div>', unsafe_allow_html=True)


def lead_filter(df):
    if selected_leader != "Tất cả" and df is not None and not df.empty and "Lead" in df.columns:
        return df[df["Lead"] == selected_leader]
    return df


# =====================================================================
# Tab renderers
# =====================================================================
def need_cols(df, spec):
    """Đảm bảo bảng có đủ cột (tránh KeyError khi dữ liệu cũ / thiếu cột)."""
    for c, default in spec.items():
        if c not in df.columns:
            df[c] = default
    return df


def safe(fn, *args, **kw):
    """Chạy một mục; nếu lỗi chỉ báo lỗi ở mục đó, không làm sập cả trang."""
    try:
        fn(*args, **kw)
    except Exception as e:  # noqa: BLE001
        st.error(f"Mục này đang gặp lỗi dữ liệu ({type(e).__name__}: {e}). Các mục khác vẫn dùng bình thường.")
        with st.expander("Chi tiết kỹ thuật (gửi cho người hỗ trợ)"):
            st.code(traceback.format_exc())


def tab_overview(P, cps_m, dtv_m, my_m, ls, label, n_alert=0, n_low=0):
    if n_alert:
        st.error(f"🚨 Có {n_alert} bài Plus phỏng vấn SAI ĐỐI TƯỢNG. Bấm chuông 🔔 ở góc trên bên phải "
                 "hoặc mở tab 'Trả bài Plus' để xem chi tiết.")
    if n_low:
        st.warning(f"⚠️ Có {n_low} nhân viên phỏng vấn dưới {THR}% điểm cần follow, trả bài ở kỳ tiếp theo. "
                   "Bấm chuông 🔔 hoặc mở tab 'Trả bài Plus'.")
    plus = P[P["Nghiệp vụ"] == "Plus"]
    my_t = my_m[~my_m["Ngoài DS giao"]]
    cd, ct = int(cps_m["_done"].sum()), len(cps_m)
    dd, dt = int(dtv_m["_done"].sum()), len(dtv_m)
    md, mt = int(my_t["_done"].sum()), len(my_t)
    pdn, pt = int(plus["Hoàn thành"].sum()), len(plus)
    cards = [
        kpi_card("CPS – đủ 4 hạng mục", f"{cd}/{ct}", "cửa hàng đã hoàn thành", pct(cd, ct)),
        kpi_card("DTV – đủ hạng mục", f"{dd}/{dt}", "cửa hàng đã hoàn thành", pct(dd, dt)) if (label == "Lần 1" and dt)
        else kpi_card("DTV", "—", "Lần 2 không áp dụng" if label == "Lần 2" else "Không có cửa hàng DTV"),
        kpi_card("Plus – plan hoàn thành", f"{pdn}/{pt}", "Field và QC đều đã xong", pct(pdn, pt)),
        kpi_card("Mystery – cửa hàng hoàn tất", f"{md}/{mt}", "trên tổng số cửa hàng được giao", pct(md, mt)),
        kpi_card("Plan bị từ chối", int(P["Bị từ chối"].sum()), "cần chấm lại / bổ sung", None, bad=True),
        kpi_card("QC chưa chấm", int((P["_st"] == "WAIT_QC").sum()), "plan Field xong, chờ QC viên", None, bad=True),
    ]
    st.markdown('<div class="kpi-row">' + "".join(cards) + "</div>", unsafe_allow_html=True)

    section("Scorecard theo Lead", "KPI = số cửa hàng Lead đang quản lý · Xanh ≥ 80% · Cam 50–80% · Đỏ < 50%")
    lead_cards(ls)
    section("Bảng số liệu theo Lead")
    pcols = ["% CPS", "% DTV", "% Mystery", "% Plus", "% KPI tổng (CPS+DTV+Mystery)"]
    show_df(ls, column_config=PCT_CFG(pcols))
    if ls.empty:
        return
    a, b = st.columns(2)
    with a:
        long = ls.melt(id_vars="Lead", value_vars=["CPS (cửa hàng)", "CPS hoàn thành", "DTV (cửa hàng)", "DTV hoàn thành",
                                                  "Mystery (giao)", "Mystery hoàn tất"],
                       var_name="Chỉ tiêu", value_name="Số lượng")
        bar_chart(long, "Lead", "Số lượng", "Số cửa hàng được giao và đã hoàn thành", color="Chỉ tiêu")
    with b:
        long = ls.melt(id_vars="Lead", value_vars=pcols, var_name="Hạng mục", value_name="%")
        fig = px.bar(long, x="Lead", y="%", color="Hạng mục", barmode="group", title="Tỷ lệ hoàn thành theo Lead (%)")
        fig.update_traces(texttemplate="%{y:.0f}%", textangle=0, textposition="outside")
        show_chart(fig)
    a, b = st.columns(2)
    with a:
        cnt = P["_st"].map(STATUS_LABEL).value_counts()
        pie_chart(cnt.index.tolist(), cnt.values.tolist(), "Tình trạng của tất cả plan", STATUS_COLOR)
    with b:
        pie_chart(["CPS đủ 4 hạng mục", "CPS chưa đủ"], [cd, ct - cd], "Cửa hàng CPS: đủ / chưa đủ",
                  {"CPS đủ 4 hạng mục": "#12b76a", "CPS chưa đủ": "#f04438"})


def tab_trade(M, items, system, key, n_plans, label):
    if n_plans == 0:
        st.warning(f"Chưa có plan Trade nào của {system} trong dữ liệu {label}. "
                   "Hãy xem mục 'Kiểm tra dữ liệu' (cột Chấm, Hệ thống, Hạng mục).")
    M = text_filter(lead_filter(M), ["Mã cửa hàng", "Địa chỉ cửa hàng", "Lead"], search)
    if M.empty:
        why = "Lead đang chọn không quản lý cửa hàng này" if selected_leader != "Tất cả" else \
            f"danh sách cửa hàng chưa có shop {system}"
        st.info(f"Không có cửa hàng {system} để hiển thị ({why}).")
        return
    done, tot = int(M["_done"].sum()), len(M)
    c = st.columns(3)
    c[0].metric(f"Tổng số cửa hàng {system}", tot)
    c[1].metric("Đã đủ hạng mục", f"{done}  ({pct(done, tot):.0f}%)")
    c[2].metric("Chưa đủ hạng mục", tot - done)

    a, b, c3 = st.columns([5, 6, 4])
    with a:
        g = M.groupby("Lead").agg(**{"Đã đủ": ("_done", "sum"), "Tổng": ("_done", "size")}).reset_index()
        g["Chưa đủ"] = g["Tổng"] - g["Đã đủ"]
        bar_chart(g, "Lead", ["Đã đủ", "Chưa đủ"], f"Cửa hàng {system} theo Lead", barmode="stack")
    with b:
        long = pd.concat([M[it].value_counts().rename_axis("Tình trạng").reset_index(name="Số lượng")
                          .assign(**{"Hạng mục": it}) for it in items])
        bar_chart(long, "Hạng mục", "Số lượng", "Tình trạng từng hạng mục", barmode="stack",
                  color="Tình trạng", color_discrete_map=STATUS_COLOR)
    with c3:
        pie_chart(["Đã đủ", "Chưa đủ"], [done, tot - done], f"{system}: đủ / chưa đủ",
                  {"Đã đủ": "#12b76a", "Chưa đủ": "#f04438"})

    section(f"Cửa hàng {system} chưa đủ hạng mục", "Liệt kê hạng mục còn thiếu và lý do (theo ghi chú QC)")
    inc = M[~M["_done"]].sort_values(["Lead", "Mã cửa hàng"])
    cols = ["Lead", "Mã cửa hàng", "Địa chỉ cửa hàng"] + items + ["Số HM đạt", "Thiếu hạng mục", "Ghi chú"]
    if inc.empty:
        st.success("Tất cả cửa hàng đã hoàn thành đủ hạng mục.")
    else:
        show_df(inc[cols], height=520, column_config={"Ghi chú": st.column_config.TextColumn("Ghi chú", width="large")})
        dl_button(inc[cols], f"{system}_chua_du", f"{system}_chua_du_hang_muc.xlsx", f"dl_{key}")
    with st.expander(f"Xem tất cả cửa hàng {system}"):
        show_df(M[cols], height=500)


def tab_plus(P):
    t = lead_filter(P[P["Nghiệp vụ"] == "Plus"])
    t = text_filter(t, ["store", "Tên Plan", "Lead"], search)
    if t.empty:
        st.info("Chưa có plan Plus nào theo bộ lọc hiện tại.")
        return
    rows = []
    for it in PLUS_ITEMS + sorted(set(t["Hạng mục"]) - set(PLUS_ITEMS)):
        g = t[t["Hạng mục"] == it]
        if g.empty and it not in PLUS_ITEMS:
            continue
        rows.append({"Hạng mục": it, "Tổng plan": len(g), "Field xong": int(g["Field done"].sum()),
                     "QC duyệt xong": int(g["QC done"].sum()), "Hoàn thành (Field + QC)": int(g["Hoàn thành"].sum()),
                     "Chờ QC": int((g["_st"] == "WAIT_QC").sum()), "Bị từ chối": int(g["Bị từ chối"].sum())})
    s = pd.DataFrame(rows)
    c = st.columns(4)
    c[0].metric("Tổng số plan Plus", len(t))
    c[1].metric("Field đã xong", int(t["Field done"].sum()))
    c[2].metric("QC đã duyệt xong", int(t["QC done"].sum()))
    c[3].metric("Bị từ chối", int(t["Bị từ chối"].sum()))
    section("Tiến độ Plus 1 → Plus 5")
    show_df(s)
    a, b = st.columns(2)
    with a:
        bar_chart(s, "Hạng mục", ["Field xong", "QC duyệt xong", "Hoàn thành (Field + QC)", "Bị từ chối"],
                  "Tiến độ từng Plus")
    with b:
        cnt = t["_st"].map(STATUS_LABEL).value_counts()
        pie_chart(cnt.index.tolist(), cnt.values.tolist(), "Tình trạng plan Plus", STATUS_COLOR)
    g = t.groupby("Lead").agg(**{"Tổng plan": ("Tên Plan", "size"), "Hoàn thành": ("Hoàn thành", "sum"),
                                 "Bị từ chối": ("Bị từ chối", "sum")}).reset_index()
    bar_chart(g, "Lead", ["Tổng plan", "Hoàn thành", "Bị từ chối"], "Plus theo Lead")
    section("Plan Plus bị từ chối và lý do")
    rej = t[t["Bị từ chối"]][["Lead", "store", "Hạng mục", "Tên Plan", "Ghi chú QC"]] \
        .rename(columns={"store": "Mã cửa hàng", "Tên Plan": "Tên plan", "Ghi chú QC": "Lý do từ chối"})
    if rej.empty:
        st.success("Không có plan Plus nào bị từ chối.")
    else:
        show_df(rej, height=400, column_config={"Lý do từ chối": st.column_config.TextColumn(width="large")})


def tab_mystery(M, P, sheets):
    if "Mystery Audit" not in sheets:
        st.warning("Raw data không có sheet Mystery (tên sheet cần chứa chữ 'Mystery'). "
                   f"Các sheet đọc được: {', '.join(sheets) or 'không có'}.")
        return
    if not FLAGS_OK:
        st.warning("File store_master.csv đang thiếu cột Mystery nên chưa biết đâu là 125 cửa hàng được giao. "
                   "Tạm tính mọi cửa hàng có plan Mystery là cửa hàng được giao. "
                   "Hãy upload store_master.csv bản mới lên GitHub để tính đúng.")
    M = text_filter(lead_filter(M), ["Mã cửa hàng", "Địa chỉ cửa hàng", "Lead"], search)
    tgt = M[~M["Ngoài DS giao"]]
    if tgt.empty:
        st.info("Không có cửa hàng Mystery nào theo bộ lọc hiện tại.")
        return
    done = int(tgt["_done"].sum())
    stt = tgt["Trạng thái"].value_counts()
    c = st.columns(4)
    c[0].metric("Cửa hàng được giao", len(tgt))
    c[1].metric("Đã hoàn tất", f"{done}  ({pct(done, len(tgt)):.0f}%)")
    c[2].metric("Có plan bị từ chối", int(stt.get("❌ Có plan bị từ chối", 0)))
    c[3].metric("Chưa có plan", int(stt.get("— Chưa có plan", 0)))
    a, b = st.columns(2)
    with a:
        g = tgt.groupby("Lead").agg(**{"Giao": ("_done", "size"), "Hoàn tất": ("_done", "sum")}).reset_index()
        bar_chart(g, "Lead", ["Giao", "Hoàn tất"], "Mystery theo Lead")
    with b:
        pie_chart(stt.index.tolist(), stt.values.tolist(), "Tình trạng cửa hàng Mystery",
                  {"✅ Hoàn tất": "#12b76a", "🕓 Đang thực hiện": "#f79009",
                   "❌ Có plan bị từ chối": "#f04438", "— Chưa có plan": "#d0d5dd"})
    section("Cửa hàng Mystery chưa hoàn tất", "Kèm lý do: plan bị từ chối (theo QC note), đang thực hiện hoặc chưa có plan")
    cols = ["Lead", "Mã cửa hàng", "Địa chỉ cửa hàng", "Số plan", "Plan hoàn thành", "Plan bị từ chối", "Trạng thái", "Ghi chú"]
    inc = tgt[~tgt["_done"]].sort_values(["Lead", "Mã cửa hàng"])
    show_df(inc[cols], height=480, column_config={"Ghi chú": st.column_config.TextColumn(width="large")})
    if not inc.empty:
        dl_button(inc[cols], "Mystery_chua_xong", "Mystery_chua_hoan_tat.xlsx", "dl_my")
    extra = M[M["Ngoài DS giao"]]
    if not extra.empty:
        st.warning(f"Có {len(extra)} cửa hàng có plan Mystery nhưng không nằm trong danh sách được giao.")
    mp = lead_filter(P[P["Nghiệp vụ"] == "Mystery"])
    if not mp.empty:
        section("Kịch bản Mystery theo Lead")
        g = mp.groupby(["Lead", "Hạng mục"]).agg(**{"Tổng plan": ("Tên Plan", "size"),
                                                   "Hoàn thành": ("Hoàn thành", "sum")}).reset_index()
        show_df(g)
        bar_chart(g, "Lead", "Tổng plan", "Cơ cấu kịch bản Mystery", barmode="stack", color="Hạng mục")


def tab_campus(C, P):
    C = lead_filter(C)
    if C.empty:
        st.info("Chưa tìm thấy cơ sở CAMPUS nào trong dữ liệu.")
        st.caption(f"App nhận diện CAMPUS khi từ khóa '{CAMPUS_KW}' xuất hiện trong Mã cửa hàng, Hệ thống hoặc Tên plan. "
                   "Nếu mã CAMPUS của bạn viết khác, đổi từ khóa ở Thiết lập (thanh bên trái).")
        with st.expander("Giá trị 'Hệ thống' và mẫu mã cửa hàng trong dữ liệu"):
            show_df(P.groupby("Hệ thống").agg(**{"Số plan": ("Tên Plan", "size"),
                                                 "Mã cửa hàng mẫu": ("store", lambda s: ", ".join(sorted(set(s))[:3]))}).reset_index())
        return
    done = int(C["_done"].sum())
    c = st.columns(3)
    c[0].metric("Số cơ sở CAMPUS", len(C))
    c[1].metric("Đã hoàn thành hết", done)
    c[2].metric("Chưa xong / bị từ chối", len(C) - done)
    cols = ["Lead", "Mã cửa hàng", "Số plan", "Plan hoàn thành", "Plan bị từ chối", "Trạng thái", "Ghi chú"]
    show_df(C[cols], height=420, column_config={"Ghi chú": st.column_config.TextColumn(width="large")})
    cnt = C["Trạng thái"].value_counts()
    pie_chart(cnt.index.tolist(), cnt.values.tolist(), "Tình trạng các cơ sở CAMPUS")


def tab_interviews(IV):
    st.caption(f"Kết quả chấm của từng nhân viên theo dữ liệu Field/QC hiện tại. "
               f"Dưới {THR}% điểm tối đa thì phải trả bài lại ở đợt 2 và được follow.")
    if IV.empty:
        st.info("Chưa có dữ liệu trả bài (cần sheet Trade Audit Plus có dòng mã câu hỏi TT1).")
        return
    d = need_cols(IV.copy(), {"field_done": False, "plus_item": "Plus ?", "qc_status": "NONE", "Lead": "Chưa gán",
                              "field_name": "", "employee_id": "", "store_code": "", "pct": np.nan,
                              "score": np.nan, "max_score": np.nan, "Sai đối tượng": False,
                              "Kiểm tra đối tượng": "Chưa kiểm tra", "Vị trí (nhân sự)": "", "Trạng thái làm việc": ""})
    d["Kết luận"] = d["pct"].apply(lambda v: eval_pct(v, THR))
    d = text_filter(lead_filter(d), ["employee_name", "employee_id", "store_code", "plan_name"], search)
    if d.empty:
        st.info("Không có bài nào theo bộ lọc hiện tại.")
        return
    low = d[d["Kết luận"].str.startswith("CHƯA ĐẠT")]
    ok = d[d["Kết luận"].eq("ĐẠT")]
    nos = d[d["Kết luận"].eq("CHƯA CÓ ĐIỂM")]
    wrong = d[d["Sai đối tượng"].astype(bool)]
    c = st.columns(6)
    c[0].metric("Số bài đã chấm", len(d))
    c[1].metric(f"Đạt (≥ {THR}%)", len(ok))
    c[2].metric(f"Chưa đạt (< {THR}%)", len(low))
    c[3].metric("Chưa có điểm", len(nos))
    c[4].metric("Field chưa xong", int((~d["field_done"].astype(bool)).sum()))
    c[5].metric("🚨 Sai đối tượng", len(wrong))
    if len(wrong):
        st.error(f"🚨 Có {len(wrong)} bài Plus phỏng vấn SAI ĐỐI TƯỢNG (MSNV không thuộc nhân viên bán hàng, "
                 "trưởng/quản lý cửa hàng, trợ lý cửa hàng hoặc vị trí AIO theo danh sách nhân sự).")
        wt = alert_table(wrong)
        show_df(wt, height=300)
        dl_button(wt, "Sai_doi_tuong", "Bai_Plus_sai_doi_tuong.xlsx", "dl_wrong_tab")
    elif d["Kiểm tra đối tượng"].eq("Chưa kiểm tra").all():
        st.warning("Chưa kiểm tra được đối tượng phỏng vấn vì chưa có danh sách nhân sự (nhan_su.csv).")

    kq = np.where(d["Kết luận"].eq("ĐẠT"), "Đạt",
                  np.where(d["Kết luận"].str.startswith("CHƯA ĐẠT"), f"Chưa đạt (<{THR}%)", "Chưa có điểm"))
    cmap = {"Đạt": "#12b76a", f"Chưa đạt (<{THR}%)": "#f04438", "Chưa có điểm": "#98a2b3"}
    a, b = st.columns(2)
    with a:
        g = d.assign(KQ=kq).groupby(["Lead", "KQ"]).size().reset_index(name="Số bài")
        bar_chart(g, "Lead", "Số bài", "Kết quả trả bài theo Lead", barmode="stack", color="KQ", color_discrete_map=cmap)
    with b:
        pie_chart(["Đạt", f"Chưa đạt (<{THR}%)", "Chưa có điểm"], [len(ok), len(low), len(nos)],
                  "Tỷ lệ đạt / chưa đạt", cmap)
    g = d.assign(KQ=kq).groupby(["plus_item", "KQ"]).size().reset_index(name="Số bài") \
        .rename(columns={"plus_item": "Plus"})
    bar_chart(g, "Plus", "Số bài", "Kết quả theo Plus 1 → 5", barmode="stack", color="KQ", color_discrete_map=cmap)

    def fmt(x):
        y = pd.DataFrame({
            "Lead": x["Lead"], "Nhân viên": x["employee_name"], "MSNV": x["employee_id"],
            "Mã cửa hàng": x["store_code"], "Plus": x["plus_item"],
            "Vị trí": x["Vị trí (nhân sự)"], "Đối tượng": x["Kiểm tra đối tượng"], "Điểm": x["score"],
            "Điểm tối đa": x["max_score"], "% điểm": x["pct"],
            "Trạng thái Field": np.where(x["field_done"].astype(bool), "Đã xong", "Chưa xong"),
            "Trạng thái QC": x["qc_status"].map(QC_LABEL).fillna("Khác"),
            "Người chấm (Field)": x["field_name"], "Kết luận": x["Kết luận"]})
        return y

    section(f"Nhân sự chưa đạt (< {THR}%) – cần trả bài đợt 2 và follow")
    lt = fmt(low.sort_values("pct"))
    show_df(lt, height=460, column_config={"% điểm": st.column_config.NumberColumn(format="%.1f%%")})
    if not lt.empty:
        dl_button(lt, "Chua_dat_tra_bai_dot2", "Nhan_su_chua_dat_tra_bai_dot2.xlsx", "dl_low")
    with st.expander("Xem tất cả bài đã chấm"):
        allv = fmt(d.sort_values("pct"))
        show_df(allv, height=460, column_config={"% điểm": st.column_config.NumberColumn(format="%.1f%%")})
        dl_button(allv, "Tat_ca_bai_Plus", "Tat_ca_bai_Plus_hien_tai.xlsx", "dl_all_iv")


def raw_plan_viewer(P, file_bytes):
    plans = P.loc[P["Bị từ chối"], "Tên Plan"].tolist()
    if not plans:
        return
    with st.expander("🔍 Xem dòng gốc trong file raw của một plan bị từ chối (để kiểm tra ghi chú QC)"):
        pick = st.selectbox("Chọn plan", plans, key="raw_plan_pick")
        shown = False
        for name, df in load_report(file_bytes, APP_VERSION).items():
            if "Tên Plan" not in df.columns:
                continue
            sub = df[df["Tên Plan"].astype(str).str.strip() == pick]
            if len(sub):
                shown = True
                st.caption(f"Sheet {name}: {len(sub)} dòng · cột ghi chú đọc được: "
                           + (", ".join(c for c in sub.columns if c == "QC note" or is_note_col(c)) or "không có"))
                show_df(sub.head(60), height=300)
        if not shown:
            st.info("Không tìm thấy dòng nào của plan này trong file raw.")


def tab_reject(P, file_bytes=None, file_info=""):
    r = text_filter(lead_filter(P[P["Bị từ chối"]]), ["store", "Tên Plan", "Lead"], search)
    if r.empty:
        st.success("Không có plan nào bị từ chối hoặc yêu cầu bổ sung.")
        return
    n_no = int(r["Ghi chú QC"].eq("").sum())
    c = st.columns(3)
    c[0].metric("Plan bị từ chối / yêu cầu bổ sung", len(r))
    c[1].metric("Đã có ghi chú QC", len(r) - n_no)
    c[2].metric("Chưa có ghi chú trong file raw", n_no)
    if n_no:
        st.info(f"{n_no} plan chưa có ghi chú trong file raw đang dùng ({file_info or 'file đã nạp'}). "
                "Nếu trên hệ thống QC đã ghi chú, rất có thể file được xuất TRƯỚC khi QC ghi — hãy xuất lại và nạp file mới. "
                "Còn nếu file mới vẫn thiếu, mở mục 'Xem dòng gốc' bên dưới để xem ghi chú nằm ở cột nào.")
    a, b = st.columns(2)
    with a:
        bar_chart(r.groupby("Nghiệp vụ").size().reset_index(name="Số plan"), "Nghiệp vụ", "Số plan",
                  "Plan bị từ chối theo nghiệp vụ")
    with b:
        bar_chart(r.groupby("Lead").size().reset_index(name="Số plan"), "Lead", "Số plan", "Plan bị từ chối theo Lead")
    out = pd.DataFrame({"Nghiệp vụ": r["Nghiệp vụ"], "Lead": r["Lead"], "Mã cửa hàng": r["store"],
                        "Hạng mục": r["Hạng mục"], "Tên plan": r["Tên Plan"],
                        "Trạng thái QC": r["QC"].map(QC_LABEL).fillna("Khác"),
                        "Lý do": r["Ghi chú QC"].replace("", "Chưa có ghi chú QC trong file raw")}).sort_values(["Nghiệp vụ", "Lead"])
    section("Danh sách plan bị từ chối / yêu cầu bổ sung")
    show_df(out, height=520, column_config={"Lý do": st.column_config.TextColumn(width="large")})
    dl_button(out, "Plan_bi_tu_choi", "Plan_bi_tu_choi.xlsx", "dl_rej")
    if file_bytes is not None:
        raw_plan_viewer(P, file_bytes)


def tab_validation(P, bundle, label):
    sheets = bundle["sheets"]
    n_flag = int((stores["Mystery"] == "Có").sum()) if not stores.empty else 0
    n_l2 = int((stores["L2"] == "Có").sum()) if not stores.empty else 0
    checks = [("Sheet Trade Audit", "Có" if "Trade Audit" in sheets else "THIẾU"),
              ("Sheet Trade Audit Plus", "Có" if "Trade Audit Plus" in sheets else "THIẾU"),
              ("Sheet Mystery Audit", "Có" if "Mystery Audit" in sheets else "THIẾU"),
              ("Các giá trị cột Chấm trong file", ", ".join(bundle["rounds"]) or "không có"),
              ("Số cửa hàng trong danh sách (store_master.csv)", len(stores)),
              ("Số cửa hàng được gắn cờ Mystery (cần = 125)", n_flag if n_flag else "THIẾU – cần upload store_master.csv bản mới"),
              ("Số cửa hàng thuộc Lần 2 (cần = 174)", n_l2 if n_l2 else "THIẾU – cần upload store_master.csv bản mới"),
              ("Số nhân sự trong danh sách nhân sự", len(staff) if len(staff) else "THIẾU – cần file nhan_su.csv"),
              ("Số bài Plus sai đối tượng", int(bundle["IV"]["Sai đối tượng"].sum())
               if "Sai đối tượng" in bundle["IV"].columns else "Chưa kiểm tra"),
              ("Plan chưa nhận diện được hạng mục", int(P["Hạng mục"].isin(["Trade khác", "Plus ?"]).sum())),
              ("Plan có trạng thái QC không nhận diện được", int(P["QC"].eq("UNKNOWN").sum())),
              ("Cửa hàng có trong raw nhưng không có trong danh sách (không tính CAMPUS)",
               len([c for c in set(P["store"]) - set(stores["Mã cửa hàng"]) if (norm(CAMPUS_KW).upper() or "CAMPUS") not in c]))]
    note_rows = []
    if bundle.get("fb") is not None:
        for sh, df in load_report(bundle["fb"], APP_VERSION).items():
            for c in df.columns:
                if c == "QC note" or is_note_col(c):
                    note_rows.append({"Sheet": sh, "Cột ghi chú": c,
                                      "Số dòng có nội dung": int((df[c].notna() & df[c].astype(str).str.strip().ne("")).sum()),
                                      "Dùng làm": "Ghi chú QC (ưu tiên)" if c == "QC note" else "Dự phòng khi 'QC note' trống"})
    section("Kiểm tra nguồn dữ liệu")
    show_df(pd.DataFrame(checks, columns=["Nội dung kiểm tra", "Kết quả"]).astype(str))
    if note_rows:
        section("Cột ghi chú đọc được từ file raw", "Nếu thiếu cột chứa ghi chú QC của bạn, gửi tên cột đó cho người hỗ trợ")
        show_df(pd.DataFrame(note_rows))
    else:
        st.warning("Không tìm thấy cột ghi chú nào (QC note / Ghi chú / Note…) trong file raw.")
    section("Số plan theo nghiệp vụ, hệ thống và hạng mục", "Dùng để phát hiện hạng mục bị nhận diện sai")
    show_df(P.groupby(["Nghiệp vụ", "Hệ thống", "Hạng mục"]).size().reset_index(name="Số plan"))
    if not stores.empty:
        diff = P[(P["lead_raw"] != "") & (P["Lead"] != P["lead_raw"]) & P["store"].isin(stores["Mã cửa hàng"])]
        if not diff.empty:
            section("Cửa hàng có Lead trong raw khác danh sách", "App đang dùng Lead theo danh sách cửa hàng")
            show_df(diff.drop_duplicates("store")[["store", "lead_raw", "Lead"]]
                    .rename(columns={"store": "Mã cửa hàng", "lead_raw": "Lead trong raw", "Lead": "Lead theo danh sách"}))
    miss = sorted(set(P["store"]) - set(stores["Mã cửa hàng"]))
    camp = [c for c in miss if (norm(CAMPUS_KW).upper() or "CAMPUS") in c]
    other = [c for c in miss if c not in camp]
    if camp:
        st.info(f"{len(camp)} mã CAMPUS nằm ngoài danh sách cửa hàng (bình thường): " + ", ".join(camp))
    if other:
        st.warning(f"{len(other)} mã cửa hàng có trong raw nhưng chưa có trong danh sách cửa hàng "
                   "(Lead sẽ lấy theo raw). Nếu gần như toàn bộ mã đều bị báo, danh sách cửa hàng chưa được nạp.")
        with st.expander("Xem các mã này"):
            st.write(", ".join(other))


def clean_name(v):
    return "" if pd.isna(v) else str(v).strip()


def token_filter(df, cols, q):
    """Tìm nhiều từ khóa một lúc (ví dụ dán nhiều mã cửa hàng, cách nhau bằng dấu phẩy / khoảng trắng / xuống dòng)."""
    toks = [norm(t) for t in re.split(r"[,;\s]+", str(q or "")) if norm(t)]
    if not toks or df is None or df.empty:
        return df
    hay = pd.Series("", index=df.index)
    for c in cols:
        hay = hay + " " + df[c].fillna("").astype(str).apply(norm)
    return df[hay.str.contains("|".join(re.escape(t) for t in toks), regex=True)]


FOLLOW_COLS = ["STT", "Mã cửa hàng", "Địa chỉ cửa hàng", "Lead", "Nghiệp vụ", "Hạng mục", "Tên plan", "Người thực hiện",
               "Tài khoản", "Tình trạng", "Lý do QC", "Trạng thái yêu cầu", "Nội dung yêu cầu", "Ngày gửi",
               "Phản hồi của Field", "Ngày bổ sung"]


def followup_df(sub, reqs, e2m):
    """File theo dõi bổ sung: mỗi plan một dòng, kèm trạng thái yêu cầu mới nhất đã gửi."""
    last = {r["plan"]: r for r in reqs}  # yêu cầu mới nhất của từng plan
    rows = []
    for i, (_, r) in enumerate(sub.iterrows(), 1):
        q = last.get(r["Tên Plan"], {})
        who = clean_name(r["Field name"])
        rows.append({"STT": i, "Mã cửa hàng": r["store"], "Địa chỉ cửa hàng": r.get("Địa chỉ", ""), "Lead": r["Lead"],
                     "Nghiệp vụ": r["Nghiệp vụ"], "Hạng mục": r["Hạng mục"], "Tên plan": r["Tên Plan"],
                     "Người thực hiện": who, "Tài khoản": e2m.get(norm(who), ""),
                     "Tình trạng": STATUS_LABEL.get(r["_st"], r["_st"]),
                     "Lý do QC": r["Ghi chú QC"] or "Chưa có ghi chú QC",
                     "Trạng thái yêu cầu": q.get("status", "Chưa gửi"), "Nội dung yêu cầu": q.get("message", ""),
                     "Ngày gửi": q.get("created", ""), "Phản hồi của Field": q.get("field_reply", ""),
                     "Ngày bổ sung": q.get("done_at", "")})
    return pd.DataFrame(rows, columns=FOLLOW_COLS)


def followup_by_person(fu):
    if fu.empty:
        return pd.DataFrame(columns=["Người thực hiện", "Tài khoản", "Số plan", "Số cửa hàng", "Đã gửi yêu cầu", "Chưa gửi yêu cầu"])
    d = fu.assign(_who=fu["Người thực hiện"].replace("", "(chưa có người thực hiện)"))
    g = d.groupby("_who").agg(**{"Tài khoản": ("Tài khoản", "first"), "Số plan": ("Tên plan", "size"),
                                 "Số cửa hàng": ("Mã cửa hàng", "nunique"),
                                 "Đã gửi yêu cầu": ("Trạng thái yêu cầu", lambda s: int((s != "Chưa gửi").sum())),
                                 "Chưa gửi yêu cầu": ("Trạng thái yêu cầu", lambda s: int((s == "Chưa gửi").sum()))})
    return g.reset_index().rename(columns={"_who": "Người thực hiện"}).sort_values("Số plan", ascending=False)


def followup_message(person, g, sender, note="Bạn kiểm tra và bổ sung giúp mình, xong báo lại nhé."):
    lines = [f"Chào {person},", f"{sender} nhờ bạn bổ sung {len(g)} plan sau:"]
    for i, (_, r) in enumerate(g.iterrows(), 1):
        lines.append(f"{i}. {r['Mã cửa hàng']} – {r['Nghiệp vụ']} {r['Hạng mục']}: {r['Lý do QC']}")
    lines += [note, "Cảm ơn bạn!"]
    return "\n".join(lines)


def followup_messages(fu, sender, note="Bạn kiểm tra và bổ sung giúp mình, xong báo lại nhé."):
    out = {}
    for who, g in fu.groupby(fu["Người thực hiện"].replace("", "(chưa có người thực hiện)")):
        out[who] = followup_message(who, g, sender, note)
    return out


def followup_sheets(fu, sender):
    msgs = followup_messages(fu, sender)
    by = followup_by_person(fu)
    mdf = pd.DataFrame({"Người thực hiện": list(msgs), "Số plan": [int((fu["Người thực hiện"].replace("", "(chưa có người thực hiện)") == k).sum()) for k in msgs],
                        "Tin nhắn gửi nhân sự": list(msgs.values())})
    return {"Cần bổ sung": fu, "Theo người thực hiện": by, "Tin nhắn gửi nhân sự": mdf}, msgs


def stamp():
    return pd.Timestamp.now(tz="Asia/Ho_Chi_Minh").strftime("%Y%m%d_%H%M")


XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def editor(df, **kw):
    try:
        return st.data_editor(df, hide_index=True, **STRETCH, **kw)
    except Exception:  # noqa: BLE001  (phiên bản Streamlit cũ không nhận width)
        return st.data_editor(df, hide_index=True, **kw)


PLUS_MIN = 2  # cửa hàng CPS hoàn thành khi đủ 4 hạng mục và từ 2 bài Plus hoàn thành trở lên
STORE_STATUS = {"DONE": ("✅ Hoàn thành", "ok"), "REJECT": ("❌ Cần bổ sung", "bad"),
                "PROGRESS": ("🕓 Đang thực hiện", "warn"), "NOT_STARTED": ("⏳ Chưa thực hiện", "idle")}
STORE_ORDER = {"REJECT": 0, "PROGRESS": 1, "NOT_STARTED": 2, "DONE": 3}
ITEM_ICON = {"DONE": "✅", "REJECT": "❌", "WAIT_QC": "🕓", "NOT_FIELD": "⏳", "NONE": "▫️"}
ITEM_CLS = {"DONE": "ok", "REJECT": "bad", "WAIT_QC": "warn", "NOT_FIELD": "idle", "NONE": "idle"}
ITEM_TEXT = {"DONE": "hoàn thành", "REJECT": "bị từ chối", "WAIT_QC": "chờ QC duyệt", "NOT_FIELD": "chưa làm xong",
             "NONE": "chưa có plan"}
SP_COLS = ["store", "Địa chỉ", "Lead", "Hệ thống", "stt", "Trạng thái", "comp", "Plus hoàn thành", "Plus chờ QC",
           "Plus bị từ chối", "Plus tổng", "Plus cần", "Còn thiếu", "Người thực hiện"]


def store_progress_df(Pall):
    """Tiến độ theo cửa hàng (CPS / DTV). CPS hoàn thành = đủ 4 hạng mục (Field + QC xong) và từ PLUS_MIN bài Plus hoàn thành;
    các bài Plus còn lại giữ nguyên trạng thái. DTV hoàn thành = hạng mục Trade Audit DTV hoàn thành."""
    t = Pall[Pall["Nghiệp vụ"].isin(["Trade", "Plus"]) & Pall["Hệ thống"].isin(["CPS", "DTV"])]
    if t.empty:
        return pd.DataFrame(columns=SP_COLS)
    best = pick_best(t[t["Nghiệp vụ"] == "Trade"])
    bm = {(r["store"], r["Hạng mục"]): r for _, r in best.iterrows()}
    plus_by = {k: g for k, g in t[t["Nghiệp vụ"] == "Plus"].groupby("store")}
    rows = []
    for code, g in t.groupby("store"):
        system = g["Hệ thống"].iloc[0]
        items = CPS_ITEMS if system == "CPS" else DTV_ITEMS
        comp = {}
        for it in items:
            r = bm.get((code, it))
            comp[it] = ({"st": r["_st"], "who": clean_name(r["Field name"]), "note": r["Ghi chú QC"]} if r is not None
                        else {"st": "NONE", "who": "", "note": ""})
        pg = plus_by.get(code, g.iloc[0:0])
        n_done, n_wait = int(pg["Hoàn thành"].sum()), int((pg["_st"] == "WAIT_QC").sum())
        n_rej, n_tot = int(pg["Bị từ chối"].sum()), len(pg)
        need = PLUS_MIN if system == "CPS" else 0
        plus_ok = n_done >= need
        all_items = all(v["st"] == "DONE" for v in comp.values())
        rejected = any(v["st"] == "REJECT" for v in comp.values()) or (not plus_ok and n_rej > 0)
        started = any(v["st"] in ("DONE", "WAIT_QC", "REJECT") for v in comp.values()) or (n_done + n_wait + n_rej) > 0
        stt = "DONE" if (all_items and plus_ok) else "REJECT" if rejected else "PROGRESS" if started else "NOT_STARTED"
        missing = [f"{it}: {ITEM_TEXT[v['st']]}" for it, v in comp.items() if v["st"] != "DONE"]
        if not plus_ok:
            extra = (f", {n_wait} chờ QC" if n_wait else "") + (f", {n_rej} bị từ chối" if n_rej else "")
            missing.append(f"Plus: mới {n_done}/{need} bài hoàn thành{extra}")
        rows.append({"store": code, "Địa chỉ": g["Địa chỉ"].iloc[0], "Lead": g["Lead"].iloc[0], "Hệ thống": system, "stt": stt,
                     "Trạng thái": STORE_STATUS[stt][0], "comp": comp, "Plus hoàn thành": n_done, "Plus chờ QC": n_wait,
                     "Plus bị từ chối": n_rej, "Plus tổng": n_tot, "Plus cần": need, "Còn thiếu": " · ".join(missing),
                     "Người thực hiện": ", ".join(sorted({clean_name(x) for x in g["Field name"] if clean_name(x)}))})
    out = pd.DataFrame(rows, columns=SP_COLS)
    out["_o"] = out["stt"].map(STORE_ORDER)
    return out.sort_values(["_o", "store"]).drop(columns="_o").reset_index(drop=True)


def store_card_html(r, me):
    label, cls = STORE_STATUS[r["stt"]]
    chips, others = [], []
    for it, v in r["comp"].items():
        txt = f"{it} {ITEM_ICON[v['st']]}"
        if v["who"] and norm(v["who"]) not in me:
            others.append(f"{it} ({v['who']})")
        chips.append(f'<span class="sc {ITEM_CLS[v["st"]]}">{html.escape(txt)}</span>')
    if r["Plus cần"]:
        ok = r["Plus hoàn thành"] >= r["Plus cần"]
        pc = "ok" if ok else ("bad" if r["Plus bị từ chối"] else "warn")
        chips.append(f'<span class="sc {pc}">Plus {r["Plus hoàn thành"]}/{r["Plus cần"]}+ {"✅" if ok else "⏳"}</span>')
    plus_line = ""
    if r["Plus cần"]:
        bits = [f'{r["Plus hoàn thành"]} hoàn thành']
        if r["Plus chờ QC"]:
            bits.append(f'{r["Plus chờ QC"]} chờ QC')
        if r["Plus bị từ chối"]:
            bits.append(f'{r["Plus bị từ chối"]} bị từ chối')
        plus_line = f'<div class="splus">Bài Plus: {" · ".join(bits)} / {r["Plus tổng"]} bài</div>'
    miss = ('<div class="smiss ok">Đủ điều kiện hoàn thành (các bài Plus còn lại giữ nguyên trạng thái).</div>'
            if r["stt"] == "DONE" else f'<div class="smiss">Còn thiếu: {html.escape(r["Còn thiếu"])}</div>')
    oth = f'<div class="sother">Do người khác thực hiện: {html.escape(", ".join(others))}</div>' if others else ""
    addr = f'<div class="saddr">{html.escape(str(r["Địa chỉ"]))}</div>' if r["Địa chỉ"] else ""
    return (f'<div class="scard {cls}"><div class="shead"><span class="scode">{html.escape(r["store"])}</span>'
            f'<span class="sbadge {cls}">{label}</span></div>{addr}<div class="schips">{"".join(chips)}</div>'
            f'{plus_line}{miss}{oth}</div>')


def store_export_df(sp):
    rows = []
    for _, r in sp.iterrows():
        d = {"Mã cửa hàng": r["store"], "Địa chỉ cửa hàng": r["Địa chỉ"], "Lead": r["Lead"], "Hệ thống": r["Hệ thống"],
             "Trạng thái": r["Trạng thái"]}
        for it, v in r["comp"].items():
            d[it] = f"{ITEM_ICON[v['st']]} {ITEM_TEXT[v['st']]}" + (f" ({v['who']})" if v["who"] else "")
        d.update({"Plus hoàn thành": r["Plus hoàn thành"], "Plus chờ QC": r["Plus chờ QC"], "Plus bị từ chối": r["Plus bị từ chối"],
                  "Plus tổng": r["Plus tổng"], "Còn thiếu": r["Còn thiếu"] or "Đủ điều kiện", "Người thực hiện": r["Người thực hiện"]})
        rows.append(d)
    df = pd.DataFrame(rows)
    first = ["Mã cửa hàng", "Địa chỉ cửa hàng", "Lead", "Hệ thống", "Trạng thái"] + [c for c in CPS_ITEMS + DTV_ITEMS if c in df.columns]
    return df[first + [c for c in df.columns if c not in first]] if len(df) else df


def tab_field_staff(P):
    t = text_filter(lead_filter(P), ["Field name", "Tên Plan", "store"], search)
    users = load_users(users_signature())
    acct = name_email_map() if AUTH_ON else {}
    reqs = load_requests()
    open_by = pd.Series([norm(r.get("to_name", "")) for r in reqs if r.get("status") == "Mở"], dtype=str).value_counts().to_dict()
    t = t.assign(_n=t["Field name"].fillna("").astype(str).str.strip().replace("", "(chưa gán)"))
    g = t.groupby("_n").agg(**{
        "Tổng plan": ("Tên Plan", "size"), "Hoàn thành": ("Hoàn thành", "sum"),
        "Chờ QC": ("_st", lambda s: int((s == "WAIT_QC").sum())), "Bị từ chối": ("Bị từ chối", "sum"),
        "Chưa Field xong": ("_st", lambda s: int((s == "NOT_FIELD").sum()))}).reset_index().rename(columns={"_n": "Nhân sự Field"})
    scope_lead = MY_LEAD or (selected_leader if selected_leader != "Tất cả" else "")
    if AUTH_ON and not users.empty:  # thêm tài khoản Field thuộc Lead nhưng chưa có plan nào
        mine = users[(users["role"] == "field") & ((users["lead"] == scope_lead) if scope_lead else True)]
        have = {norm(x) for x in g["Nhân sự Field"]}
        extra = [{"Nhân sự Field": r["display_name"], "Tổng plan": 0, "Hoàn thành": 0, "Chờ QC": 0, "Bị từ chối": 0,
                  "Chưa Field xong": 0} for _, r in mine.iterrows() if norm(r["display_name"]) not in have]
        if extra:
            g = pd.concat([g, pd.DataFrame(extra).drop_duplicates("Nhân sự Field")], ignore_index=True)
    if g.empty:
        st.info("Chưa có nhân sự Field nào để hiển thị.")
        return
    sp_all = store_progress_df(P)
    st_stt = dict(zip(sp_all["store"], sp_all["stt"]))
    tt = t[t["Nghiệp vụ"].isin(["Trade", "Plus"]) & t["Hệ thống"].isin(["CPS", "DTV"])]
    owned = tt.groupby("_n")["store"].agg(lambda x: set(x)).to_dict()
    g.insert(1, "Cửa hàng được giao", g["Nhân sự Field"].map(lambda n: len(owned.get(n, ()))))
    g.insert(2, "Cửa hàng hoàn thành", g["Nhân sự Field"].map(lambda n: sum(1 for c in owned.get(n, ()) if st_stt.get(c) == "DONE")))
    g.insert(3, "% cửa hàng hoàn thành", [pct(a, b) if b else np.nan for a, b in zip(g["Cửa hàng hoàn thành"], g["Cửa hàng được giao"])])
    g["% hoàn thành"] = [pct(a, b) if b else np.nan for a, b in zip(g["Hoàn thành"], g["Tổng plan"])]
    g["Yêu cầu đang mở"] = g["Nhân sự Field"].apply(lambda n: int(open_by.get(norm(n), 0)))
    g["Tài khoản"] = g["Nhân sự Field"].apply(lambda n: acct.get(norm(n), "—"))
    g = g.sort_values(["Tổng plan", "Nhân sự Field"], ascending=[False, True]).reset_index(drop=True)
    c = st.columns(4)
    c[0].metric("Nhân sự Field", len(g))
    c[1].metric("Đang có plan", int((g["Tổng plan"] > 0).sum()))
    c[2].metric("Plan hoàn thành", int(g["Hoàn thành"].sum()))
    c[3].metric("Plan bị từ chối", int(g["Bị từ chối"].sum()))
    top = g[g["Tổng plan"] > 0].head(25)
    if not top.empty:
        long = top.melt(id_vars="Nhân sự Field", value_vars=["Hoàn thành", "Chờ QC", "Bị từ chối", "Chưa Field xong"],
                        var_name="Tình trạng", value_name="Số plan")
        fig = px.bar(long, x="Nhân sự Field", y="Số plan", color="Tình trạng", barmode="stack", text_auto=True,
                     title="Kết quả audit từng nhân sự Field",
                     color_discrete_map={"Hoàn thành": "#12b76a", "Chờ QC": "#f79009", "Bị từ chối": "#f04438",
                                         "Chưa Field xong": "#98a2b3"})
        show_chart(fig)
    section("Bảng kết quả từng nhân sự Field", "Chọn một người ở bên dưới để xem chi tiết plan của họ")
    show_df(g, height=420, column_config=PCT_CFG(["% cửa hàng hoàn thành", "% hoàn thành"]))
    pick = st.selectbox("Xem chi tiết plan của", ["—"] + g["Nhân sự Field"].tolist(), key="staff_pick")
    if pick != "—":
        d = t[t["_n"] == pick]
        show_df(pd.DataFrame({"Nghiệp vụ": d["Nghiệp vụ"], "Mã cửa hàng": d["store"], "Hạng mục": d["Hạng mục"],
                              "Tên plan": d["Tên Plan"], "Tình trạng": d["_st"].map(STATUS_LABEL),
                              "Lý do / ghi chú QC": d["Ghi chú QC"]}), height=320)


REQ_KINDS = {"Bị từ chối / yêu cầu bổ sung": "REJ", "Đã Field xong – chờ QC duyệt": "WAIT_QC",
             "Chưa Field xong": "NOT_FIELD", "Tất cả plan chưa hoàn thành": "ALL"}


def sender_label():
    if ROLE == "lead":
        return f"Lead {MY_LEAD}"
    return f"Lead {selected_leader}" if selected_leader != "Tất cả" else "Quản trị"


def tab_requests(P):
    section("Gửi yêu cầu bổ sung cho nhân sự Field",
            "Tìm theo mã cửa hàng, chọn plan rồi gửi: nhân sự Field sẽ thấy yêu cầu trong màn hình của họ")
    kind = REQ_KINDS[st.selectbox("Loại plan", list(REQ_KINDS), key="req_kind")]
    base = lead_filter(P)
    mask = {"REJ": base["Bị từ chối"], "WAIT_QC": base["_st"].eq("WAIT_QC"), "NOT_FIELD": base["_st"].eq("NOT_FIELD"),
            "ALL": ~base["Hoàn thành"]}[kind]
    pool = base[mask]
    f1, f2, f3 = st.columns([2.2, 1, 1.4])
    q = f1.text_area("🔎 Tìm mã cửa hàng / tên plan / người thực hiện", key="req_search", height=70,
                     placeholder="Dán 1 hoặc nhiều mã cửa hàng, cách nhau bằng dấu phẩy, khoảng trắng hoặc xuống dòng")
    sel_nv = f2.multiselect("Nghiệp vụ", sorted(pool["Nghiệp vụ"].unique()), key="req_nv")
    sel_who = f3.multiselect("Người thực hiện", sorted({clean_name(x) for x in pool["Field name"] if clean_name(x)}), key="req_who")
    cand = pool
    if sel_nv:
        cand = cand[cand["Nghiệp vụ"].isin(sel_nv)]
    if sel_who:
        cand = cand[cand["Field name"].apply(clean_name).isin(sel_who)]
    cand = token_filter(cand, ["store", "Tên Plan", "Field name"], q)
    cand = text_filter(cand, ["store", "Tên Plan", "Field name"], search).reset_index(drop=True)
    st.caption(f"Đang hiển thị {len(cand)} / {len(pool)} plan")
    reqs_all = load_requests()
    e2m = name_email_map() if AUTH_ON else {}
    sender = sender_label()
    if cand.empty:
        st.success("Không có plan nào khớp bộ lọc.")
    else:
        sel_all = st.checkbox("Chọn tất cả plan đang hiển thị", key="req_selall")
        tbl = pd.DataFrame({"Chọn": bool(sel_all), "Mã cửa hàng": cand["store"], "Nghiệp vụ": cand["Nghiệp vụ"], "Hạng mục": cand["Hạng mục"],
                            "Tên plan": cand["Tên Plan"], "Người thực hiện": cand["Field name"].apply(clean_name),
                            "Tình trạng": cand["_st"].map(STATUS_LABEL),
                            "Lý do QC": cand["Ghi chú QC"].replace("", "Chưa có ghi chú QC")})
        ed = editor(tbl, disabled=[c for c in tbl.columns if c != "Chọn"], height=380,
                    key=f"req_editor_{kind}_{int(sel_all)}_{abs(hash(tuple(cand['Tên Plan']))) % 10**8}",
                    column_config={"Chọn": st.column_config.CheckboxColumn("Chọn", default=False)})
        msg = st.text_area("Nội dung yêu cầu", "Vui lòng bổ sung / chấm lại plan này theo ghi chú QC và cập nhật lại sớm.",
                           key="req_msg")
        n_sel = int(ed["Chọn"].sum())
        if st.button(f"📨 Gửi yêu cầu cho {n_sel} plan đã chọn", disabled=n_sel == 0, type="primary", key="req_send"):
            new, no_owner = [], 0
            for i in ed.index[ed["Chọn"]]:
                r = cand.loc[i]
                nm = clean_name(r["Field name"])
                if not nm:
                    no_owner += 1
                    continue
                new.append({"created": now_str(), "plan": r["Tên Plan"], "store": r["store"], "item": r["Hạng mục"],
                            "kind": r["Nghiệp vụ"], "reason": r["Ghi chú QC"], "to_name": nm, "to_email": e2m.get(norm(nm), ""),
                            "from_email": USER["email"], "from_lead": r["Lead"], "message": msg, "status": "Mở",
                            "done_at": "", "field_reply": ""})
            a, s_ = add_requests(new) if new else (0, 0)
            if a:
                st.success(f"Đã gửi {a} yêu cầu." + (f" Bỏ qua {s_} plan đang có yêu cầu mở." if s_ else ""))
            if s_ and not a:
                st.info(f"Bỏ qua {s_} plan vì đang có yêu cầu mở.")
            if no_owner:
                st.warning(f"{no_owner} plan chưa có người thực hiện trong dữ liệu nên chưa gửi được.")
        section("Xuất file theo dõi và tin nhắn gửi nhân sự",
                "File Excel gồm 3 sheet: danh sách cần bổ sung (kèm trạng thái yêu cầu), tổng hợp theo người, tin nhắn soạn sẵn")
        fu = followup_df(cand, reqs_all, e2m)
        sheets, msgs = followup_sheets(fu, sender)
        e1, e2 = st.columns(2)
        e1.download_button(f"📥 Xuất Excel – {len(fu)} plan đang hiển thị", data=to_excel_multi(sheets),
                           file_name=f"yeu_cau_bo_sung_{stamp()}.xlsx", mime=XLSX_MIME, key="req_dl_all")
        if n_sel:
            sh2, _ = followup_sheets(followup_df(cand.loc[ed.index[ed["Chọn"]]], reqs_all, e2m), sender)
            e2.download_button(f"📥 Xuất Excel – {n_sel} plan đã chọn", data=to_excel_multi(sh2),
                               file_name=f"yeu_cau_bo_sung_da_chon_{stamp()}.xlsx", mime=XLSX_MIME, key="req_dl_sel")
        who = st.selectbox("Tin nhắn soạn sẵn gửi cho", list(msgs), key="req_msg_who")
        st.caption("Bấm biểu tượng sao chép ở góc phải khung bên dưới rồi dán vào Zalo / tin nhắn gửi nhân sự.")
        st.code(msgs[who], language=None)

    section("Yêu cầu đã gửi", "Trạng thái: Mở → Đã bổ sung (nhân sự Field bấm) → Đã đóng (Lead xác nhận)")
    items = [r for r in load_requests() if IS_ADMIN or r.get("from_lead") == MY_LEAD]
    if selected_leader != "Tất cả" and IS_ADMIN:
        items = [r for r in items if r.get("from_lead") == selected_leader]
    if not items:
        st.info("Chưa có yêu cầu nào.")
        return
    df = pd.DataFrame(items)
    c = st.columns(3)
    c[0].metric("Đang mở", int((df["status"] == "Mở").sum()))
    c[1].metric("Đã bổ sung – chờ xác nhận", int((df["status"] == "Đã bổ sung").sum()))
    c[2].metric("Đã đóng", int((df["status"] == "Đã đóng").sum()))
    g1, g2 = st.columns([2.2, 1])
    fq = g1.text_area("🔎 Tìm trong yêu cầu đã gửi (mã cửa hàng / tên plan / người nhận)", key="req_sent_q", height=70)
    fs = g2.multiselect("Trạng thái", ["Mở", "Đã bổ sung", "Đã đóng"], key="req_sent_s")
    dff = token_filter(df, ["store", "plan", "to_name"], fq)
    if fs:
        dff = dff[dff["status"].isin(fs)]
    view = dff[["id", "created", "status", "store", "kind", "item", "to_name", "message", "field_reply", "done_at", "plan"]].rename(columns={
        "id": "Mã YC", "created": "Gửi lúc", "status": "Trạng thái", "store": "Mã cửa hàng", "kind": "Nghiệp vụ", "item": "Hạng mục",
        "to_name": "Gửi cho", "message": "Nội dung", "field_reply": "Phản hồi của Field", "done_at": "Bổ sung lúc", "plan": "Tên plan"})
    st.caption(f"Đang hiển thị {len(view)} / {len(df)} yêu cầu")
    show_df(view.iloc[::-1], height=360)
    if not dff.empty:
        summ = pd.crosstab(dff["to_name"], dff["status"]).reindex(columns=["Mở", "Đã bổ sung", "Đã đóng"], fill_value=0)
        summ["Tổng"] = summ.sum(axis=1)
        summ = summ.rename_axis("Gửi cho").reset_index().sort_values("Tổng", ascending=False)
        st.download_button(f"📥 Xuất Excel – theo dõi {len(view)} yêu cầu đã gửi",
                           data=to_excel_multi({"Theo dõi yêu cầu": view.iloc[::-1], "Tổng hợp theo người nhận": summ}),
                           file_name=f"theo_doi_yeu_cau_{stamp()}.xlsx", mime=XLSX_MIME, key="req_dl_sent")
    open_ids = df[df["status"] != "Đã đóng"]["id"].tolist()
    close = st.multiselect("Đóng yêu cầu (đã nhận đủ bổ sung)", open_ids, key="req_close")
    if st.button("Đóng các yêu cầu đã chọn", disabled=not close, key="req_close_btn"):
        for rid in close:
            update_request(rid, status="Đã đóng")
        st.rerun()


def field_stores_tab(sp):
    me = MY_NAMES
    f1, f2 = st.columns([3, 2])
    flt = f1.radio("Hiển thị", ["Tất cả", "Chưa hoàn thành", "Cần bổ sung", "Đang thực hiện", "Chưa thực hiện", "Đã hoàn thành"],
                   horizontal=True, key="fld_sfilter")
    q = f2.text_input("🔎 Tìm mã cửa hàng", key="fld_sq", placeholder="Dán 1 hoặc nhiều mã, cách nhau bằng dấu phẩy")
    keep = {"Tất cả": None, "Chưa hoàn thành": ["REJECT", "PROGRESS", "NOT_STARTED"], "Cần bổ sung": ["REJECT"],
            "Đang thực hiện": ["PROGRESS"], "Chưa thực hiện": ["NOT_STARTED"], "Đã hoàn thành": ["DONE"]}[flt]
    d = sp if keep is None else sp[sp["stt"].isin(keep)]
    d = token_filter(d, ["store", "Địa chỉ"], q)
    st.caption(f"Đang hiển thị {len(d)} / {len(sp)} cửa hàng. Cửa hàng được tính hoàn thành khi đủ 4 hạng mục CPS "
               f"(Demo, Tủ máy, Vách/Đảo, CellphoneS) và từ {PLUS_MIN} bài Plus trở lên đã hoàn thành (Field + QC). "
               "Cửa hàng DTV hoàn thành khi hạng mục Trade Audit DTV hoàn thành.")
    if d.empty:
        st.info("Không có cửa hàng nào khớp bộ lọc.")
        return
    st.markdown('<div class="sgrid">' + "".join(store_card_html(r, me) for _, r in d.iterrows()) + "</div>", unsafe_allow_html=True)
    st.download_button(f"📥 Xuất Excel – tiến độ {len(d)} cửa hàng", data=to_excel_multi({"Tiến độ cửa hàng": store_export_df(d)}),
                       file_name=f"tien_do_cua_hang_{stamp()}.xlsx", mime=XLSX_MIME, key="fld_dl_stores")


def field_home(P, P_all, IV, label):
    me = USER.get("display_name") or USER["email"]
    if P.empty:
        st.info(f"Chưa có plan nào được giao cho {me} trong đợt {label}. Nếu bạn nghĩ đây là nhầm lẫn, báo Lead hoặc quản trị.")
        return
    sp_all = store_progress_df(P_all)
    mine = set(P[P["Nghiệp vụ"].isin(["Trade", "Plus"]) & P["Hệ thống"].isin(["CPS", "DTV"])]["store"])
    sp = sp_all[sp_all["store"].isin(mine)].reset_index(drop=True)
    n = len(sp)
    cnt = sp["stt"].value_counts().to_dict() if n else {}
    n_done, n_rej, n_prog, n_ns = cnt.get("DONE", 0), cnt.get("REJECT", 0), cnt.get("PROGRESS", 0), cnt.get("NOT_STARTED", 0)
    if n:
        p = pct(n_done, n)
        if n_done == n:
            msg = "🎉 Bạn đã hoàn thành tất cả cửa hàng được giao."
        else:
            msg = f"Bạn chưa hoàn thành: còn {n - n_done} cửa hàng ({n_rej} cần bổ sung · {n_prog} đang thực hiện · {n_ns} chưa thực hiện)."
        st.markdown(
            f'<div class="fbanner"><div class="ft">Tiến độ cửa hàng của bạn</div>'
            f'<div class="fv">{n_done}<span> / {n} cửa hàng đã hoàn thành</span></div>'
            f'<div class="kbar"><span style="width:{min(max(p, 0), 100)}%;background:{tone(p)}"></span></div>'
            f'<div class="fm">{html.escape(msg)}</div></div>', unsafe_allow_html=True)
        cards = [kpi_card("Cửa hàng được giao", n, "CPS + DTV"),
                 kpi_card("Đã hoàn thành", n_done, "đủ điều kiện", pct(n_done, n)),
                 kpi_card("Đang thực hiện", n_prog, "đã làm một phần / chờ QC"),
                 kpi_card("Cần bổ sung", n_rej, "có plan bị từ chối", None, bad=True),
                 kpi_card("Chưa thực hiện", n_ns, "chưa có plan nào xong")]
        st.markdown('<div class="kpi-row compact">' + "".join(cards) + "</div>", unsafe_allow_html=True)
    else:
        st.info("Bạn chưa có cửa hàng CPS/DTV nào được giao trong đợt này (có thể bạn chỉ phụ trách Mystery / CAMPUS).")
    tot, done = len(P), int(P["Hoàn thành"].sum())
    wait, rej, notf = int((P["_st"] == "WAIT_QC").sum()), int(P["Bị từ chối"].sum()), int((P["_st"] == "NOT_FIELD").sum())
    others = P[~P["Nghiệp vụ"].isin(["Trade", "Plus"]) | ~P["Hệ thống"].isin(["CPS", "DTV"])]
    extra = ""
    if len(others):
        extra = f" · Mystery/CAMPUS: {int(others['Hoàn thành'].sum())}/{len(others)} plan hoàn thành"
    st.caption(f"Tính theo plan: {tot} plan được giao · {done} hoàn thành · {wait} chờ QC · {rej} bị từ chối · {notf} chưa làm xong{extra}")
    my_e2m = {n: USER["email"] for n in MY_NAMES}
    t0, t1, t2, t3 = st.tabs(["🏬 Cửa hàng của tôi", "🔔 Việc cần xử lý", "📋 Tất cả plan của tôi", "🎤 Kết quả Plus của tôi"])
    with t0:
        safe(field_stores_tab, sp)
    with t1:
        fq = st.text_area("🔎 Tìm mã cửa hàng / tên plan", key="fld_q", height=70,
                          placeholder="Dán 1 hoặc nhiều mã cửa hàng, cách nhau bằng dấu phẩy, khoảng trắng hoặc xuống dòng")
        toks = [norm(t) for t in re.split(r"[,;\s]+", fq or "") if norm(t)]
        mine_all = [r for r in load_requests() if (str(r.get("to_email", "")).lower() == USER["email"].lower()
                                                   or norm(r.get("to_name", "")) in MY_NAMES)]
        mine = [r for r in mine_all if r.get("status") in ("Mở", "Đã bổ sung")
                and (not toks or any(t in norm(f"{r.get('store', '')} {r.get('plan', '')}") for t in toks))]
        Pq = token_filter(P, ["store", "Tên Plan"], fq)
        need = Pq[Pq["Bị từ chối"] | Pq["_st"].eq("NOT_FIELD")]
        req_df = pd.DataFrame([{"Mã YC": r.get("id"), "Gửi lúc": r.get("created"), "Trạng thái": r.get("status"),
                                "Mã cửa hàng": r.get("store"), "Nghiệp vụ": r.get("kind"), "Hạng mục": r.get("item"),
                                "Lead": r.get("from_lead"), "Nội dung": r.get("message"), "Ghi chú QC": r.get("reason"),
                                "Phản hồi của tôi": r.get("field_reply"), "Bổ sung lúc": r.get("done_at"),
                                "Tên plan": r.get("plan")} for r in mine_all],
                              columns=["Mã YC", "Gửi lúc", "Trạng thái", "Mã cửa hàng", "Nghiệp vụ", "Hạng mục", "Lead", "Nội dung",
                                       "Ghi chú QC", "Phản hồi của tôi", "Bổ sung lúc", "Tên plan"])
        st.download_button(f"📥 Xuất Excel – {len(need)} plan cần xử lý + yêu cầu từ Lead",
                           data=to_excel_multi({"Cần xử lý của tôi": followup_df(need, load_requests(), my_e2m),
                                                "Yêu cầu từ Lead": req_df}),
                           file_name=f"viec_can_xu_ly_{stamp()}.xlsx", mime=XLSX_MIME, key="fld_dl_need")
        section("Yêu cầu bổ sung từ Lead", f"{sum(r['status'] == 'Mở' for r in mine)} yêu cầu đang chờ bạn")
        if not mine:
            st.success("Không có yêu cầu nào từ Lead." if not toks else "Không có yêu cầu nào khớp mã cửa hàng đã tìm.")
        for r in mine:
            with st.container(border=True):
                st.markdown(f"**{r['store']} · {r['kind']} · {r['item']}**  \n`{r['plan']}`")
                st.caption(f"Gửi lúc {r['created']} · Lead: {r['from_lead']}")
                st.write(r["message"])
                if r.get("reason"):
                    st.warning(f"Ghi chú QC: {r['reason']}")
                if r["status"] == "Mở":
                    reply = st.text_input("Phản hồi (không bắt buộc)", key=f"fr_{r['id']}")
                    if st.button("✅ Tôi đã bổ sung xong", key=f"fd_{r['id']}", type="primary"):
                        update_request(r["id"], status="Đã bổ sung", done_at=now_str(), field_reply=reply)
                        st.rerun()
                else:
                    st.success(f"Bạn đã báo bổ sung lúc {r['done_at']} – chờ Lead xác nhận.")
        section("Plan bị từ chối / cần làm lại")
        d = Pq[Pq["Bị từ chối"]]
        if d.empty:
            st.success("Không có plan nào bị từ chối.")
        else:
            show_df(pd.DataFrame({"Mã cửa hàng": d["store"], "Hạng mục": d["Hạng mục"], "Tên plan": d["Tên Plan"],
                                  "Lý do": d["Ghi chú QC"].replace("", "Chưa có ghi chú QC")}), height=260,
                    column_config={"Lý do": st.column_config.TextColumn(width="large")})
        section("Plan chưa làm xong")
        d = Pq[Pq["_st"] == "NOT_FIELD"]
        if d.empty:
            st.success("Bạn không còn plan nào chưa làm.")
        else:
            show_df(pd.DataFrame({"Mã cửa hàng": d["store"], "Nghiệp vụ": d["Nghiệp vụ"], "Hạng mục": d["Hạng mục"],
                                  "Tên plan": d["Tên Plan"]}), height=260)
    with t2:
        q2 = st.text_area("🔎 Tìm mã cửa hàng / tên plan", key="fld_q2", height=70,
                          placeholder="Dán 1 hoặc nhiều mã cửa hàng, cách nhau bằng dấu phẩy, khoảng trắng hoặc xuống dòng")
        f1, f2 = st.columns(2)
        sel_st = f1.multiselect("Tình trạng", list(STATUS_LABEL.values()), default=[], key="fld_status")
        sel_kind = f2.multiselect("Nghiệp vụ", sorted(P["Nghiệp vụ"].unique()), default=[], key="fld_kind")
        d = P
        if sel_st:
            d = d[d["_st"].map(STATUS_LABEL).isin(sel_st)]
        if sel_kind:
            d = d[d["Nghiệp vụ"].isin(sel_kind)]
        d = text_filter(token_filter(d, ["store", "Tên Plan"], q2), ["store", "Tên Plan"], search)
        st.caption(f"Đang hiển thị {len(d)} / {len(P)} plan")
        show_df(pd.DataFrame({"Nghiệp vụ": d["Nghiệp vụ"], "Mã cửa hàng": d["store"], "Hạng mục": d["Hạng mục"],
                              "Tên plan": d["Tên Plan"], "Tình trạng": d["_st"].map(STATUS_LABEL),
                              "Ghi chú QC": d["Ghi chú QC"]}), height=480)
        st.download_button(f"📥 Xuất Excel – {len(d)} plan đang hiển thị",
                           data=to_excel_multi({"Plan của tôi": followup_df(d, load_requests(), my_e2m)}),
                           file_name=f"plan_cua_toi_{stamp()}.xlsx", mime=XLSX_MIME, key="fld_dl_all")
    with t3:
        if IV is None or IV.empty:
            st.info("Bạn chưa có bài phỏng vấn Plus nào được chấm.")
        else:
            d = IV.copy()
            d["Kết luận"] = d["pct"].apply(lambda v: eval_pct(v, THR))
            show_df(pd.DataFrame({"Nhân viên được phỏng vấn": d["employee_name"], "MSNV": d["employee_id"],
                                  "Mã cửa hàng": d["store_code"], "Plus": d["plus_item"], "Điểm": d["score"],
                                  "Điểm tối đa": d["max_score"], "% điểm": d["pct"], "Kết luận": d["Kết luận"]}).sort_values("% điểm"),
                    height=420, column_config={"% điểm": st.column_config.NumberColumn(format="%.1f%%")})




def tab_accounts(P):
    users = load_users(users_signature())
    if users.empty:
        st.warning("Chưa có file users.csv nên chưa bật đăng nhập: bất kỳ ai có link đều thấy toàn bộ dữ liệu.")
        return
    src = users_source()
    st.info("Đang dùng bản chỉnh sửa lưu trên máy chủ." if src is USERS_LIVE else
            "Đang dùng file users.csv trên GitHub. Khi bạn bấm Lưu, thay đổi được lưu trên máy chủ và có hiệu lực ngay." if src is not None else
            "Đang dùng danh sách tài khoản tích hợp sẵn trong app (chưa thấy users.csv trên GitHub). Khi bạn bấm Lưu, thay đổi được lưu trên máy chủ và có hiệu lực ngay.")
    st.warning("Bản chỉnh sửa lưu trên máy chủ sẽ mất khi app khởi động lại. Sau khi sửa xong, bấm **Tải users.csv** "
               "bên dưới và upload lên GitHub (ghi đè users.csv) để giữ lâu dài.")
    fields = ["hash", "active", "role", "lead", "field_names", "display_name"]
    base_t = {r["key"]: tuple(r[c] for c in fields) for _, r in base_users().iterrows()}
    cur_t = {r["key"]: tuple(r[c] for c in fields) for _, r in users.iterrows()}
    changed = [k for k, v in cur_t.items() if base_t.get(k) != v] + [k for k in base_t if k not in cur_t]
    n_locked = int((users["active"] == "0").sum())
    st.caption(f"Tổng {len(users)} tài khoản · {len(users) - n_locked} đang hoạt động · {n_locked} đã khóa")
    if changed:
        st.error(f"{len(changed)} tài khoản đang có mật khẩu/thông tin/trạng thái khác bản gốc trên GitHub (do nhân viên tự đổi mật khẩu hoặc admin chỉnh sửa). "
                 "Các thay đổi này **mất khi app khởi động lại**: hãy bấm **📥 Tải users.csv hiện tại** ở dưới rồi upload ghi đè `users.csv` lên GitHub.")
    msg = st.session_state.pop("acct_msg", None)
    if msg:
        st.success(msg)
    pws = st.session_state.get("acct_pw")
    if pws:
        section("Mật khẩu ban đầu (chỉ hiện một lần)", "Gửi riêng cho từng người; tải về ngay vì sẽ không xem lại được")
        show_df(pd.DataFrame(pws))
        c1, c2 = st.columns([1, 1])
        with c1:
            st.download_button("📥 Tải danh sách mật khẩu (Excel)", data=pw_xlsx_bytes(pws), key="acct_pw_dl",
                               file_name="mat_khau_moi.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with c2:
            if st.button("Đã lưu, ẩn danh sách này", key="acct_pw_hide"):
                st.session_state.pop("acct_pw", None)
                st.rerun()

    base = users.reset_index(drop=True)[["email", "role", "display_name", "lead", "field_names"]].copy()
    base.insert(0, "_id", range(len(base)))
    base.insert(3, "status", users.reset_index(drop=True)["active"].map(lambda a: "Đã khóa" if a == "0" else "Hoạt động"))
    known_leads = sorted(set(stores["Lead"]) - {""}) if not stores.empty else []
    section("Chỉnh sửa tài khoản", "Sửa trực tiếp trong bảng (đổi cột Trạng thái để khóa / mở khóa). Thêm dòng mới ở cuối bảng; chọn dòng rồi nhấn Delete để xóa tài khoản.")
    ed = editor(base, num_rows="dynamic", height=430, key="acct_editor", column_config={
        "_id": None,
        "email": st.column_config.TextColumn("Tài khoản (email)", required=True),
        "role": st.column_config.SelectboxColumn("Vai trò", options=list(VALID_ROLES), required=True),
        "status": st.column_config.SelectboxColumn("Trạng thái", options=["Hoạt động", "Đã khóa"], required=True),
        "display_name": st.column_config.TextColumn("Tên nhân viên / tên hiển thị"),
        "lead": st.column_config.SelectboxColumn("Lead", options=[""] + known_leads),
        "field_names": st.column_config.TextColumn("Tên người thực hiện trong plan (nhiều tên cách nhau bằng |)", width="large")})
    me_key = USER["email"].strip().lower()
    me_rows = users.reset_index(drop=True).index[users.reset_index(drop=True)["key"] == me_key].tolist()
    me_id = int(me_rows[0]) if me_rows else None
    b1, b2 = st.columns([1, 3])
    with b1:
        save = st.button("💾 Lưu thay đổi", type="primary", key="acct_save")
    with b2:
        st.download_button("📥 Tải users.csv hiện tại (để cập nhật GitHub)", key="acct_csv_dl", file_name="users.csv",
                           data=users[USER_SAVE_COLS].to_csv(index=False).encode("utf-8"), mime="text/csv")
    if save:
        new, new_pw, errs = apply_user_edits(users, ed, me_id, known_leads)
        if errs:
            for e in errs:
                st.error(e)
        else:
            save_users(new)
            st.session_state["acct_pw"] = new_pw or None
            st.session_state["acct_msg"] = f"Đã lưu {len(new)} tài khoản." + (f" Đã cấp mật khẩu cho {len(new_pw)} tài khoản mới." if new_pw else "")
            if not new_pw:
                st.session_state.pop("acct_pw", None)
            st.rerun()

    section("Đặt lại mật khẩu", "Dùng khi nhân viên quên mật khẩu: tạo mật khẩu mới ngẫu nhiên, mật khẩu cũ mất hiệu lực")
    pick = st.multiselect("Chọn tài khoản", users["email"].tolist(), key="acct_reset_pick")
    if st.button("🔑 Đặt lại mật khẩu cho tài khoản đã chọn", disabled=not pick, key="acct_reset_btn"):
        newdf, out = reset_passwords(users, {p.strip().lower() for p in pick})
        save_users(newdf)
        st.session_state["acct_pw"] = out
        st.session_state["acct_msg"] = f"Đã đặt lại mật khẩu cho {len(out)} tài khoản."
        st.rerun()

    section("Khóa / mở khóa tài khoản", "Khóa: người dùng không đăng nhập được, nếu đang đăng nhập sẽ bị đăng xuất ngay; dữ liệu và mật khẩu được giữ nguyên. Mở khóa để dùng lại.")
    lock_pick = st.multiselect("Chọn tài khoản", users["email"].tolist(), key="acct_lock_pick")
    l1, l2 = st.columns(2)
    for col, label_, val, key_ in [(l1, "🔒 Khóa tài khoản đã chọn", "0", "acct_lock_btn"), (l2, "🔓 Mở khóa tài khoản đã chọn", "1", "acct_unlock_btn")]:
        with col:
            if st.button(label_, disabled=not lock_pick, key=key_):
                keys_ = {p.strip().lower() for p in lock_pick}
                if val == "0" and me_key in keys_:
                    st.error("Không thể tự khóa tài khoản đang đăng nhập.")
                else:
                    u2 = users.reset_index(drop=True).copy()
                    u2.loc[u2["key"].isin(keys_), "active"] = val
                    if val == "0" and not ((u2["role"] == "admin") & (u2["active"] == "1")).any():
                        st.error("Phải còn ít nhất một tài khoản Quản trị đang hoạt động.")
                    else:
                        save_users(u2)
                        st.session_state["acct_msg"] = f"Đã {'khóa' if val == '0' else 'mở khóa'} {len(keys_)} tài khoản."
                        st.rerun()

    cnt = P["Field name"].fillna("").apply(norm).value_counts().to_dict()
    show = users.assign(**{"Số tên Field": users["field_names"].apply(lambda s: len([x for x in str(s).split("|") if x.strip()])),
                           "Số plan (đợt này)": users["field_names"].apply(
                               lambda s: int(sum(cnt.get(norm(x), 0) for x in str(s).split("|")) if str(s).strip() else 0))})
    section("Thống kê tài khoản", "Mật khẩu không hiển thị (chỉ lưu dạng băm)")
    show["Trạng thái"] = show["active"].map(lambda a: "🔒 Đã khóa" if a == "0" else "🟢 Hoạt động")
    show_df(show[["email", "role", "Trạng thái", "display_name", "lead", "Số tên Field", "Số plan (đợt này)"]].rename(columns={
        "email": "Tài khoản", "role": "Vai trò", "display_name": "Tên", "lead": "Lead"}), height=320)
    known = {norm(n) for s in users["field_names"] for n in str(s).split("|") if norm(n)}
    miss = pd.Series({k: v for k, v in cnt.items() if k and k not in known}).sort_values(ascending=False)
    section("Tên người thực hiện chưa có tài khoản", "Các plan này chỉ Lead và Quản trị thấy; thêm tài khoản (hoặc thêm tên vào cột 'Tên người thực hiện') để họ tự xem")
    if miss.empty:
        st.success("Mọi người thực hiện plan đều đã có tài khoản.")
    else:
        show_df(miss.rename_axis("Tên (không dấu)").reset_index(name="Số plan"), height=260)


def qc_group(nv, ht):
    if nv == "Trade":
        return "Trade DTV" if ht == "DTV" else "Trade CPS (CellphoneS)"
    if nv == "Plus":
        return "Audit Plus"
    return "Mystery CAMPUS" if ht == "CAMPUS" else "Mystery CPS"


AGE_BINS = [-1, 1, 3, 7, 10_000]
AGE_LABELS = ["0–1 ngày", "2–3 ngày", "4–7 ngày", "Trên 7 ngày"]
QC_COLORS = {"Đã duyệt": "#12b76a", "Từ chối": "#f04438", "Chưa chấm": "#f79009"}


def tab_qc(P):
    P = need_cols(P.copy(), {"auditor": "", "QM": "NONE", "Chờ QM": False, "th_date": pd.NaT})
    f = P[P["Field done"]].copy()
    if f.empty:
        st.info("Chưa có plan nào Field xong nên chưa có gì để QC.")
        return
    ref = P["Ngày update"].max()
    if pd.isna(ref):
        ref = pd.Timestamp.now().normalize()
    f["th_date"] = pd.to_datetime(f["th_date"], errors="coerce")
    f["Nhóm"] = [qc_group(a, b) for a, b in zip(f["Nghiệp vụ"], f["Hệ thống"])]
    f["QC viên"] = f["auditor"].replace("", "(chưa giao QC viên)")
    f["t1"] = np.select([f["QC"].eq("DONE"), f["Bị từ chối"]], ["Đã duyệt", "Từ chối"], "Chưa chấm")
    f["Tồn (ngày)"] = (ref.normalize() - f["th_date"]).dt.days.clip(lower=0)
    f["Quản lý chờ"] = f["Chờ QM"].astype(bool)
    st.caption(f"Số liệu tính đến {ref:%d/%m/%Y} (ngày cập nhật mới nhất trong file raw). "
               "QC viên = cấp chấm đầu; QC Manager = cấp duyệt thứ hai (chỉ tính plan QC viên đã duyệt xong). "
               "'Tồn' = số ngày từ lúc Field thực hiện đến ngày số liệu.")
    n, d, r = len(f), int((f["t1"] == "Đã duyệt").sum()), int((f["t1"] == "Từ chối").sum())
    w, qw = int((f["t1"] == "Chưa chấm").sum()), int(f["Quản lý chờ"].sum())
    cards = [kpi_card("Plan Field đã xong", n, "cần QC chấm"),
             kpi_card("QC viên đã xử lý", f"{d + r}/{n}", f"duyệt {d} · từ chối {r}", pct(d + r, n)),
             kpi_card("QC viên CHƯA CHẤM", w, "plan chờ QC viên", None, bad=True),
             kpi_card("QC Manager chưa duyệt", qw, "plan QC viên đã duyệt, chờ Manager", None, bad=True),
             kpi_card("Tồn lâu nhất", f"{int(f.loc[f['t1'] == 'Chưa chấm', 'Tồn (ngày)'].max() or 0) if w else 0} ngày",
                      "plan chờ QC viên lâu nhất")]
    st.markdown('<div class="kpi-row">' + "".join(cards) + "</div>", unsafe_allow_html=True)

    def summarize(g):
        gw = g[g["t1"] == "Chưa chấm"]
        done_ = int((g["t1"] == "Đã duyệt").sum())
        rej_ = int((g["t1"] == "Từ chối").sum())
        return pd.Series({
            "Field xong": len(g), "QC viên – đã duyệt": done_, "QC viên – từ chối": rej_, "QC viên – CHƯA CHẤM": len(gw),
            "% QC viên đã xử lý": pct(done_ + rej_, len(g)),
            "QC Manager – đã duyệt": int((g["QC"].eq("DONE") & g["QM"].eq("DONE")).sum()),
            "QC Manager – chưa duyệt": int(g["Quản lý chờ"].sum()),
            "Tồn lâu nhất (ngày)": int(gw["Tồn (ngày)"].max()) if len(gw) and gw["Tồn (ngày)"].notna().any() else 0,
            "Tồn trung bình (ngày)": round(float(gw["Tồn (ngày)"].mean()), 1) if len(gw) and gw["Tồn (ngày)"].notna().any() else 0.0})

    order = ["Trade CPS (CellphoneS)", "Trade DTV", "Audit Plus", "Mystery CPS", "Mystery CAMPUS"]
    by = pd.DataFrame({k: summarize(g) for k, g in f.groupby("Nhóm")}).T.reindex([o for o in order if o in set(f["Nhóm"])])
    for c_ in by.columns:
        by[c_] = pd.to_numeric(by[c_])
    tot = summarize(f).to_frame("TỔNG CỘNG").T
    by_show = pd.concat([by, tot]).rename_axis("Nghiệp vụ").reset_index()
    for c_ in ["Field xong", "QC viên – đã duyệt", "QC viên – từ chối", "QC viên – CHƯA CHẤM", "QC Manager – đã duyệt",
               "QC Manager – chưa duyệt", "Tồn lâu nhất (ngày)"]:
        by_show[c_] = pd.to_numeric(by_show[c_]).astype(int)
    section("QC chưa chấm theo từng nghiệp vụ")
    show_df(by_show, column_config=PCT_CFG(["% QC viên đã xử lý"]))

    a, b = st.columns(2)
    with a:
        ch = by.rename_axis("Nhóm").reset_index()[["Nhóm", "QC viên – đã duyệt", "QC viên – từ chối", "QC viên – CHƯA CHẤM"]].rename(columns={
            "QC viên – đã duyệt": "Đã duyệt", "QC viên – từ chối": "Từ chối", "QC viên – CHƯA CHẤM": "Chưa chấm"})
        bar_chart(ch, "Nhóm", ["Đã duyệt", "Từ chối", "Chưa chấm"], "QC viên: đã duyệt / từ chối / chưa chấm", barmode="stack")
    with b:
        ch2 = by.rename_axis("Nhóm").reset_index()[["Nhóm", "QC viên – CHƯA CHẤM", "QC Manager – chưa duyệt"]].rename(columns={
            "QC viên – CHƯA CHẤM": "Chờ QC viên", "QC Manager – chưa duyệt": "Chờ QC Manager"})
        fig = px.bar(ch2, x="Nhóm", y=["Chờ QC viên", "Chờ QC Manager"], barmode="group", text_auto=True,
                     title="Tồn đọng chờ QC theo cấp", color_discrete_map={"Chờ QC viên": "#f79009", "Chờ QC Manager": "#7a5af8"})
        fig.update_yaxes(title_text="Số plan")
        show_chart(fig)

    wait = f[f["t1"] == "Chưa chấm"].copy()
    if not wait.empty:
        wait["Độ tồn"] = pd.cut(wait["Tồn (ngày)"].fillna(0), bins=AGE_BINS, labels=AGE_LABELS)
        ag = wait.groupby(["Độ tồn", "Nhóm"], observed=False).size().reset_index(name="Số plan")
        fig = px.bar(ag, x="Độ tồn", y="Số plan", color="Nhóm", barmode="stack", text_auto=True,
                     title="Plan chờ QC viên theo độ tồn (ngày kể từ lúc Field thực hiện)")
        show_chart(fig)

    section("Hiệu suất từng QC viên", "Tính theo plan được giao cho từng QC viên (cột 'Tên Auditor' trong raw)")
    proc = f[f["t1"] != "Chưa chấm"]
    def per_qc(name, g):
        gw = g[g["t1"] == "Chưa chấm"]
        return {"QC viên": name, "Được giao (Field xong)": len(g), "Đã duyệt": int((g["t1"] == "Đã duyệt").sum()),
                "Từ chối": int((g["t1"] == "Từ chối").sum()), "Chưa chấm": len(gw),
                "% đã xử lý": pct(len(g) - len(gw), len(g)),
                "Tồn lâu nhất (ngày)": int(gw["Tồn (ngày)"].max()) if len(gw) and gw["Tồn (ngày)"].notna().any() else 0}

    q = pd.DataFrame([per_qc(k, g) for k, g in f.groupby("QC viên")])
    spd = (proc["Ngày update"].dt.normalize() - proc["th_date"]).dt.days.clip(lower=0).groupby(proc["QC viên"]).mean().round(1)
    q["Ngày từ Field đến cập nhật cuối (TB, ước tính)"] = q["QC viên"].map(spd)
    q = q.sort_values("Chưa chấm", ascending=False).reset_index(drop=True)
    show_df(q, column_config=PCT_CFG(["% đã xử lý"]))
    bar_chart(q.melt(id_vars="QC viên", value_vars=["Đã duyệt", "Từ chối", "Chưa chấm"], var_name="Tình trạng", value_name="Số plan"),
              "QC viên", "Số plan", "Khối lượng và tồn đọng từng QC viên", barmode="stack", color="Tình trạng",
              color_discrete_map=QC_COLORS)

    section("Danh sách plan QC viên chưa chấm", "Dùng để đôn đốc, sắp xếp theo độ tồn giảm dần")
    c1, c2 = st.columns(2)
    sel_g = c1.multiselect("Lọc nghiệp vụ", order, key="qc_flt_g")
    sel_q = c2.multiselect("Lọc QC viên", sorted(wait["QC viên"].unique()), key="qc_flt_q")
    lst = wait
    if sel_g:
        lst = lst[lst["Nhóm"].isin(sel_g)]
    if sel_q:
        lst = lst[lst["QC viên"].isin(sel_q)]
    lst = lst.sort_values("Tồn (ngày)", ascending=False)
    out = pd.DataFrame({"Nghiệp vụ": lst["Nhóm"], "Hạng mục": lst["Hạng mục"], "Mã cửa hàng": lst["store"], "Lead": lst["Lead"],
                        "Tên plan": lst["Tên Plan"], "QC viên được giao": lst["QC viên"],
                        "Ngày Field thực hiện": lst["th_date"].dt.strftime("%d/%m/%Y"), "Tồn (ngày)": lst["Tồn (ngày)"],
                        "Trạng thái QC": lst["QC"].map(QC_LABEL)})
    show_df(out, height=420)
    if not out.empty:
        dl_button(out, "QC_chua_cham", "QC_chua_cham.xlsx", "dl_qc_wait")
    mg = f[f["Quản lý chờ"]]
    with st.expander(f"Plan chờ QC Manager duyệt ({len(mg)})"):
        outm = pd.DataFrame({"Nghiệp vụ": mg["Nhóm"], "Hạng mục": mg["Hạng mục"], "Mã cửa hàng": mg["store"], "Lead": mg["Lead"],
                             "Tên plan": mg["Tên Plan"], "QC viên đã duyệt": mg["QC viên"],
                             "Tồn (ngày)": mg["Tồn (ngày)"], "Trạng thái Manager": mg["QM"].map(QC_LABEL)}).sort_values("Tồn (ngày)", ascending=False)
        show_df(outm, height=360)
        if not outm.empty:
            dl_button(outm, "QCManager_chua_duyet", "QC_Manager_chua_duyet.xlsx", "dl_qm_wait")


# =====================================================================
# Main
# =====================================================================
def analyze(P, label, scope=None):
    scope = stores if scope is None else scope
    only_l2 = label == "Lần 2"
    cps_m = store_matrix(P, scope, "CPS", CPS_ITEMS, only_l2)
    dtv_m = store_matrix(P, scope, "DTV", DTV_ITEMS) if not only_l2 else store_matrix(P.iloc[0:0], scope.iloc[0:0], "DTV", DTV_ITEMS)
    my_m = mystery_matrix(P, scope)
    return cps_m, dtv_m, my_m, lead_summary(P, scope, cps_m, dtv_m, my_m)


def render_round(file_bytes, fname, label):
    bundle = compute_all(file_bytes, label, stores, DEFAULT_MAX, CAMPUS_KW, APP_VERSION)
    P = bundle["P"]
    if P.empty:
        st.error(f"File {fname} không có dữ liệu '{label}' trong cột Chấm. "
                 f"Các giá trị Chấm tìm thấy: {bundle['rounds'] or 'không có cột Chấm'}")
        st.stop()
    if IS_ADMIN and not FLAGS_OK:
        st.warning("File store_master.csv trên GitHub là bản cũ (thiếu cột Mystery / L2). "
                   "Hãy upload lại store_master.csv bản mới để số liệu Mystery và Lần 2 đúng.")
    IVc = check_audience(bundle["IV"], staff, ALLOWED_KW)
    scope = stores
    if ROLE == "lead":  # Lead chỉ thấy plan thuộc cửa hàng của mình
        P = P[P["Lead"] == MY_LEAD].reset_index(drop=True)
        scope = stores[stores["Lead"] == MY_LEAD]
        if not IVc.empty and "Lead" in IVc.columns:
            IVc = IVc[IVc["Lead"] == MY_LEAD]
    elif ROLE == "field":  # Field chỉ thấy plan do mình thực hiện (và tiến độ các cửa hàng được giao)
        P_all = P
        P = P[P["Field name"].fillna("").apply(norm).isin(MY_NAMES)].reset_index(drop=True)
        if not IVc.empty and "field_name" in IVc.columns:
            IVc = IVc[IVc["field_name"].fillna("").apply(norm).isin(MY_NAMES)]
        wrong, low = split_notices(IVc)
        bell(wrong, low, f"{fname}|{label}|{ROLE}|{USER['email']}")
        field_home(P, P_all, IVc, label)
        return
    bundle = {**bundle, "P": P, "IV": IVc, "fb": file_bytes}
    wrong, low = split_notices(IVc)
    bell(wrong, low, f"{fname}|{label}|{ROLE}|{MY_LEAD}")
    cps_m, dtv_m, my_m, ls = analyze(P, label, scope)
    camp = campus_matrix(P)
    names = ["📊 Tổng quan", "🏬 CPS – 4 hạng mục", "🏪 DTV", "➕ Plus 1–5", "🕵️ Mystery", "🎓 CAMPUS",
             "🎤 Trả bài Plus", "⚠️ Bị từ chối", "👥 Nhân sự Field", "📨 Yêu cầu bổ sung"]
    if IS_ADMIN:
        names += ["📈 Hiệu suất QC", "🧪 Kiểm tra dữ liệu", "🔐 Tài khoản"]
    tabs = st.tabs(names)
    trade = P[P["Nghiệp vụ"] == "Trade"]
    with tabs[0]:
        safe(tab_overview, P, cps_m, dtv_m, my_m, ls, label, len(wrong), len(low))
    with tabs[1]:
        safe(tab_trade, cps_m, CPS_ITEMS, "CPS", "cps", int((trade["Hệ thống"] == "CPS").sum()), label)
    with tabs[2]:
        if label == "Lần 2":
            st.info("Đợt Lần 2 không áp dụng DTV.")
        else:
            safe(tab_trade, dtv_m, DTV_ITEMS, "DTV", "dtv", int((trade["Hệ thống"] == "DTV").sum()), label)
    with tabs[3]:
        safe(tab_plus, P)
    with tabs[4]:
        safe(tab_mystery, my_m, P, bundle["sheets"])
    with tabs[5]:
        safe(tab_campus, camp, P)
    with tabs[6]:
        safe(tab_interviews, bundle["IV"])
    with tabs[7]:
        _when = st.session_state.get(f"{'l2' if label == 'Lần 2' else 'l1'}_saved")
        safe(tab_reject, P, file_bytes, f"{fname}" + (f", lưu lúc {_when}" if _when else ""))
    with tabs[8]:
        safe(tab_field_staff, P)
    with tabs[9]:
        safe(tab_requests, P)
    if IS_ADMIN:
        with tabs[10]:
            safe(tab_qc, P)
        with tabs[11]:
            safe(tab_validation, P, bundle, label)
        with tabs[12]:
            safe(tab_accounts, P)


def ceo_view():
    frames = []
    for label, pre in [("Lần 1", "l1"), ("Lần 2", "l2")]:
        b = st.session_state.get(f"{pre}_bytes")
        if b is None:
            continue
        P = compute_all(b, label, stores, DEFAULT_MAX, CAMPUS_KW, APP_VERSION)["P"]
        if P.empty:
            continue
        ls = analyze(P, label)[3]
        ls.insert(0, "Đợt", label)
        frames.append(ls)
    if not frames:
        welcome("Lần 1 / Lần 2")
        return
    df = pd.concat(frames, ignore_index=True)
    show_df(df, column_config=PCT_CFG(["% CPS", "% DTV", "% Mystery", "% Plus", "% KPI tổng (CPS+DTV+Mystery)"]))
    fig = px.bar(df, x="Lead", y="% KPI tổng (CPS+DTV+Mystery)", color="Đợt", barmode="group",
                 title="KPI tổng theo Lead và theo đợt (%)")
    fig.update_traces(texttemplate="%{y:.0f}%", textangle=0, textposition="outside")
    show_chart(fig)


if view == "📊 CEO VIEW":
    safe(ceo_view)
else:
    pre, label = ("l1", "Lần 1") if view == "📌 LẦN 1" else ("l2", "Lần 2")
    b = st.session_state.get(f"{pre}_bytes")
    if b is None:
        welcome(label) if IS_ADMIN else st.info(f"Chưa có dữ liệu đợt {label}. Liên hệ quản trị để cập nhật dữ liệu.")
    else:
        render_round(b, st.session_state.get(f"{pre}_name"), label)
