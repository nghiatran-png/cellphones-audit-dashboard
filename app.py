import io
import math
import numbers
import re
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="CellphoneS Audit Platform",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from master_data import TARGET_35_NV_MASTER, TARGET_94_ESIM_L1
except ImportError:
    st.error(
        "Thiếu file master_data.py. Tạo file này cùng thư mục với app.py, "
        "chứa 2 danh sách TARGET_35_NV_MASTER và TARGET_94_ESIM_L1."
    )
    st.stop()

APP_VERSION = "3.6.0"
PASS_SCORE = 50
MYSTERY_TARGET = 153

# width="stretch" cho Streamlit mới, use_container_width cho bản cũ
_ver = tuple(int(p) for p in st.__version__.split(".")[:2] if p.isdigit())
STRETCH = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}

# ---------------- UI ----------------
st.markdown("""
<style>
:root{--brand:#d70018;--brand2:#8f0010;--line:#e4e7ec;--ink:#101828;--muted:#667085;}
.stApp{background:#f6f7f9}
.block-container{max-width:1680px;padding-top:1rem;padding-bottom:3rem}
.hero{display:flex;justify-content:space-between;align-items:center;padding:20px 24px;border-radius:16px;color:white;
background:linear-gradient(135deg,var(--brand),var(--brand2));box-shadow:0 12px 28px rgba(215,0,24,.16);margin-bottom:16px}
.hero-title{font-size:28px;font-weight:900} .hero-sub{font-size:13px;opacity:.86}
.hero-pill{padding:9px 13px;border-radius:999px;background:rgba(255,255,255,.14);font-weight:800}
div[data-testid="stMetric"]{background:white;border:1px solid var(--line);border-radius:14px;padding:14px}
div[data-testid="stMetricValue"]{font-weight:900;color:var(--ink)}
.stTabs [data-baseweb="tab-list"]{background:white;border:1px solid var(--line);padding:6px;border-radius:12px;gap:4px}
.stTabs [aria-selected="true"]{background:var(--brand)!important;color:white!important;border-radius:8px;font-weight:800}
</style>
""", unsafe_allow_html=True)


# ---------------- Normalize helpers ----------------
def norm(v):
    """Chuẩn hóa: bỏ dấu, đ->d, lower, gọn khoảng trắng."""
    if pd.isna(v):
        return ""
    s = str(v).replace("\u200b", "").replace("\ufeff", "").replace("\xa0", " ").strip().lower()
    s = s.replace("đ", "d")  # NFD không xử lý được đ
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


def norm_code(v):
    if pd.isna(v):
        return ""
    return re.sub(r"\s+", "", str(v)).upper()


def digits(v):
    if pd.isna(v):
        return ""
    return re.sub(r"\D", "", str(v)).lstrip("0")


DONE_QC = {"done", "pass", "passed", "approved", "approve", "ok", "dat",
           "qc done", "completed", "hoan thanh", "da duyet"}
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
    if s in DONE_QC:
        return "DONE"
    return "UNKNOWN"


def is_field_done(series):
    return series.apply(norm).isin(DONE_FIELD)


