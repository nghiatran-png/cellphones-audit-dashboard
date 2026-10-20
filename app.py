import io
import math
import numbers
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CellphoneS Audit Platform", page_icon="📱",
                   layout="wide", initial_sidebar_state="expanded")

try:
    from master_data import TARGET_35_NV_MASTER, TARGET_94_ESIM_L1
except ImportError:
    st.error("Thiếu file master_data.py (2 danh sách TARGET_35_NV_MASTER và TARGET_94_ESIM_L1).")
    st.stop()

APP_VERSION = "4.0.0"
CPS_ITEMS = ["Demo", "Tủ máy", "Vách/Đảo", "CellphoneS"]
DTV_ITEMS = ["Trade Audit DTV"]
PLUS_ITEMS = [f"Plus {i}" for i in range(1, 6)]

_ver = tuple(int(p) for p in st.__version__.split(".")[:2] if p.isdigit())
STRETCH = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}

STATUS_LABEL = {"DONE": "✅ Hoàn thành", "REJECT": "❌ Bị từ chối", "WAIT_QC": "🕓 Chờ QC",
                "NOT_FIELD": "⏳ Chưa Field", "NONE": "— Chưa có plan"}
STATUS_COLOR = {"✅ Hoàn thành": "#12b76a", "🕓 Chờ QC": "#f79009", "❌ Bị từ chối": "#f04438",
                "⏳ Chưa Field": "#98a2b3", "— Chưa có plan": "#d0d5dd"}
REASON = {"WAIT_QC": "đã Field, chờ QC duyệt", "NOT_FIELD": "Field chưa hoàn thành", "NONE": "chưa có plan"}

