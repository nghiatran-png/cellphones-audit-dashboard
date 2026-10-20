import html
import io
import math
import numbers
import re
import traceback
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CellphoneS Audit Platform", page_icon="📱",
                   layout="wide", initial_sidebar_state="expanded")

APP_VERSION = "4.4.0"
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
STORE_FILE = Path(__file__).parent / "store_master.csv"
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
    except OSError:
        return "missing"


@st.cache_data(show_spinner=False)
def load_default_stores(sig=""):
    if not STORE_FILE.exists():
        return _empty_stores()
    return parse_store_master(STORE_FILE.read_bytes(), STORE_FILE.name)


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
             "Ngày update", "Status Plan", "QC Status", "Ngày thực hiện", "Hạng mục", "QC note"]
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


@st.cache_data(show_spinner="Đang đọc file Excel...", max_entries=3)
def load_report(file_bytes, ver=""):
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    out = {}
    for s in xls.sheet_names:
        key = canon_sheet(s)
        if key is None or key in out:
            continue
        want = {norm(c): c for c in USECOLS[key]}
        df = pd.read_excel(xls, sheet_name=s, usecols=lambda c, w=want: norm(c) in w)
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


def plan_level(df):
    """1 dòng / plan (dòng mới nhất) + gộp các QC note của plan."""
    if df is None or df.empty or "Tên Plan" not in df.columns:
        return pd.DataFrame()
    x = df[df["Tên Plan"].notna()].copy()
    x["Tên Plan"] = x["Tên Plan"].astype(str).str.strip()
    x = x[x["Tên Plan"].ne("")]
    notes = pd.Series(dtype=str)
    if "QC note" in x.columns:
        nn = x[x["QC note"].notna() & x["QC note"].astype(str).str.strip().ne("")]
        if not nn.empty:
            notes = nn.groupby("Tên Plan")["QC note"].agg(join_notes)
    if "Ngày update" in x.columns:
        x["_dt"] = pd.to_datetime(x["Ngày update"], errors="coerce", dayfirst=True)
        x = x.sort_values("_dt", na_position="first", kind="stable").drop(columns="_dt")
    x = x.drop_duplicates("Tên Plan", keep="last").reset_index(drop=True)
    x["Ghi chú QC"] = x["Tên Plan"].map(notes).fillna("")
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
        m = re.search(r"plus\s*(\d)", text)
        return f"Plus {m.group(1)}" if m else "Plus ?"
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
          "lead_raw", "status_raw"]


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
    P["Field done"] = P["status_raw"].apply(norm).isin(DONE_FIELD)
    P["QC done"] = P["QC"].eq("DONE")
    P["Hoàn thành"] = P["Field done"] & P["QC done"]
    P["Bị từ chối"] = P["QC"].isin(["REJECT", "REWORK"])
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
        "field_done": tt1["Status Plan"].apply(norm).isin(DONE_FIELD) if "Status Plan" in tt1.columns else False,
    })
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
    t = P[P["Nghiệp vụ"] == "Mystery"]
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


def to_excel(df, sheet):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as w:
        d = df[[c for c in df.columns if not c.startswith("_")]]
        d.to_excel(w, index=False, sheet_name=sheet[:31])
        wb, ws = w.book, w.sheets[sheet[:31]]
        hf = wb.add_format({"bold": True, "font_color": "white", "bg_color": "#D70018", "border": 1,
                            "align": "center", "valign": "vcenter"})
        ok = wb.add_format({"bg_color": "#D1E7DD", "font_color": "#0F5132", "bold": True})
        bad = wb.add_format({"bg_color": "#F8D7DA", "font_color": "#842029", "bold": True})
        for i, n in enumerate(d.columns):
            ws.write(0, i, n, hf)
            body = int(d[n].astype(str).str.len().fillna(0).quantile(.90)) + 2 if len(d) else 12
            ws.set_column(i, i, min(max(len(str(n)) + 2, body), 60))
        last = max(len(d), 1)
        for cand in ["Kết luận", "Đánh giá", "Kết quả L2"]:
            if cand in d.columns:
                c = d.columns.get_loc(cand)
                ws.conditional_format(1, c, last, c, {"type": "cell", "criteria": "==", "value": '"ĐẠT"', "format": ok})
                ws.conditional_format(1, c, last, c, {"type": "text", "criteria": "begins with", "value": "CHƯA ĐẠT", "format": bad})
        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, len(d), len(d.columns) - 1)
    return out.getvalue()