def rounded_score(v):
    """Làm tròn half-up như Excel. 49.99 -> 50, 49.5 -> 50."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f):
        return None
    return int(math.floor(f + 0.5))


def eval_score(v):
    r = rounded_score(v)
    if r is None:
        return "CHƯA CÓ ĐIỂM"
    return "ĐẠT" if r >= PASS_SCORE else "KHÔNG ĐẠT"


def text_filter(df, cols, q):
    q = norm(q)
    if not q or df is None or df.empty:
        return df
    mask = pd.Series(False, index=df.index)
    for c in cols:
        if c in df.columns:
            mask |= df[c].apply(norm).str.contains(q, regex=False)
    return df[mask]


def show_df(df, height=None):
    kw = {"hide_index": True, **STRETCH}
    if height:
        kw["height"] = height
    st.dataframe(df, **kw)


def show_chart(fig):
    st.plotly_chart(fig, **STRETCH)


# ---------------- File loading ----------------
for _k in ["l1_bytes", "l1_name", "l2_bytes", "l2_name"]:
    if _k not in st.session_state:
        st.session_state[_k] = None

USECOLS = {
    "Mystery Audit": ["Tên Plan", "Chấm", "Hệ thống", "Mã cửa hàng", "Tên Leader", "Tên nhân viên thực hiện",
                      "Ngày update", "Status Plan", "QC Status", "Ngày thực hiện", "Hạng mục"],
    "Trade Audit": ["Tên Plan", "Chấm", "Hệ thống", "Mã cửa hàng", "Tên Leader", "Tên nhân viên thực hiện",
                    "Ngày update", "Status Plan", "QC Status", "Ngày thực hiện", "Hạng mục", "Result",
                    "Category", "Sub-category", "KPI", "QC note"],
    "Trade Audit Plus": ["Tên Plan", "Chấm", "Hệ thống", "Mã cửa hàng", "Tên Leader", "Tên nhân viên thực hiện",
                         "Ngày update", "Status Plan", "QC Status", "Ngày thực hiện", "MSNV", "Mã câu hỏi",
                         "Câu hỏi chính", "Câu trả lời", "Trả lời ngay", "Trả lời Phụ", "Trả lời có tài liệu",
                         "Có xem tài liệu", "Thang điểm", "Thực đạt", "QC note"],
}


def canon_sheet(name):
    """Nhận diện sheet theo từ khóa, không phụ thuộc tên chính xác."""
    n = norm(name)
    if "mystery" in n:
        return "Mystery Audit"
    if "trade" in n and "plus" in n:
        return "Trade Audit Plus"
    if "trade" in n:
        return "Trade Audit"
    return None


@st.cache_data(show_spinner="Đang đọc file Excel...", max_entries=4)
def load_report(file_bytes):
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    out = {}
    for s in xls.sheet_names:
        key = canon_sheet(s)
        if key is None or key in out:
            continue
        wanted = set(USECOLS[key])
        df = pd.read_excel(xls, sheet_name=s, usecols=lambda c, w=wanted: str(c).strip() in w)
        df.columns = [str(c).strip() for c in df.columns]
        out[key] = df
    return out


def save_upload(uploaded, prefix):
    if uploaded:
        st.session_state[f"{prefix}_bytes"] = uploaded.getvalue()
        st.session_state[f"{prefix}_name"] = uploaded.name


def get_round(prefix):
    return st.session_state.get(f"{prefix}_bytes"), st.session_state.get(f"{prefix}_name")


# ---------------- Round / plan level ----------------
def round_number(v):
    m = re.search(r"(\d+)", norm(v))
    return int(m.group(1)) if m else None


def filter_round(df, label):
    """Chỉ trả đúng dữ liệu của vòng. Thiếu cột Chấm -> rỗng (không dùng dữ liệu vòng khác)."""
    if df is None or df.empty or "Chấm" not in df.columns:
        return pd.DataFrame()
    wanted = round_number(label)
    return df[df["Chấm"].apply(round_number).eq(wanted)].copy()


def available_rounds(sheets):
    vals = set()
    for df in sheets.values():
        if "Chấm" in df.columns:
            vals |= {str(v) for v in df["Chấm"].dropna().unique()}
    return sorted(vals)


def plan_level(df):
    if df is None or df.empty or "Tên Plan" not in df.columns:
        return pd.DataFrame()
    x = df[df["Tên Plan"].notna()].copy()
    x["Tên Plan"] = x["Tên Plan"].astype(str).str.strip()
    x = x[x["Tên Plan"].ne("")]
    if "Ngày update" in x.columns:
        x["_dt"] = pd.to_datetime(x["Ngày update"], errors="coerce", dayfirst=True)
        # NaT xuống đầu để keep="last" luôn lấy dòng có ngày mới nhất
        x = x.sort_values("_dt", na_position="first", kind="stable").drop(columns="_dt")
    return x.drop_duplicates("Tên Plan", keep="last").reset_index(drop=True)


def mystery_scenario_series(df):
    if df is None or df.empty:
        return pd.Series(dtype=str)
    if "Hạng mục" in df.columns:
        s = df["Hạng mục"].fillna("").astype(str).str.strip()
        if s.ne("").any():
            return s.where(s.ne(""), "Chưa rõ")
    plan = df["Tên Plan"].fillna("").astype(str) if "Tên Plan" in df.columns else pd.Series("", index=df.index)

    def parse(v):
        t = norm(v)
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
        return str(v).strip() or "Chưa rõ"

    return plan.apply(parse)


# ---------------- Plus interview engine ----------------
FLAG_COLS = ["Trả lời ngay", "Trả lời Phụ", "Trả lời có tài liệu", "Có xem tài liệu"]


def boolish(v):
    if pd.isna(v):
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, numbers.Number):
        return bool(v)
    return norm(v) in {"true", "1", "yes", "y", "x", "co", "ok"}


def plus_interviews(plus_df):
    if plus_df is None or plus_df.empty:
        return pd.DataFrame()
    if not {"Mã câu hỏi", "Tên Plan"}.issubset(plus_df.columns):
        return pd.DataFrame()

    x = plus_df[plus_df["Tên Plan"].notna()].copy()
    x["Tên Plan"] = x["Tên Plan"].astype(str).str.strip()  # chuẩn hóa TRƯỚC khi tính điểm

    answered = pd.Series(False, index=x.index)
    for c in FLAG_COLS:
        if c in x.columns:
            answered = answered | x[c].apply(boolish)

    thuc = pd.to_numeric(x["Thực đạt"], errors="coerce") if "Thực đạt" in x.columns else None
    if thuc is not None and thuc.notna().any():
        score = thuc.groupby(x["Tên Plan"]).sum(min_count=1)
    elif "Thang điểm" in x.columns:
        pts = pd.to_numeric(x["Thang điểm"], errors="coerce").fillna(0).where(answered, 0)
        score = pts.groupby(x["Tên Plan"]).sum()
    else:
        score = pd.Series(dtype=float)

    tt1 = x[x["Mã câu hỏi"].astype(str).str.strip().str.upper().eq("TT1")].copy()
    if tt1.empty:
        return pd.DataFrame()

    def col(name, default=""):
        return tt1[name].fillna("").astype(str).str.strip() if name in tt1.columns else default

    out = pd.DataFrame({
        "plan_name": tt1["Tên Plan"],
        "store_code": tt1["Mã cửa hàng"].apply(norm_code) if "Mã cửa hàng" in tt1.columns else "",
        "leader": col("Tên Leader"),
        "field_name": col("Tên nhân viên thực hiện"),
        "employee_id": col("MSNV"),
        "employee_name": col("Câu trả lời"),
        "qc_status": tt1["QC Status"].apply(classify_qc) if "QC Status" in tt1.columns else "NONE",
        "status_plan": col("Status Plan"),
        "updated_at": pd.to_datetime(tt1["Ngày update"], errors="coerce", dayfirst=True)
        if "Ngày update" in tt1.columns else pd.NaT,
    })
    out["score"] = out["plan_name"].map(score)
    out["evaluation"] = out["score"].apply(eval_score)
    out = out[out["employee_name"].apply(norm).ne("")]
    out = out.sort_values("updated_at", na_position="first", kind="stable")
    return out.drop_duplicates("plan_name", keep="last").reset_index(drop=True)


# ---------------- 35 / 94 matching ----------------
def _prep(interviews):
    x = interviews.copy()
    if not x.empty:
        x["_name"] = x["employee_name"].apply(norm)
        x["_store"] = x["store_code"].apply(norm_code)
        x["_id"] = x["employee_id"].apply(digits)
    return x


def _match_name_store(x, name, store, loose=False):
    if x.empty:
        return x
    n = norm(name)
    nm = x[x["_name"] == n]
    if nm.empty and len(n) >= 6:  # tên bị cắt cụt trong master
        nm = x[x["_name"].str.startswith(n)]
    if nm.empty:
        return nm
    raw_store = str(store)
    s = norm_code(raw_store).replace(".", "")
    if "..." in raw_store:  # mã shop bị cắt cụt -> khớp tiền tố
        by_store = nm[nm["_store"].str.startswith(s)]
    else:
        by_store = nm[nm["_store"] == s]
    if not by_store.empty:
        return by_store
    return nm if loose else by_store


def _latest(cand):
    return cand.sort_values("updated_at", na_position="first", kind="stable").iloc[-1]


def match35(interviews, loose=False):
    x = _prep(interviews)
    rows = []
    for m in TARGET_35_NV_MASTER:
        cand = _match_name_store(x, m["Tên"], m["Mã cửa hàng"], loose)
        if cand.empty:
            rows.append({"Nhân sự": m["Tên"], "Mã cửa hàng": m["Mã cửa hàng"], "Leader": m["Leader"],
                         "Điểm gốc": None, "Điểm trả bài": None, "Đánh giá": "CHƯA TRẢ BÀI",
                         "QC Status": "NONE", "Field": "", "Ngày update": pd.NaT})
        else:
            r = _latest(cand)
            rows.append({"Nhân sự": m["Tên"], "Mã cửa hàng": m["Mã cửa hàng"], "Leader": m["Leader"],
                         "Điểm gốc": r["score"], "Điểm trả bài": rounded_score(r["score"]),
                         "Đánh giá": eval_score(r["score"]), "QC Status": r["qc_status"],
                         "Field": r["field_name"], "Ngày update": r["updated_at"]})
    df = pd.DataFrame(rows)
    df["Điểm gốc"] = pd.to_numeric(df["Điểm gốc"], errors="coerce")
    df["Điểm trả bài"] = pd.to_numeric(df["Điểm trả bài"], errors="coerce").astype("Int64")
    return df


def match94(interviews, label, loose=False):
    x = _prep(interviews)
    missing_label = "BẮT BUỘC TRẢ LẦN 2" if label == "Lần 2" else "CHƯA TRẢ BÀI"
    rows = []
    for m in TARGET_94_ESIM_L1:
        cand = pd.DataFrame()
        if not x.empty:
            tid = digits(m["MSNV"])
            if tid:
                cand = x[x["_id"] == tid]
            if cand.empty:
                cand = _match_name_store(x, m["Tên"], m["Shop"], loose)
        base = {"STT": m["STT"], "MSNV": m["MSNV"], "Họ và Tên": m["Tên"], "Shop": m["Shop"],
                "Miền": m["Miền"], "Leader": m["Leader"]}
        if cand.empty:
            rows.append({**base, "Field": "", "Điểm L2 gốc": None, "Điểm L2": None,
                         "Kết quả L2": missing_label})
        else:
            r = _latest(cand)
            rows.append({**base, "Field": r["field_name"], "Điểm L2 gốc": r["score"],
                         "Điểm L2": rounded_score(r["score"]), "Kết quả L2": eval_score(r["score"])})
    df = pd.DataFrame(rows)
    df["Điểm L2 gốc"] = pd.to_numeric(df["Điểm L2 gốc"], errors="coerce")
    df["Điểm L2"] = pd.to_numeric(df["Điểm L2"], errors="coerce").astype("Int64")
    return df


# ---------------- Metrics ----------------
QC_KEYS = ["DONE", "PENDING", "PENDING_REVIEW", "REJECT", "REWORK", "UNKNOWN"]


def qc_counts(pl):
    if pl.empty or "QC Status" not in pl.columns:
        return {k: 0 for k in QC_KEYS}
    q = pl["QC Status"].apply(classify_qc)
    return {k: int((q == k).sum()) for k in QC_KEYS}


def field_done(pl):
    if pl.empty or "Status Plan" not in pl.columns:
        return 0
    return int(is_field_done(pl["Status Plan"]).sum())


def metrics(sheets, round_label):
    trade_all = sheets.get("Trade Audit", pd.DataFrame())
    plus_all = sheets.get("Trade Audit Plus", pd.DataFrame())
    mystery = sheets.get("Mystery Audit", pd.DataFrame())  # luồng KPI riêng, KHÔNG lọc theo L1/L2

    trade = filter_round(trade_all, round_label)
    plus = filter_round(plus_all, round_label)

    tplan = plan_level(trade)
    pplan = plan_level(plus)
    mplan = plan_level(mystery)
    interviews = plus_interviews(plus)

    system = (tplan["Hệ thống"].fillna("").astype(str).str.upper().str.strip()
              if not tplan.empty and "Hệ thống" in tplan.columns else pd.Series(dtype=str))

    def count_stores(sysname):
        if system.empty or "Mã cửa hàng" not in tplan.columns:
            return 0
        return int(tplan.loc[system.eq(sysname), "Mã cửa hàng"].apply(norm_code).nunique())

    cps_stores = count_stores("CPS")
    dtv_stores = count_stores("DTV")

    if round_label == "Lần 2" and not system.empty:
        tplan_scope = tplan[system.eq("CPS")].copy()  # L2 loại DTV
    else:
        tplan_scope = tplan.copy()

    return {
        "trade_plan": tplan_scope, "trade_plan_all": tplan,
        "plus_plan": pplan, "mystery_plan": mplan, "interviews": interviews,
        "trade_cps_stores": cps_stores,
        "trade_dtv_stores": 0 if round_label == "Lần 2" else dtv_stores,
        "trade_plans": len(tplan_scope), "plus_plans": len(pplan), "mystery_plans": len(mplan),
        "plus_stores": int(pplan["Mã cửa hàng"].apply(norm_code).nunique())
        if not pplan.empty and "Mã cửa hàng" in pplan.columns else 0,
        "trade_field_done": field_done(tplan_scope), "plus_field_done": field_done(pplan),
        "mystery_field_done": field_done(mplan),
        "trade_qc": qc_counts(tplan_scope), "plus_qc": qc_counts(pplan), "mystery_qc": qc_counts(mplan),
    }


@st.cache_data(show_spinner="Đang tính toán...", max_entries=8)
def compute_metrics(file_bytes, round_label):
    return metrics(load_report(file_bytes), round_label)


def mystery_by_leader_scenario(m):
    cols = ["Leader", "Kịch bản", "Tổng Plan", "Field Done", "QC Done", "QC Pending", "Chưa hoàn thành"]
    x = m["mystery_plan"].copy()
    if x.empty:
        return pd.DataFrame(columns=cols)
    x["Leader"] = (x["Tên Leader"].fillna("Chưa gán").astype(str).str.strip()
                   if "Tên Leader" in x.columns else "Chưa gán")
    x["Kịch bản"] = mystery_scenario_series(x)
    x["_fd"] = is_field_done(x["Status Plan"]) if "Status Plan" in x.columns else False
    x["_qc"] = x["QC Status"].apply(classify_qc) if "QC Status" in x.columns else "NONE"
    g = x.groupby(["Leader", "Kịch bản"], dropna=False).agg(
        **{
            "Tổng Plan": ("Tên Plan", "nunique"),
            "Field Done": ("_fd", "sum"),
            "QC Done": ("_qc", lambda s: int((s == "DONE").sum())),
            "QC Pending": ("_qc", lambda s: int(s.isin(["PENDING", "PENDING_REVIEW"]).sum())),
        }
    ).reset_index()
    g["Chưa hoàn thành"] = g["Tổng Plan"] - g["QC Done"]
    return g


def store_completion(m):
    """1 dòng / cửa hàng. Module hoàn thành = mọi plan hiện có đều Field Done và QC Done."""
    mods = ["Trade", "Plus", "Mystery"]
    frames = []
    for mod, key in [("Trade", "trade_plan"), ("Plus", "plus_plan"), ("Mystery", "mystery_plan")]:
        x = m[key]
        if x.empty or "Mã cửa hàng" not in x.columns:
            continue
        y = x.copy()
        y["_store"] = y["Mã cửa hàng"].apply(norm_code)
        y = y[y["_store"].ne("")]
        if y.empty:
            continue
        y["_fd"] = is_field_done(y["Status Plan"]) if "Status Plan" in y.columns else False
        y["_qd"] = y["QC Status"].apply(classify_qc).eq("DONE") if "QC Status" in y.columns else False
        y["_leader"] = (y["Tên Leader"].fillna("").astype(str).str.strip()
                        if "Tên Leader" in y.columns else "")
        y["_mod"] = mod
        frames.append(y[["_store", "_leader", "_mod", "Tên Plan", "_fd", "_qd"]])
    if not frames:
        return pd.DataFrame()

    allp = pd.concat(frames, ignore_index=True)
    rows = []
    for store, s in allp.groupby("_store"):
        row = {"Mã cửa hàng": store, "Leader": next((v for v in s["_leader"] if v), "")}
        parts = []
        for mod in mods:
            z = s[s["_mod"] == mod]
            if z.empty:
                row[mod] = "Chưa có data"
                row[f"{mod} tiến độ"] = ""
                continue
            plans = len(z)
            fd, qd = int(z["_fd"].sum()), int(z["_qd"].sum())
            done = fd >= plans and qd >= plans
            row[mod] = "✅ Hoàn thành" if done else "⏳ Chưa hoàn thành"
            row[f"{mod} tiến độ"] = f"Field {fd}/{plans} · QC {qd}/{plans}"
            parts.append(done)
        row["Tổng trạng thái"] = "✅ HOÀN THÀNH" if parts and all(parts) else "⏳ CHƯA HOÀN THÀNH"
        rows.append(row)
    return pd.DataFrame(rows)


def leader_summary(m):
    frames = []
    for label, key in [("Trade", "trade_plan"), ("Plus", "plus_plan"), ("Mystery", "mystery_plan")]:
        x = m[key]
        if x.empty:
            continue
        y = x.copy()
        y["Leader"] = (y["Tên Leader"].fillna("Chưa gán").astype(str).str.strip()
                       if "Tên Leader" in y.columns else "Chưa gán")
        y["QC"] = y["QC Status"].apply(classify_qc) if "QC Status" in y.columns else "NONE"
        y["Mã cửa hàng"] = y["Mã cửa hàng"] if "Mã cửa hàng" in y.columns else ""
        y["Nghiệp vụ"] = label
        frames.append(y[["Tên Plan", "Mã cửa hàng", "Leader", "QC", "Nghiệp vụ"]])
    if not frames:
        return pd.DataFrame()
    z = pd.concat(frames, ignore_index=True).drop_duplicates(["Tên Plan", "Nghiệp vụ"])
    return z.groupby("Leader").agg(
        Shop=("Mã cửa hàng", "nunique"),
        Plan=("Tên Plan", "nunique"),
        QC_Done=("QC", lambda s: int((s == "DONE").sum())),
        QC_Pending=("QC", lambda s: int(s.isin(["PENDING", "PENDING_REVIEW"]).sum())),
        QC_Reject_Rework=("QC", lambda s: int(s.isin(["REJECT", "REWORK"]).sum())),
    ).reset_index()


# ---------------- Excel export ----------------
def dataframe_to_excel_bytes(df, sheet_name):
    """Export đúng dữ liệu đang hiển thị, không dùng formula để đánh giá lại."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        wb = writer.book
        ws = writer.sheets[sheet_name]

        header_fmt = wb.add_format({"bold": True, "font_color": "white", "bg_color": "#D70018",
                                    "border": 1, "align": "center", "valign": "vcenter"})
        pass_fmt = wb.add_format({"bg_color": "#D1E7DD", "font_color": "#0F5132", "bold": True})
        fail_fmt = wb.add_format({"bg_color": "#F8D7DA", "font_color": "#842029", "bold": True})
        wait_fmt = wb.add_format({"bg_color": "#FFF3CD", "font_color": "#664D03", "bold": True})

        for i, name in enumerate(df.columns):
            ws.write(0, i, name, header_fmt)
            body = int(df[name].astype(str).map(len).quantile(.90)) + 2 if len(df) else 12
            ws.set_column(i, i, min(max(len(str(name)) + 2, body), 42))

        last = max(len(df), 1)
        for cand in ["Kết quả L2", "Đánh giá"]:
            if cand in df.columns:
                c = df.columns.get_loc(cand)
                # dùng so sánh bằng, KHÔNG dùng "containing" (ĐẠT nằm trong KHÔNG ĐẠT)
                ws.conditional_format(1, c, last, c, {"type": "cell", "criteria": "==",
                                                      "value": '"ĐẠT"', "format": pass_fmt})
                ws.conditional_format(1, c, last, c, {"type": "cell", "criteria": "==",
                                                      "value": '"KHÔNG ĐẠT"', "format": fail_fmt})
                for prefix in ["BẮT BUỘC", "CHƯA"]:
                    ws.conditional_format(1, c, last, c, {"type": "text", "criteria": "begins with",
                                                          "value": prefix, "format": wait_fmt})
        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, len(df), len(df.columns) - 1)
    return output.getvalue()


# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown("### 🖥️ MÀN HÌNH ĐIỀU HÀNH")
    view = st.radio("Chế độ", ["📌 LẦN 1", "📌 LẦN 2", "📊 CEO VIEW"], index=1)
    st.divider()
    u1 = st.file_uploader("Raw Data Lần 1", type=["xlsx", "xls"], key="up_l1")
    if u1:
        save_upload(u1, "l1")
        st.success("Đã nạp L1")
    u2 = st.file_uploader("Raw Data Lần 2", type=["xlsx", "xls"], key="up_l2")
    if u2:
        save_upload(u2, "l2")
        st.success("Đã nạp L2")
    st.divider()
    leaders = sorted({x["Leader"] for x in TARGET_35_NV_MASTER} | {x["Leader"] for x in TARGET_94_ESIM_L1})
    selected_leader = st.selectbox("Leader", ["Tất cả"] + leaders)
    selected_region = st.selectbox("Miền", ["Tất cả", "Miền Bắc", "Miền Nam"])
    search = st.text_input("Tìm NV / MSNV / Shop", "")
    loose = st.checkbox("Khớp theo tên khi lệch mã shop", value=False,
                        help="Bật nếu nhân sự trả bài ở shop khác với master. Có thể khớp nhầm người trùng tên.")