st.markdown("""
<style>
:root{--brand:#d70018;--brand2:#8f0010;--line:#e4e7ec;--ink:#101828}
.stApp{background:#f6f7f9}
.block-container{max-width:1680px;padding-top:1rem;padding-bottom:3rem}
.hero{display:flex;justify-content:space-between;align-items:center;padding:20px 24px;border-radius:16px;color:white;
background:linear-gradient(135deg,var(--brand),var(--brand2));box-shadow:0 12px 28px rgba(215,0,24,.16);margin-bottom:16px}
.hero-title{font-size:28px;font-weight:900}.hero-sub{font-size:13px;opacity:.86}
.hero-pill{padding:9px 13px;border-radius:999px;background:rgba(255,255,255,.14);font-weight:800}
div[data-testid="stMetric"]{background:white;border:1px solid var(--line);border-radius:14px;padding:14px}
div[data-testid="stMetricValue"]{font-weight:900;color:var(--ink)}
.stTabs [data-baseweb="tab-list"]{background:white;border:1px solid var(--line);padding:6px;border-radius:12px;gap:4px;flex-wrap:wrap}
.stTabs [aria-selected="true"]{background:var(--brand)!important;color:white!important;border-radius:8px;font-weight:800}
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
    return "ĐẠT" if r >= thr else f"DƯỚI {thr}% – TRẢ BÀI ĐỢT 2"


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


def show_df(df, height=None, **kw):
    args = {"hide_index": True, **STRETCH, **kw}
    if height:
        args["height"] = height
    st.dataframe(df, **args)


def show_chart(fig):
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), legend_title_text="")
    st.plotly_chart(fig, **STRETCH)


def bar_chart(df, x, ys, title, barmode="group", **kw):
    fig = px.bar(df, x=x, y=ys, barmode=barmode, title=title, text_auto=True, **kw)
    show_chart(fig)


def pie_chart(names, values, title, colors=None):
    fig = px.pie(names=names, values=values, title=title, hole=0.45,
                 color=names, color_discrete_map=colors or {})
    fig.update_traces(textinfo="value+percent")
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


@st.cache_data(show_spinner=False)
def load_default_stores():
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
def load_report(file_bytes):
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
def system_of(code, ht):
    h = norm(ht).upper()
    if "CAMPUS" in code or "CAMPUS" in h:
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


def build_plans(sheets, label, stores):
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
        out["Hệ thống"] = [system_of(c, h) for c, h in zip(out["store"], g("Hệ thống"))]
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
    })
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
def compute_all(file_bytes, label, stores, default_max):
    sheets = load_report(file_bytes)
    return {"P": build_plans(sheets, label, stores),
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
    if only_l2 and not s.empty:
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
    tgt = stores[stores["Mystery"] == "Có"] if not stores.empty else stores
    extra = sorted(set(t["store"]) - set(tgt["Mã cửa hàng"] if not tgt.empty else []))
    info = stores.set_index("Mã cửa hàng") if not stores.empty else None
    m = _group_matrix(t, (list(tgt["Mã cửa hàng"]) if not tgt.empty else []) + extra, info)
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
                      my_m[my_m["Lead"] == ld], plus[plus["Lead"] == ld])
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
        for cand in ["Đánh giá", "Kết quả L2"]:
            if cand in d.columns:
                c = d.columns.get_loc(cand)
                ws.conditional_format(1, c, last, c, {"type": "cell", "criteria": "==", "value": '"ĐẠT"', "format": ok})
                ws.conditional_format(1, c, last, c, {"type": "text", "criteria": "begins with", "value": "DƯỚI", "format": bad})
        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, len(d), len(d.columns) - 1)
    return out.getvalue()


def dl_button(df, sheet, fname, key):
    st.download_button(f"📥 Xuất Excel – {sheet}", data=to_excel(df, sheet), file_name=fname, key=key,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# =====================================================================
# 35 NV / 94 eSIM matching (điểm = % so với điểm tối đa)
# =====================================================================
def _prep(iv):
    x = iv.copy()
    if not x.empty:
        x["_name"] = x["employee_name"].apply(norm)
        x["_store"] = x["store_code"].apply(norm_code)
        x["_id"] = x["employee_id"].apply(digits)
    return x


def _by_name_store(x, name, store, loose):
    if x.empty:
        return x
    n = norm(name)
    nm = x[x["_name"] == n]
    if nm.empty and len(n) >= 6:
        nm = x[x["_name"].str.startswith(n)]
    if nm.empty:
        return nm
    by = nm[nm["_store"] == norm_code(store)]
    return by if (not by.empty or not loose) else nm


def _latest(c):
    return c.sort_values("updated_at", na_position="first", kind="stable").iloc[-1]


def _score_cols(r, thr):
    return {"Điểm": r["score"], "Điểm tối đa": r["max_score"], "% điểm": r["pct"],
            "Đánh giá": eval_pct(r["pct"], thr)}


NO_SCORE = {"Điểm": np.nan, "Điểm tối đa": np.nan, "% điểm": np.nan}


def match35(iv, thr, loose, stores):
    x, rows = _prep(iv), []
    lead_map = stores.set_index("Mã cửa hàng")["Lead"].to_dict() if not stores.empty else {}
    for m in TARGET_35_NV_MASTER:
        cand = _by_name_store(x, m["Tên"], m["Mã cửa hàng"], loose)
        lead = lead_map.get(norm_code(m["Mã cửa hàng"]), m["Leader"])
        base = {"Nhân sự": m["Tên"], "Mã cửa hàng": m["Mã cửa hàng"], "Leader": lead,
                "Lead cũ (list)": m["Leader"] if canon_leader(m["Leader"]) != lead else ""}
        if cand.empty:
            rows.append({**base, **NO_SCORE, "Đánh giá": "CHƯA TRẢ BÀI", "QC Status": "NONE", "Field": ""})
        else:
            r = _latest(cand)
            rows.append({**base, **_score_cols(r, thr), "QC Status": r["qc_status"], "Field": r["field_name"]})
    return pd.DataFrame(rows)


def match94(iv, label, thr, loose, stores):
    x, rows = _prep(iv), []
    lead_map = stores.set_index("Mã cửa hàng")["Lead"].to_dict() if not stores.empty else {}
    missing = "BẮT BUỘC TRẢ LẦN 2" if label == "Lần 2" else "CHƯA TRẢ BÀI"
    for m in TARGET_94_ESIM_L1:
        cand = pd.DataFrame()
        if not x.empty:
            tid = digits(m["MSNV"])
            cand = x[x["_id"] == tid] if tid else pd.DataFrame()
            if cand.empty:
                cand = _by_name_store(x, m["Tên"], m["Shop"], loose)
        lead = lead_map.get(norm_code(m["Shop"]), m["Leader"])
        base = {"STT": m["STT"], "MSNV": m["MSNV"], "Họ và Tên": m["Tên"], "Shop": m["Shop"], "Miền": m["Miền"],
                "Leader": lead}
        if cand.empty:
            rows.append({**base, "Field": "", **NO_SCORE, "Kết quả L2": missing})
        else:
            r = _latest(cand)
            sc = _score_cols(r, thr)
            rows.append({**base, "Field": r["field_name"], "Điểm": sc["Điểm"], "Điểm tối đa": sc["Điểm tối đa"],
                         "% điểm": sc["% điểm"], "Kết quả L2": sc["Đánh giá"]})
    return pd.DataFrame(rows)


# =====================================================================
# Sidebar
# =====================================================================
for _k in ["l1_bytes", "l1_name", "l2_bytes", "l2_name"]:
    st.session_state.setdefault(_k, None)

default_stores = load_default_stores()

with st.sidebar:
    st.markdown("### 🖥️ MÀN HÌNH ĐIỀU HÀNH")
    view = st.radio("Chế độ", ["📌 LẦN 1", "📌 LẦN 2", "📊 CEO VIEW"], index=0)
    st.divider()
    for lbl, pre in [("Raw Data Lần 1", "l1"), ("Raw Data Lần 2", "l2")]:
        up = st.file_uploader(lbl, type=["xlsx", "xls"], key=f"up_{pre}")
        if up:
            st.session_state[f"{pre}_bytes"], st.session_state[f"{pre}_name"] = up.getvalue(), up.name
            st.success(f"Đã nạp {pre.upper()}")
    st.divider()
    stores_all = default_stores
    leaders = sorted(set(stores_all["Lead"]) - {""}) if not stores_all.empty else []
    selected_leader = st.selectbox("Lead", ["Tất cả"] + leaders)
    selected_region = st.selectbox("Miền (bảng 94 eSIM)", ["Tất cả", "Miền Bắc", "Miền Nam"])
    search = st.text_input("Tìm cửa hàng / NV / MSNV", "")
    with st.expander("⚙️ Thiết lập"):
        THR = st.slider("Ngưỡng điểm trả bài (%)", 50, 100, 80, 5)
        DEFAULT_MAX = st.number_input("Điểm tối đa (khi raw thiếu 'Thang điểm')", 1, 1000, 100)
        loose = st.checkbox("Khớp NV theo tên khi lệch mã shop", value=False)
        u3 = st.file_uploader("DS cửa hàng thay thế (CSV/Excel)", type=["csv", "xlsx", "xls"], key="up_store")
    stores = default_stores
    if u3:
        parsed = parse_store_master(u3.getvalue(), u3.name)
        if parsed.empty:
            st.warning("Không đọc được DS cửa hàng vừa nạp, dùng bảng mặc định.")
        else:
            stores = merge_flags(parsed, default_stores)
    st.caption(f"DS cửa hàng: {len(stores)} shop" + ("" if len(stores) else " ⚠️ thiếu store_master.csv"))

st.markdown(f"""
<div class="hero"><div><div class="hero-title">📱 CELLPHONES ENTERPRISE AUDIT — {view}</div>
<div class="hero-sub">Trade (CPS/DTV) • Plus • Mystery • CAMPUS • Trả bài • QC</div></div>
<div class="hero-pill">v{APP_VERSION}</div></div>
""", unsafe_allow_html=True)


def lead_filter(df):
    if selected_leader != "Tất cả" and df is not None and not df.empty and "Lead" in df.columns:
        return df[df["Lead"] == selected_leader]
    return df


# =====================================================================
# Tab renderers
# =====================================================================
def tab_overview(P, cps_m, dtv_m, my_m, ls, label):
    c = st.columns(5)
    c[0].metric("CPS hoàn thành đủ HM", f"{int(cps_m['_done'].sum())} / {len(cps_m)}")
    c[1].metric("DTV hoàn thành", f"{int(dtv_m['_done'].sum())} / {len(dtv_m)}" if label == "Lần 1" else "Không áp dụng L2")
    plus = P[P["Nghiệp vụ"] == "Plus"]
    c[2].metric("Plus hoàn thành", f"{int(plus['Hoàn thành'].sum())} / {len(plus)}")
    c[3].metric("Mystery hoàn tất", f"{int(my_m['_done'].sum())} / {int(my_m['Ngoài DS giao'].eq(False).sum())}")
    c[4].metric("Plan bị từ chối", int(P["Bị từ chối"].sum()))

    st.subheader("Tiến độ từng Lead so với KPI (= số cửa hàng đang quản lý)")
    pcols = ["% CPS", "% DTV", "% Mystery", "% Plus", "% KPI tổng (CPS+DTV+Mystery)"]
    show_df(ls, column_config=PCT_CFG(pcols))

    if ls.empty:
        return
    a, b = st.columns(2)
    with a:
        long = ls.melt(id_vars="Lead", value_vars=["CPS (cửa hàng)", "CPS hoàn thành", "DTV (cửa hàng)", "DTV hoàn thành",
                                                  "Mystery (giao)", "Mystery hoàn tất"],
                       var_name="Chỉ tiêu", value_name="Số lượng")
        bar_chart(long, "Lead", "Số lượng", "Cửa hàng quản lý vs đã hoàn thành", color="Chỉ tiêu")
    with b:
        long = ls.melt(id_vars="Lead", value_vars=pcols, var_name="Hạng mục", value_name="%")
        fig = px.bar(long, x="Lead", y="%", color="Hạng mục", barmode="group", title="% hoàn thành theo Lead")
        fig.update_traces(texttemplate="%{y:.0f}%")
        show_chart(fig)
    a, b = st.columns(2)
    with a:
        cnt = P["_st"].map(STATUS_LABEL).value_counts()
        pie_chart(cnt.index.tolist(), cnt.values.tolist(), "Trạng thái toàn bộ plan", STATUS_COLOR)
    with b:
        done, tot = int(cps_m["_done"].sum()), len(cps_m)
        pie_chart(["CPS đủ 4 hạng mục", "CPS chưa đủ"], [done, tot - done], "Cửa hàng CPS",
                  {"CPS đủ 4 hạng mục": "#12b76a", "CPS chưa đủ": "#f04438"})


def tab_trade(M, items, system, key):
    M = text_filter(lead_filter(M), ["Mã cửa hàng", "Địa chỉ cửa hàng", "Lead"], search)
    if M.empty:
        st.info(f"Không có cửa hàng {system} nào theo bộ lọc hiện tại.")
        return
    done, tot = int(M["_done"].sum()), len(M)
    c = st.columns(3)
    c[0].metric(f"Cửa hàng {system}", tot)
    c[1].metric("Đã đủ hạng mục", f"{done}  ({pct(done, tot):.0f}%)")
    c[2].metric("Chưa đủ", tot - done)

    a, b = st.columns(2)
    with a:
        g = M.groupby("Lead").agg(**{"Đã đủ": ("_done", "sum"), "Tổng": ("_done", "size")}).reset_index()
        g["Chưa đủ"] = g["Tổng"] - g["Đã đủ"]
        bar_chart(g, "Lead", ["Đã đủ", "Chưa đủ"], f"Cửa hàng {system} theo Lead", barmode="stack",
                  color_discrete_map={"Đã đủ": "#12b76a", "Chưa đủ": "#f04438"})
    with b:
        long = pd.concat([M[it].value_counts().rename_axis("Trạng thái").reset_index(name="Số lượng")
                          .assign(**{"Hạng mục": it}) for it in items])
        bar_chart(long, "Hạng mục", "Số lượng", "Trạng thái theo hạng mục", barmode="stack",
                  color="Trạng thái", color_discrete_map=STATUS_COLOR)
    pie_chart(["Đã đủ", "Chưa đủ"], [done, tot - done], f"{system}: đủ / chưa đủ",
              {"Đã đủ": "#12b76a", "Chưa đủ": "#f04438"})

    st.markdown(f"#### Cửa hàng {system} chưa đủ hạng mục – thiếu gì, vì sao")
    inc = M[~M["_done"]].sort_values(["Lead", "Mã cửa hàng"])
    cols = ["Lead", "Mã cửa hàng", "Địa chỉ cửa hàng"] + items + ["Số HM đạt", "Thiếu hạng mục", "Ghi chú"]
    if inc.empty:
        st.success("Tất cả cửa hàng đã hoàn thành đủ hạng mục.")
    else:
        show_df(inc[cols], height=520, column_config={"Ghi chú": st.column_config.TextColumn("Ghi chú", width="large")})
        dl_button(inc[cols], f"{system}_chua_du", f"{system}_chua_du.xlsx", f"dl_{key}")
    with st.expander("Xem toàn bộ cửa hàng"):
        show_df(M[cols], height=500)


def tab_plus(P):
    t = lead_filter(P[P["Nghiệp vụ"] == "Plus"])
    t = text_filter(t, ["store", "Tên Plan", "Lead"], search)
    if t.empty:
        st.info("Chưa có plan Plus theo bộ lọc hiện tại.")
        return
    rows = []
    for it in PLUS_ITEMS + sorted(set(t["Hạng mục"]) - set(PLUS_ITEMS)):
        g = t[t["Hạng mục"] == it]
        if g.empty and it not in PLUS_ITEMS:
            continue
        rows.append({"Hạng mục": it, "Tổng plan": len(g), "Field chấm xong": int(g["Field done"].sum()),
                     "QC chấm xong": int(g["QC done"].sum()), "Hoàn thành (Field+QC)": int(g["Hoàn thành"].sum()),
                     "Chờ QC": int((g["_st"] == "WAIT_QC").sum()), "Bị từ chối": int(g["Bị từ chối"].sum())})
    s = pd.DataFrame(rows)
    c = st.columns(4)
    c[0].metric("Tổng plan Plus", len(t))
    c[1].metric("Field chấm xong", int(t["Field done"].sum()))
    c[2].metric("QC chấm xong", int(t["QC done"].sum()))
    c[3].metric("Bị từ chối", int(t["Bị từ chối"].sum()))
    show_df(s)
    a, b = st.columns(2)
    with a:
        bar_chart(s, "Hạng mục", ["Field chấm xong", "QC chấm xong", "Hoàn thành (Field+QC)", "Bị từ chối"],
                  "Plus 1 → 5: tiến độ")
    with b:
        cnt = t["_st"].map(STATUS_LABEL).value_counts()
        pie_chart(cnt.index.tolist(), cnt.values.tolist(), "Trạng thái plan Plus", STATUS_COLOR)
    g = t.groupby("Lead").agg(**{"Tổng plan": ("Tên Plan", "size"), "Hoàn thành": ("Hoàn thành", "sum"),
                                 "Bị từ chối": ("Bị từ chối", "sum")}).reset_index()
    bar_chart(g, "Lead", ["Tổng plan", "Hoàn thành", "Bị từ chối"], "Plus theo Lead")
    st.markdown("#### Plan Plus bị từ chối – lý do")
    rej = t[t["Bị từ chối"]][["Lead", "store", "Hạng mục", "Tên Plan", "Ghi chú QC"]] \
        .rename(columns={"store": "Mã cửa hàng", "Ghi chú QC": "Lý do từ chối"})
    if rej.empty:
        st.success("Không có plan Plus bị từ chối.")
    else:
        show_df(rej, height=400, column_config={"Lý do từ chối": st.column_config.TextColumn(width="large")})


def tab_mystery(M, P):
    M = text_filter(lead_filter(M), ["Mã cửa hàng", "Địa chỉ cửa hàng", "Lead"], search)
    tgt = M[~M["Ngoài DS giao"]]
    if tgt.empty:
        st.info("Chưa có dữ liệu Mystery.")
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
        pie_chart(stt.index.tolist(), stt.values.tolist(), "Trạng thái cửa hàng Mystery",
                  {"✅ Hoàn tất": "#12b76a", "🕓 Đang thực hiện": "#f79009",
                   "❌ Có plan bị từ chối": "#f04438", "— Chưa có plan": "#d0d5dd"})
    st.markdown("#### Cửa hàng Mystery chưa hoàn tất – lý do")
    cols = ["Lead", "Mã cửa hàng", "Địa chỉ cửa hàng", "Số plan", "Plan hoàn thành", "Plan bị từ chối", "Trạng thái", "Ghi chú"]
    inc = tgt[~tgt["_done"]].sort_values(["Lead", "Mã cửa hàng"])
    show_df(inc[cols], height=480, column_config={"Ghi chú": st.column_config.TextColumn(width="large")})
    if not inc.empty:
        dl_button(inc[cols], "Mystery_chua_xong", "Mystery_chua_xong.xlsx", "dl_my")
    extra = M[M["Ngoài DS giao"]]
    if not extra.empty:
        st.warning(f"{len(extra)} cửa hàng có plan Mystery nhưng không nằm trong DS giao.")
    mp = lead_filter(P[P["Nghiệp vụ"] == "Mystery"])
    if not mp.empty:
        st.markdown("#### Kịch bản theo Lead")
        g = mp.groupby(["Lead", "Hạng mục"]).agg(**{"Tổng plan": ("Tên Plan", "size"),
                                                   "Hoàn thành": ("Hoàn thành", "sum")}).reset_index()
        show_df(g)
        bar_chart(g, "Lead", "Tổng plan", "Cơ cấu kịch bản Mystery", barmode="stack", color="Hạng mục")


def tab_campus(C):
    C = lead_filter(C)
    if C.empty:
        st.info("Chưa thấy plan nào thuộc mã CAMPUS trong raw data (nhận diện theo 'CAMPUS' trong Mã cửa hàng hoặc Hệ thống).")
        return
    done = int(C["_done"].sum())
    c = st.columns(3)
    c[0].metric("Cơ sở CAMPUS", len(C))
    c[1].metric("Hoàn thành hết", done)
    c[2].metric("Còn bị từ chối / chưa xong", len(C) - done)
    cols = ["Lead", "Mã cửa hàng", "Số plan", "Plan hoàn thành", "Plan bị từ chối", "Trạng thái", "Ghi chú"]
    show_df(C[cols], height=420, column_config={"Ghi chú": st.column_config.TextColumn(width="large")})
    cnt = C["Trạng thái"].value_counts()
    pie_chart(cnt.index.tolist(), cnt.values.tolist(), "Trạng thái CAMPUS")


def tab_interviews(IV, label):
    if IV.empty:
        st.info("Chưa có dữ liệu trả bài (cần sheet Trade Audit Plus có dòng TT1).")
        return
    d = IV.copy()
    d["Đánh giá"] = d["pct"].apply(lambda v: eval_pct(v, THR))
    d = lead_filter(d)
    d = text_filter(d, ["employee_name", "employee_id", "store_code"], search)
    low = d[d["Đánh giá"].str.startswith("DƯỚI")]
    ok = d[d["Đánh giá"].eq("ĐẠT")]
    c = st.columns(4)
    c[0].metric("Nhân sự đã trả bài", len(d))
    c[1].metric(f"Đạt (≥ {THR}%)", len(ok))
    c[2].metric(f"Dưới {THR}% → trả bài đợt 2", len(low))
    c[3].metric("Chưa có điểm", int(d["Đánh giá"].eq("CHƯA CÓ ĐIỂM").sum()))
    a, b = st.columns(2)
    with a:
        g = d.assign(KQ=np.where(d["Đánh giá"].eq("ĐẠT"), "Đạt", np.where(d["Đánh giá"].str.startswith("DƯỚI"),
                                                                           f"Dưới {THR}%", "Chưa có điểm")))
        g = g.groupby(["Lead", "KQ"]).size().reset_index(name="Số NV")
        bar_chart(g, "Lead", "Số NV", "Kết quả trả bài theo Lead", barmode="stack", color="KQ",
                  color_discrete_map={"Đạt": "#12b76a", f"Dưới {THR}%": "#f04438", "Chưa có điểm": "#98a2b3"})
    with b:
        pie_chart(["Đạt", f"Dưới {THR}%", "Chưa có điểm"],
                  [len(ok), len(low), len(d) - len(ok) - len(low)], "Tỷ lệ đạt / chưa đạt",
                  {"Đạt": "#12b76a", f"Dưới {THR}%": "#f04438", "Chưa có điểm": "#98a2b3"})
    st.markdown(f"#### Nhân sự dưới {THR}% – yêu cầu trả bài đợt 2 và follow")
    cols = ["Lead", "employee_name", "employee_id", "store_code", "score", "max_score", "pct", "qc_status", "field_name"]
    ren = {"employee_name": "Nhân viên", "employee_id": "MSNV", "store_code": "Mã cửa hàng", "score": "Điểm",
           "max_score": "Điểm tối đa", "pct": "% điểm", "qc_status": "QC", "field_name": "Field chấm"}
    lt = low.sort_values("pct")[cols].rename(columns=ren)
    lt["Đánh giá"] = f"DƯỚI {THR}% – TRẢ BÀI ĐỢT 2"
    show_df(lt, height=420, column_config={"% điểm": st.column_config.NumberColumn(format="%.1f%%")})
    if not lt.empty:
        dl_button(lt, "Duoi_nguong_tra_bai_d2", "NV_duoi_nguong_tra_bai_dot2.xlsx", "dl_low")
    with st.expander("Toàn bộ nhân sự đã trả bài"):
        allv = d.sort_values("pct")[cols + ["Đánh giá"]].rename(columns=ren)
        show_df(allv, height=420)

    t35 = match35(IV, THR, loose, stores)
    t94 = match94(IV, label, THR, loose, stores)
    t35 = text_filter(lead_filter(t35.rename(columns={"Leader": "Lead"})), ["Nhân sự", "Mã cửa hàng"], search)
    t94 = lead_filter(t94.rename(columns={"Leader": "Lead"}))
    if selected_region != "Tất cả":
        t94 = t94[t94["Miền"] == selected_region]
    t94 = text_filter(t94, ["MSNV", "Họ và Tên", "Shop"], search)
    s35, s94 = st.tabs(["🎤 35 NV cần test", "📱 94 NV eSIM"])
    with s35:
        a = st.columns(4)
        a[0].metric("Đã trả bài", int((t35["Đánh giá"] != "CHƯA TRẢ BÀI").sum()))
        a[1].metric("Đạt", int((t35["Đánh giá"] == "ĐẠT").sum()))
        a[2].metric(f"Dưới {THR}%", int(t35["Đánh giá"].str.startswith("DƯỚI").sum()))
        a[3].metric("Chưa trả bài", int((t35["Đánh giá"] == "CHƯA TRẢ BÀI").sum()))
        show_df(t35, height=520, column_config={"% điểm": st.column_config.NumberColumn(format="%.1f%%")})
        dl_button(t35, "35_NV", f"CPS_35NV_{label.replace(' ', '_')}.xlsx", "dl_35")
    with s94:
        a = st.columns(3)
        a[0].metric("Đã trả bài", int((~t94["Kết quả L2"].isin(["CHƯA TRẢ BÀI", "BẮT BUỘC TRẢ LẦN 2"])).sum()))
        a[1].metric("Đạt", int((t94["Kết quả L2"] == "ĐẠT").sum()))
        a[2].metric(f"Dưới {THR}%", int(t94["Kết quả L2"].str.startswith("DƯỚI").sum()))
        show_df(t94, height=520, column_config={"% điểm": st.column_config.NumberColumn(format="%.1f%%")})
        dl_button(t94, "94_eSIM", f"CPS_94NV_eSIM_{label.replace(' ', '_')}.xlsx", "dl_94")


def tab_reject(P):
    r = text_filter(lead_filter(P[P["Bị từ chối"]]), ["store", "Tên Plan", "Lead"], search)
    if r.empty:
        st.success("Không có plan bị từ chối / rework.")
        return
    cnt = r.groupby(["Nghiệp vụ"]).size().reset_index(name="Số plan")
    a, b = st.columns(2)
    with a:
        bar_chart(cnt, "Nghiệp vụ", "Số plan", "Plan bị từ chối theo nghiệp vụ")
    with b:
        g = r.groupby("Lead").size().reset_index(name="Số plan")
        bar_chart(g, "Lead", "Số plan", "Plan bị từ chối theo Lead")
    cols = ["Nghiệp vụ", "Lead", "store", "Hạng mục", "Tên Plan", "QC", "Ghi chú QC"]
    out = r[cols].rename(columns={"store": "Mã cửa hàng", "Ghi chú QC": "Lý do"}).sort_values(["Nghiệp vụ", "Lead"])
    show_df(out, height=520, column_config={"Lý do": st.column_config.TextColumn(width="large")})
    dl_button(out, "Plan_bi_tu_choi", "Plan_bi_tu_choi.xlsx", "dl_rej")


def tab_validation(P, bundle, label):
    sheets = bundle["sheets"]
    checks = [("Sheet Trade Audit", "PASS" if "Trade Audit" in sheets else "FAIL"),
              ("Sheet Trade Audit Plus", "PASS" if "Trade Audit Plus" in sheets else "FAIL"),
              ("Sheet Mystery Audit", "PASS" if "Mystery Audit" in sheets else "FAIL"),
              ("Giá trị cột Chấm trong file", ", ".join(bundle["rounds"])),
              ("Plan chưa nhận diện được hạng mục (Trade khác / Plus ?)",
               int(P["Hạng mục"].isin(["Trade khác", "Plus ?"]).sum())),
              ("QC Status không nhận diện được", int(P["QC"].eq("UNKNOWN").sum())),
              ("Cửa hàng trong raw không có trong DS", len(set(P["store"]) - set(stores["Mã cửa hàng"])))]
    show_df(pd.DataFrame(checks, columns=["Kiểm tra", "Kết quả"]).astype(str))
    st.markdown("#### Số plan theo nghiệp vụ / hệ thống / hạng mục")
    show_df(P.groupby(["Nghiệp vụ", "Hệ thống", "Hạng mục"]).size().reset_index(name="Số plan"))
    if not stores.empty:
        diff = P[(P["lead_raw"] != "") & (P["Lead"] != P["lead_raw"]) & P["store"].isin(stores["Mã cửa hàng"])]
        if not diff.empty:
            st.markdown("#### Shop có Lead trong raw khác DS cửa hàng (đang dùng Lead theo DS)")
            show_df(diff.drop_duplicates("store")[["store", "lead_raw", "Lead"]]
                    .rename(columns={"store": "Mã cửa hàng", "lead_raw": "Lead trong raw", "Lead": "Lead theo DS"}))
    miss = sorted(set(P["store"]) - set(stores["Mã cửa hàng"]))
    if miss:
        st.warning("Mã cửa hàng có trong raw nhưng không có trong DS: " + ", ".join(miss))


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
    bundle = compute_all(file_bytes, label, stores, DEFAULT_MAX)
    P = bundle["P"]
    if P.empty:
        st.error(f"File {fname} không có dữ liệu '{label}' trong cột Chấm. "
                 f"Giá trị Chấm tìm thấy: {bundle['rounds'] or 'không có cột Chấm'}")
        st.stop()
    cps_m, dtv_m, my_m, ls = analyze(P, label)
    camp = campus_matrix(P)
    tabs = st.tabs(["📊 Tổng quan", "🏬 CPS (4 hạng mục)", "🏪 DTV", "➕ Plus 1–5", "🕵️ Mystery",
                    "🎓 CAMPUS", "🎤 Trả bài (<80%)", "⚠️ Từ chối", "🧪 Kiểm tra"])
    with tabs[0]:
        tab_overview(P, cps_m, dtv_m, my_m, ls, label)
    with tabs[1]:
        tab_trade(cps_m, CPS_ITEMS, "CPS", "cps")
    with tabs[2]:
        if label == "Lần 2":
            st.info("Lần 2 không áp dụng DTV.")
        else:
            tab_trade(dtv_m, DTV_ITEMS, "DTV", "dtv")
    with tabs[3]:
        tab_plus(P)
    with tabs[4]:
        tab_mystery(my_m, P)
    with tabs[5]:
        tab_campus(camp)
    with tabs[6]:
        tab_interviews(bundle["IV"], label)
    with tabs[7]:
        tab_reject(P)
    with tabs[8]:
        tab_validation(P, bundle, label)


if view == "📊 CEO VIEW":
    frames = []
    for label, pre in [("Lần 1", "l1"), ("Lần 2", "l2")]:
        b = st.session_state.get(f"{pre}_bytes")
        if b is None:
            continue
        P = compute_all(b, label, stores, DEFAULT_MAX)["P"]
        if P.empty:
            continue
        ls = analyze(P, label)[3]
        ls.insert(0, "Đợt", label)
        frames.append(ls)
    if not frames:
        st.info("Nạp L1/L2 để so sánh.")
    else:
        df = pd.concat(frames, ignore_index=True)
        show_df(df, column_config=PCT_CFG(["% CPS", "% DTV", "% Mystery", "% Plus", "% KPI tổng (CPS+DTV+Mystery)"]))
        fig = px.bar(df, x="Lead", y="% KPI tổng (CPS+DTV+Mystery)", color="Đợt", barmode="group",
                     title="% KPI tổng theo Lead và đợt")
        fig.update_traces(texttemplate="%{y:.0f}%")
        show_chart(fig)
else:
    pre, label = ("l1", "Lần 1") if view == "📌 LẦN 1" else ("l2", "Lần 2")
    b = st.session_state.get(f"{pre}_bytes")
    if b is None:
        st.info(f"Chưa nạp file {label}.")
    else:
        render_round(b, st.session_state.get(f"{pre}_name"), label)