def dl_button(df, sheet, fname, key):
    st.download_button(f"📥 Xuất Excel – {sheet}", data=to_excel(df, sheet), file_name=fname, key=key,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# =====================================================================
# Danh sách nhân sự -> kiểm tra đối tượng phỏng vấn Plus
# =====================================================================
STAFF_FILE = Path(__file__).parent / "nhan_su.csv"
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
    except OSError:
        return "missing"


@st.cache_data(show_spinner=False)
def load_default_staff(sig=""):
    if not STAFF_FILE.exists():
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


def _alerts_body(alerts):
    st.error(f"Có {len(alerts)} bài Plus phỏng vấn SAI ĐỐI TƯỢNG. Chỉ nhận bài của nhân viên bán hàng, "
             "trưởng/quản lý cửa hàng, trợ lý cửa hàng và các vị trí AIO.")
    t = alert_table(alerts)
    show_df(t, height=380)
    dl_button(t, "Sai_doi_tuong", "Bai_Plus_sai_doi_tuong.xlsx", "dl_alert_dialog")


show_alerts = _dialog("🚨 Cảnh báo: bài Plus phỏng vấn sai đối tượng", width="large")(_alerts_body) if _dialog else None


def bell(alerts, tag):
    """Chuông cảnh báo góc trên bên phải: đỏ nhấp nháy khi có bài sai đối tượng; tự bật popup 1 lần khi có cảnh báo mới."""
    n = len(alerts)
    clicked = st.button(f"🔔 {n} bài sai đối tượng" if n else "🔔 Không có cảnh báo",
                        key="bell_alert" if n else "bell_ok", help="Bài Plus phỏng vấn sai đối tượng")
    sig = f"{tag}|{n}"
    auto = n > 0 and st.session_state.get("bell_seen") != sig
    if auto:
        st.session_state["bell_seen"] = sig
    if n and (clicked or auto):
        if show_alerts:
            show_alerts(alerts)
        else:
            _alerts_body(alerts)


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

default_stores = load_default_stores(store_signature())

with st.sidebar:
    st.markdown('<div class="brand"><div class="logo">C</div><div><div class="bn">CellphoneS Audit</div>'
                '<div class="bs">Màn hình điều hành</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="sbt">Chế độ xem</div>', unsafe_allow_html=True)
    view = st.radio("Chế độ", ["📌 LẦN 1", "📌 LẦN 2", "📊 CEO VIEW"], index=0, label_visibility="collapsed")
    st.markdown('<div class="sbt">Dữ liệu</div>', unsafe_allow_html=True)
    for lbl, pre in [("Raw Data Lần 1", "l1"), ("Raw Data Lần 2", "l2")]:
        up = st.file_uploader(lbl, type=["xlsx", "xls"], key=f"up_{pre}")
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
    selected_leader = st.selectbox("Lead", ["Tất cả"] + leaders)
    search = st.text_input("Tìm cửa hàng / NV / MSNV", "")
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
    st.markdown(chip(f"DS cửa hàng: {len(stores)} shop" if len(stores) else "⚠️ Thiếu store_master.csv",
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


def tab_overview(P, cps_m, dtv_m, my_m, ls, label, n_alert=0):
    if n_alert:
        st.error(f"🚨 Có {n_alert} bài Plus phỏng vấn SAI ĐỐI TƯỢNG. Bấm chuông 🔔 ở góc trên bên phải "
                 "hoặc mở tab 'Trả bài Plus' để xem chi tiết.")
    plus = P[P["Nghiệp vụ"] == "Plus"]
    my_t = my_m[~my_m["Ngoài DS giao"]]
    cd, ct = int(cps_m["_done"].sum()), len(cps_m)
    dd, dt = int(dtv_m["_done"].sum()), len(dtv_m)
    md, mt = int(my_t["_done"].sum()), len(my_t)
    pdn, pt = int(plus["Hoàn thành"].sum()), len(plus)
    cards = [
        kpi_card("CPS – đủ 4 hạng mục", f"{cd}/{ct}", "cửa hàng đã hoàn thành", pct(cd, ct)),
        kpi_card("DTV – đủ hạng mục", f"{dd}/{dt}", "cửa hàng đã hoàn thành", pct(dd, dt)) if label == "Lần 1"
        else kpi_card("DTV", "—", "Lần 2 không áp dụng"),
        kpi_card("Plus – plan hoàn thành", f"{pdn}/{pt}", "Field và QC đều đã xong", pct(pdn, pt)),
        kpi_card("Mystery – cửa hàng hoàn tất", f"{md}/{mt}", "trên tổng số cửa hàng được giao", pct(md, mt)),
        kpi_card("Plan bị từ chối", int(P["Bị từ chối"].sum()), "cần chấm lại / bổ sung", None, bad=True),
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


def tab_reject(P):
    r = text_filter(lead_filter(P[P["Bị từ chối"]]), ["store", "Tên Plan", "Lead"], search)
    if r.empty:
        st.success("Không có plan nào bị từ chối hoặc yêu cầu bổ sung.")
        return
    a, b = st.columns(2)
    with a:
        bar_chart(r.groupby("Nghiệp vụ").size().reset_index(name="Số plan"), "Nghiệp vụ", "Số plan",
                  "Plan bị từ chối theo nghiệp vụ")
    with b:
        bar_chart(r.groupby("Lead").size().reset_index(name="Số plan"), "Lead", "Số plan", "Plan bị từ chối theo Lead")
    out = pd.DataFrame({"Nghiệp vụ": r["Nghiệp vụ"], "Lead": r["Lead"], "Mã cửa hàng": r["store"],
                        "Hạng mục": r["Hạng mục"], "Tên plan": r["Tên Plan"],
                        "Trạng thái QC": r["QC"].map(QC_LABEL).fillna("Khác"),
                        "Lý do": r["Ghi chú QC"].replace("", "Chưa có ghi chú QC")}).sort_values(["Nghiệp vụ", "Lead"])
    section("Danh sách plan bị từ chối / yêu cầu bổ sung")
    show_df(out, height=520, column_config={"Lý do": st.column_config.TextColumn(width="large")})
    dl_button(out, "Plan_bi_tu_choi", "Plan_bi_tu_choi.xlsx", "dl_rej")


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
              ("Cửa hàng có trong raw nhưng không có trong danh sách", len(set(P["store"]) - set(stores["Mã cửa hàng"])))]
    section("Kiểm tra nguồn dữ liệu")
    show_df(pd.DataFrame(checks, columns=["Nội dung kiểm tra", "Kết quả"]).astype(str))
    section("Số plan theo nghiệp vụ, hệ thống và hạng mục", "Dùng để phát hiện hạng mục bị nhận diện sai")
    show_df(P.groupby(["Nghiệp vụ", "Hệ thống", "Hạng mục"]).size().reset_index(name="Số plan"))
    if not stores.empty:
        diff = P[(P["lead_raw"] != "") & (P["Lead"] != P["lead_raw"]) & P["store"].isin(stores["Mã cửa hàng"])]
        if not diff.empty:
            section("Cửa hàng có Lead trong raw khác danh sách", "App đang dùng Lead theo danh sách cửa hàng")
            show_df(diff.drop_duplicates("store")[["store", "lead_raw", "Lead"]]
                    .rename(columns={"store": "Mã cửa hàng", "lead_raw": "Lead trong raw", "Lead": "Lead theo danh sách"}))
    miss = sorted(set(P["store"]) - set(stores["Mã cửa hàng"]))
    if miss:
        st.warning("Mã cửa hàng có trong raw nhưng chưa có trong danh sách: " + ", ".join(miss))


# =====================================================================
# Main
# =====================================================================
def analyze(P, label):
    only_l2 = label == "Lần 2"
    cps_m = store_matrix(P, stores, "CPS", CPS_ITEMS, only_l2)
    dtv_m = store_matrix(P, stores, "DTV", DTV_ITEMS) if not only_l2 else store_matrix(P.iloc[0:0], stores.iloc[0:0], "DTV", DTV_ITEMS)
    my_m = mystery_matrix(P, stores)
    return cps_m, dtv_m, my_m, lead_summary(P, stores, cps_m, dtv_m, my_m)


def render_round(file_bytes, fname, label):
    bundle = compute_all(file_bytes, label, stores, DEFAULT_MAX, CAMPUS_KW, APP_VERSION)
    P = bundle["P"]
    if P.empty:
        st.error(f"File {fname} không có dữ liệu '{label}' trong cột Chấm. "
                 f"Các giá trị Chấm tìm thấy: {bundle['rounds'] or 'không có cột Chấm'}")
        st.stop()
    if not FLAGS_OK:
        st.warning("File store_master.csv trên GitHub là bản cũ (thiếu cột Mystery / L2). "
                   "Hãy upload lại store_master.csv bản mới để số liệu Mystery và Lần 2 đúng.")
    IVc = check_audience(bundle["IV"], staff, ALLOWED_KW)
    bundle = {**bundle, "IV": IVc}
    alerts = IVc[IVc["Sai đối tượng"]] if (not IVc.empty and "Sai đối tượng" in IVc.columns) else IVc.iloc[0:0]
    bell(alerts, f"{fname}|{label}")
    cps_m, dtv_m, my_m, ls = analyze(P, label)
    camp = campus_matrix(P)
    tabs = st.tabs(["📊 Tổng quan", "🏬 CPS – 4 hạng mục", "🏪 DTV", "➕ Plus 1–5", "🕵️ Mystery",
                    "🎓 CAMPUS", "🎤 Trả bài Plus", "⚠️ Bị từ chối", "🧪 Kiểm tra dữ liệu"])
    trade = P[P["Nghiệp vụ"] == "Trade"]
    with tabs[0]:
        safe(tab_overview, P, cps_m, dtv_m, my_m, ls, label, len(alerts))
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
        safe(tab_reject, P)
    with tabs[8]:
        safe(tab_validation, P, bundle, label)


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
        welcome(label)
    else:
        render_round(b, st.session_state.get(f"{pre}_name"), label)