st.markdown(f"""
<div class="hero"><div><div class="hero-title">📱 CELLPHONES ENTERPRISE AUDIT — {view}</div>
<div class="hero-sub">Plan-level engine • Trade • Plus • Mystery • Interview • QC</div></div>
<div class="hero-pill">v{APP_VERSION}</div></div>
""", unsafe_allow_html=True)


# ---------------- Render ----------------
def render_round(file_bytes, fname, label):
    sheets = load_report(file_bytes)
    m = compute_metrics(file_bytes, label)

    if not sheets:
        st.error(f"File {fname} không có sheet Trade Audit / Trade Audit Plus / Mystery Audit.")
        st.stop()

    if not any([m["trade_plans"], m["plus_plans"], m["mystery_plans"]]):
        st.error(f"File {fname} không có dữ liệu '{label}' trong cột Chấm. "
                 f"Các giá trị Chấm tìm thấy: {available_rounds(sheets) or 'không có cột Chấm'}")
        st.stop()

    t35 = match35(m["interviews"], loose)
    t94 = match94(m["interviews"], label, loose)
    tested = int((t35["Đánh giá"] != "CHƯA TRẢ BÀI").sum())
    passed = int((t35["Đánh giá"] == "ĐẠT").sum())

    rework_count = sum(m[k][s] for k in ["trade_qc", "plus_qc", "mystery_qc"] for s in ["REJECT", "REWORK"])

    if label == "Lần 2":
        c = st.columns(5)
        c[0].metric("Trade CPS Stores", m["trade_cps_stores"])
        c[1].metric("Plus Stores", m["plus_stores"])
        c[2].metric("Mystery Field Done", f'{m["mystery_field_done"]} / {MYSTERY_TARGET}')
        c[3].metric("35 NV đã trả bài", f"{tested} / 35")
        c[4].metric("Rework/Reject Plans", rework_count)
    else:
        c = st.columns(6)
        c[0].metric("Trade CPS Stores", m["trade_cps_stores"])
        c[1].metric("Trade DTV Stores", m["trade_dtv_stores"])
        c[2].metric("Plus Stores", m["plus_stores"])
        c[3].metric("Mystery Field Done", f'{m["mystery_field_done"]} / {MYSTERY_TARGET}')
        c[4].metric("35 NV đã trả bài", f"{tested} / 35")
        c[5].metric("Rework/Reject Plans", rework_count)

    tabs = st.tabs(["📊 Executive", "🏪 Shop Status", "🎤 35 NV", "📱 94 eSIM", "➕ Audit Plus",
                    "🕵️ Mystery", "👤 Leader", "⚠️ Rework", "🧪 Validation"])

    def pending(k):
        return m[k]["PENDING"] + m[k]["PENDING_REVIEW"]

    def rework(k):
        return m[k]["REJECT"] + m[k]["REWORK"]

    with tabs[0]:
        overview = pd.DataFrame([
            {"Nghiệp vụ": "Trade CPS" if label == "Lần 2" else "Trade", "Plan": m["trade_plans"],
             "Field Done": m["trade_field_done"], "QC Done": m["trade_qc"]["DONE"],
             "QC Pending": pending("trade_qc"), "Reject/Rework": rework("trade_qc"),
             "QC khác": m["trade_qc"]["UNKNOWN"]},
            {"Nghiệp vụ": "Plus", "Plan": m["plus_plans"], "Field Done": m["plus_field_done"],
             "QC Done": m["plus_qc"]["DONE"], "QC Pending": pending("plus_qc"),
             "Reject/Rework": rework("plus_qc"), "QC khác": m["plus_qc"]["UNKNOWN"]},
            {"Nghiệp vụ": "Mystery (toàn kỳ)", "Plan": m["mystery_plans"],
             "Field Done": m["mystery_field_done"], "QC Done": m["mystery_qc"]["DONE"],
             "QC Pending": pending("mystery_qc"), "Reject/Rework": rework("mystery_qc"),
             "QC khác": m["mystery_qc"]["UNKNOWN"]},
        ])
        show_df(overview)
        show_chart(px.bar(overview, x="Nghiệp vụ", y=["Field Done", "QC Done", "QC Pending"],
                          barmode="group", title="Tiến độ plan-level"))

    with tabs[1]:
        ss = store_completion(m)
        if not ss.empty:
            if selected_leader != "Tất cả":
                ss = ss[ss["Leader"] == selected_leader]
            ss = text_filter(ss, ["Mã cửa hàng", "Leader"], search)
        st.subheader("🏪 Trạng thái hoàn thành theo từng cửa hàng")
        st.caption("Hoàn thành module = tất cả Plan hiện có của module tại shop đều Field Done và QC Done.")
        show_df(ss, height=650)

    with tabs[2]:
        v = t35.copy()
        if selected_leader != "Tất cả":
            v = v[v["Leader"] == selected_leader]
        v = text_filter(v, ["Nhân sự", "Mã cửa hàng"], search)
        a, b, c2, d = st.columns(4)
        a.metric("Đã trả bài", tested)
        b.metric("ĐẠT (49.99→50)", passed)
        c2.metric("Không đạt/Chưa điểm", int(t35["Đánh giá"].isin(["KHÔNG ĐẠT", "CHƯA CÓ ĐIỂM"]).sum()))
        d.metric("Chưa trả bài", int((t35["Đánh giá"] == "CHƯA TRẢ BÀI").sum()))
        show_df(v, height=600)
        st.download_button(
            "📥 Xuất Excel 35 NV",
            data=dataframe_to_excel_bytes(v, "35_NV"),
            file_name=f"CPS_35NV_{label.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with tabs[3]:
        v = t94.copy()
        if selected_leader != "Tất cả":
            v = v[v["Leader"] == selected_leader]
        if selected_region != "Tất cả":
            v = v[v["Miền"] == selected_region]
        v = text_filter(v, ["MSNV", "Họ và Tên", "Shop"], search)
        show_df(v, height=600)
        st.caption("Điểm L2 = điểm làm tròn (49.99 → 50 → ĐẠT). Cột 'Điểm L2 gốc' giữ để đối chiếu.")
        st.download_button(
            "📥 Xuất Excel 94 NV eSIM",
            data=dataframe_to_excel_bytes(v, "94_ESIM_L2"),
            file_name=f"CPS_94NV_eSIM_{label.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with tabs[4]:
        st.caption(f'Có nhân viên trả bài: {len(m["interviews"])} / {m["plus_plans"]} plan Plus')
        show_df(m["interviews"], height=620)

    with tabs[5]:
        mp = m["mystery_plan"].copy()
        scen = mystery_by_leader_scenario(m)
        if selected_leader != "Tất cả" and not scen.empty:
            scen = scen[scen["Leader"] == selected_leader]

        a, b, c2, d = st.columns(4)
        a.metric("Mystery unique Plan", m["mystery_plans"])
        b.metric("Field Done", m["mystery_field_done"])
        c2.metric("QC Done", m["mystery_qc"]["DONE"])
        d.metric("QC Pending", pending("mystery_qc"))

        st.markdown("#### Kịch bản theo từng Leader")
        show_df(scen)
        if not scen.empty:
            show_chart(px.bar(scen, x="Leader", y="Tổng Plan", color="Kịch bản", barmode="stack",
                              title="Cơ cấu kịch bản Mystery theo Leader"))

        st.markdown("#### Chi tiết Plan Mystery")
        cols = [c3 for c3 in ["Tên Plan", "Mã cửa hàng", "Tên Leader", "Hạng mục", "Status Plan",
                              "QC Status", "Ngày update", "Ngày thực hiện"] if c3 in mp.columns]
        show_df(mp[cols] if cols else mp, height=560)

    with tabs[6]:
        ls = leader_summary(m)
        show_df(ls)
        if not ls.empty:
            show_chart(px.bar(ls, x="Leader", y=["QC_Done", "QC_Pending", "QC_Reject_Rework"],
                              barmode="stack", title="QC theo unique Plan"))

    with tabs[7]:
        parts = []
        for key, name in [("trade_plan", "Trade"), ("plus_plan", "Plus"), ("mystery_plan", "Mystery")]:
            x = m[key]
            if x.empty or "QC Status" not in x.columns:
                continue
            r = x[x["QC Status"].apply(classify_qc).isin(["REJECT", "REWORK"])].copy()
            if not r.empty:
                r["Nghiệp vụ"] = name
                parts.append(r)
        rw = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        if rw.empty:
            st.success("Không có Plan Rework/Reject theo dữ liệu hiện tại.")
        else:
            show_df(rw, height=600)

    with tabs[8]:
        checks = pd.DataFrame([
            {"Check": "Sheet Trade Audit", "Value": "PASS" if "Trade Audit" in sheets else "FAIL"},
            {"Check": "Sheet Trade Audit Plus", "Value": "PASS" if "Trade Audit Plus" in sheets else "FAIL"},
            {"Check": "Sheet Mystery Audit", "Value": "PASS" if "Mystery Audit" in sheets else "FAIL"},
            {"Check": "Giá trị cột Chấm trong file", "Value": ", ".join(available_rounds(sheets))},
            {"Check": f"{label} Trade plans", "Value": m["trade_plans"]},
            {"Check": f"{label} Plus plans", "Value": m["plus_plans"]},
            {"Check": "Mystery plans (không lọc L1/L2)", "Value": m["mystery_plans"]},
            {"Check": "QC Status không nhận diện được (Trade/Plus/Mystery)",
             "Value": f'{m["trade_qc"]["UNKNOWN"]} / {m["plus_qc"]["UNKNOWN"]} / {m["mystery_qc"]["UNKNOWN"]}'},
            {"Check": "Master 35 còn mã shop '...' (khớp theo tiền tố)",
             "Value": sum("..." in x["Mã cửa hàng"] for x in TARGET_35_NV_MASTER)},
        ])
        checks["Value"] = checks["Value"].astype(str)
        show_df(checks)
        st.info("L2 bỏ DTV; Mystery đọc toàn kỳ; QC đếm unique Plan; điểm làm tròn half-up (49.99 → 50 = ĐẠT).")


# ---------------- Main ----------------
if view == "📊 CEO VIEW":
    rows = []
    for label, prefix in [("Lần 1", "l1"), ("Lần 2", "l2")]:
        b, _ = get_round(prefix)
        if b is None:
            continue
        m = compute_metrics(b, label)
        row = {"Đợt": label, "Trade CPS": m["trade_cps_stores"], "Plus Stores": m["plus_stores"],
               "Mystery Field Done": m["mystery_field_done"], "Mystery QC Done": m["mystery_qc"]["DONE"],
               "Trade QC Done": m["trade_qc"]["DONE"], "Plus QC Done": m["plus_qc"]["DONE"]}
        if label != "Lần 2":
            row["Trade DTV"] = m["trade_dtv_stores"]
        rows.append(row)
    if not rows:
        st.info("Nạp L1/L2 để so sánh.")
    else:
        df = pd.DataFrame(rows)
        show_df(df)
        show_chart(px.bar(df, x="Đợt", y=["Trade QC Done", "Plus QC Done", "Mystery QC Done"], barmode="group"))
else:
    prefix = "l1" if view == "📌 LẦN 1" else "l2"
    label = "Lần 1" if prefix == "l1" else "Lần 2"
    b, fname = get_round(prefix)
    if b is None:
        st.info(f"Chưa nạp file {label}.")
    else:
        render_round(b, fname, label)
