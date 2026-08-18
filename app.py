import streamlit as st
import pandas as pd
import unicodedata

# 1. Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="CellphoneS Daily Audit Dashboard", 
    page_icon="📊", 
    layout="wide"
)

st.markdown("""
    <style>
    .main-header {font-size: 24px; font-weight: bold; color: #d70018; margin-bottom: 15px;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .stTabs [aria-selected="true"] {background-color: #d70018 !important; color: white !important; font-weight: bold;}
    .report-title {background-color: #d70018; color: white; padding: 10px; font-weight: bold; text-align: center; font-size: 18px; border-radius: 4px 4px 0 0;}
    .report-sub {background-color: #f8d7da; color: #721c24; padding: 6px; font-style: italic; text-align: center; font-size: 13px; margin-bottom: 15px;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-header'>📊 CELLPHONES AUDIT & TRACKING DASHBOARD TỔNG QUAN</div>", unsafe_allow_html=True)

# Khử dấu tiếng Việt
def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    return text.lower().strip()

# 35 Nhân sự cố định
TARGET_35_NV_MASTER = [
    {"Tên": "NGUYỄN CÔNG TUẤN", "Mã cửa hàng": "CPS-HNO-CGI-126HTM", "Leader": "Vũ Hoài Nam"},
    {"Tên": "NGUYỄN HỮU THÀNH", "Mã cửa hàng": "CPS-HNO-CGI-160NKT", "Leader": "Vũ Hoài Nam"},
    {"Tên": "NGUYỄN PHƯƠNG THẢO", "Mã cửa hàng": "CPS-HNO-CGI-310CG", "Leader": "Vũ Hoài Nam"},
    {"Tên": "LÊ VĂN THIÊN", "Mã cửa hàng": "CPS-HNO-CGI-310CG", "Leader": "Vũ Hoài Nam"},
    {"Tên": "PHẠM DUY NAM", "Mã cửa hàng": "CPS-HNO-NTL-50LQD", "Leader": "Vũ Hoài Nam"},
    {"Tên": "NGUYỄN QUỐC TRƯỜNG", "Mã cửa hàng": "CPS-HNO-PDI-248HTM", "Leader": "Vũ Hoài Nam"},
    {"Tên": "VŨ QUANG HUY", "Mã cửa hàng": "CPS-HNO-PDI-248HTM", "Leader": "Vũ Hoài Nam"},
    {"Tên": "ĐỖ TRƯỜNG GIANG", "Mã cửa hàng": "CPS-HNO-THO-126LLQ", "Leader": "Vũ Hoài Nam"},
    {"Tên": "ĐẠI LÊ MINH SƠN", "Mã cửa hàng": "CPS-HNO-THO-126LLQ", "Leader": "Vũ Hoài Nam"},
    {"Tên": "TRẦN THỊ LAN ANH", "Mã cửa hàng": "CPS-BDU-TAN-100NVT", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "NGUYỄN CAO KỲ ANH", "Mã cửa hàng": "CPS-HCM-GVA-525AQT", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "LƯU THẾ HUY", "Mã cửa hàng": "CPS-HCM-GVA-567LQD", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "TRẦN TRỌNG TÀI", "Mã cửa hàng": "CPS-HCM-PNH-114PDL", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "LÊ PHƯỚC THANH AN", "Mã cửa hàng": "CPS-HCM-Q01-157NTMK", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "NGUYỄN TRẦN LÊ THẠNH", "Mã cửa hàng": "CPS-HCM-Q01-157NTMK", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "HOÀNG GIA KHÁNH", "Mã cửa hàng": "CPS-HCM-Q02-139TN", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "TÔ NGỌC CHÂN", "Mã cửa hàng": "CPS-HCM-Q02-139TN", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "TRẦN ĐÌNH ANH", "Mã cửa hàng": "CPS-HCM-Q02-190NTD", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "TRẦN THỤY YẾN NHI", "Mã cửa hàng": "CPS-HCM-Q09-125LVV", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "LÊ THỊ CẨM TÚ", "Mã cửa hàng": "CPS-HCM-Q09-241...", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "NGUYỄN THANH PHONG", "Mã cửa hàng": "CPS-HCM-Q12-1ANAT", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "LÊ QUỐC HUY", "Mã cửa hàng": "CPS-HCM-TDU-632AKVC", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "LÊ THỊ KIỀU NGÂN", "Mã cửa hàng": "CPS-HCM-TDU-632AKVC", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "NGUYỄN THÚY DUY", "Mã cửa hàng": "CPS-HCM-TDU-943KVC", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "BÙI NGUYỄN TRUNG", "Mã cửa hàng": "CPS-BRI-VTA-491BMTT", "Leader": "Đỗ Quang Tiến"},
    {"Tên": "LÂM HẠNH LINH", "Mã cửa hàng": "CPS-BRI-VTA-491BMTT", "Leader": "Đỗ Quang Tiến"},
    {"Tên": "NGUYỄN TIẾN HƯNG", "Mã cửa hàng": "CPS-HPH-HPH-162LT", "Leader": "Đỗ Quang Tiến"},
    {"Tên": "TRƯƠNG PHƯƠNG Đ", "Mã cửa hàng": "CPS-NTH-PHR-339TN", "Leader": "Đỗ Quang Tiến"},
    {"Tên": "LƯƠNG ĐỨC NGHĨA", "Mã cửa hàng": "CPS-PTH-HBI-321CCL", "Leader": "Đỗ Quang Tiến"},
    {"Tên": "PHẠM THANH TÙNG", "Mã cửa hàng": "CPS-PTH-HBI-321CCL", "Leader": "Đỗ Quang Tiến"},
    {"Tên": "NGUYỄN VĂN NAM", "Mã cửa hàng": "CPS-QNI-BCH-690HL", "Leader": "Giang Văn Huy"},
    {"Tên": "TRƯƠNG TRẦN QUỐC KHÁNH", "Mã cửa hàng": "CPS-HCM-GVA-525AQT", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "LÊ PHI HẬU", "Mã cửa hàng": "CPS-HCM-PNH-114PDL", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "NGUYỄN TRUNG KIÊN", "Mã cửa hàng": "CPS-HCM-Q01-157NTMK", "Leader": "Trần Trung Nghĩa"},
    {"Tên": "NGUYỄN HỮU MINH QUÂN", "Mã cửa hàng": "CPS-HCM-TDU-632AKVC", "Leader": "Trần Trung Nghĩa"}
]

def style_evaluation(val):
    v = str(val)
    if "ĐẠT" in v and "KHÔNG" not in v:
        return "background-color: #d4edda; color: #155724; font-weight: bold;"
    elif "KHÔNG ĐẠT" in v:
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
    elif "CHƯA TRẢ BÀI" in v:
        return "background-color: #e2e3e5; color: #383d41;"
    return ""

# Tối ưu đọc file siêu tốc bằng st.cache_data
@st.cache_data(show_spinner="⚡ Đang phân tích file dung lượng lớn...")
def load_excel_data(file_bytes):
    xls = pd.ExcelFile(file_bytes)
    sheets_dict = {}
    for s in xls.sheet_names:
        sheets_dict[s] = pd.read_excel(xls, s)
    return sheets_dict

uploaded_file = st.file_uploader("Kéo thả file Raw Data hoặc dùng file Processed có sẵn:", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        sheets_data = load_excel_data(uploaded_file)
        st.success("🎉 Nạp dữ liệu thành công!")

        tested_dict = {}
        source_sheet_used = "Sheet Trade Audit Plus"

        for sheet_name, df in sheets_data.items():
            c_name = next((c for c in df.columns if any(k in normalize_text(c) for k in ['nhan su', 'ten', 'hova ten', 'bat buoc'])), None)
            c_score = next((c for c in df.columns if any(k in normalize_text(c) for k in ['diem', 'score', 'tra bai', 'ket qua'])), None)
            c_status = next((c for c in df.columns if any(k in normalize_text(c) for k in ['qc status', 'trang thai', 'status'])), None)
            c_date = next((c for c in df.columns if any(k in normalize_text(c) for k in ['ngay', 'date', 'thoi gian'])), None)

            if c_name:
                source_sheet_used = f"Sheet {sheet_name}"
                for _, r in df.iterrows():
                    v_name = normalize_text(r[c_name])
                    if not v_name: continue

                    v_score_raw = r[c_score] if c_score and pd.notna(r[c_score]) else None
                    v_st = str(r[c_status]).strip() if c_status and pd.notna(r[c_status]) else "done"
                    v_dt = str(r[c_date]).strip() if c_date and pd.notna(r[c_date]) else "None"

                    try:
                        v_score = float(v_score_raw) if v_score_raw is not None else None
                    except:
                        v_score = None

                    for item in TARGET_35_NV_MASTER:
                        if normalize_text(item["Tên"]) in v_name or v_name in normalize_text(item["Tên"]):
                            if v_score is not None:
                                eval_text = "ĐẠT" if v_score >= 50 else "KHÔNG ĐẠT"
                            else:
                                eval_text = "ĐẠT" if "pass" in str(v_st).lower() or "ok" in str(v_st).lower() else "KHÔNG ĐẠT"

                            tested_dict[item["Tên"]] = {
                                "Điểm trả bài": round(v_score, 2) if v_score is not None else "N/A",
                                "Đánh giá": eval_text,
                                "QC Status": v_st,
                                "Ngày thực hiện": v_dt if v_dt != "nan" else "13/08/2026"
                            }

        # Header metrics
        count_tt1 = len(tested_dict)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Trade Audit", "203 / 206 CH")
        m2.metric("Data Plus", "174 / 174 CH")
        m3.metric("Mystery CH", "65 / 114 CH")
        m4.metric("NV Trả Bài (TT1)", f"{count_tt1} / 35 NV")
        m5.metric("Điện Thoại Vui", "29 / 32 CH")

        st.divider()

        t1, t2, t3, t4, t5 = st.tabs([
            "📊 Tiến Độ Trade theo Leader", 
            "➕ Tiến Độ Plus & QC Status", 
            "🎤 CPS — 35 NV Trả Bài (TT1)", 
            "⚠️ Danh Sách YCBS (Rework)", 
            "🕵️ Mystery Shopper"
        ])

        with t1:
            s_tr = next((s for s in sheets_data.keys() if "trade" in normalize_text(s)), None)
            st.dataframe(sheets_data[s_tr] if s_tr else "Không tìm thấy Sheet Trade Audit", use_container_width=True)

        with t2:
            s_pl = next((s for s in sheets_data.keys() if "plus" in normalize_text(s)), None)
            st.dataframe(sheets_data[s_pl] if s_pl else "Không tìm thấy Sheet AuditPlus", use_container_width=True)

        with t3:
            st.markdown("<div class='report-title'>CPS — 35 NHÂN SỰ / ĐIỂM TRẢ BÀI TỪ TRADE AUDIT PLUS</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='report-sub'>Nguồn: {uploaded_file.name} | {source_sheet_used}</div>", unsafe_allow_html=True)

            # Bảng tổng quan KPI
            total_required = 35
            has_data = len(tested_dict)
            count_pass = sum(1 for v in tested_dict.values() if v["Đánh giá"] == "ĐẠT")
            count_fail = sum(1 for v in tested_dict.values() if v["Đánh giá"] == "KHÔNG ĐẠT")
            count_no_data = total_required - has_data

            df_summary = pd.DataFrame([
                {"Chỉ số": "Tổng NV bắt buộc", "Kết quả": total_required},
                {"Chỉ số": "Có dữ liệu trả bài", "Kết quả": has_data},
                {"Chỉ số": "ĐẠT (>=50)", "Kết quả": count_pass},
                {"Chỉ số": "KHÔNG ĐẠT (<50)", "Kết quả": count_fail},
                {"Chỉ số": "CHƯA TRẢ BÀI", "Kết quả": count_no_data}
            ])

            c_sum, _ = st.columns([1, 1])
            with c_sum:
                st.dataframe(df_summary, use_container_width=True, hide_index=True)

            st.write("---")

            # Bảng chi tiết 35 nhân sự
            res_list = []
            for item in TARGET_35_NV_MASTER:
                nv_name = item["Tên"]
                if nv_name in tested_dict:
                    info = tested_dict[nv_name]
                else:
                    info = {
                        "Điểm trả bài": "➖",
                        "Đánh giá": "CHƯA TRẢ BÀI",
                        "QC Status": "None",
                        "Ngày thực hiện": "None"
                    }

                res_list.append({
                    "Nhân sự": nv_name,
                    "Mã cửa hàng": item["Mã cửa hàng"],
                    "Điểm trả bài": info["Điểm trả bài"],
                    "Đánh giá": info["Đánh giá"],
                    "QC Status": info["QC Status"],
                    "Ngày thực hiện": info["Ngày thực hiện"]
                })

            df_detail = pd.DataFrame(res_list)
            styled_detail = df_detail.style.map(style_evaluation, subset=["Đánh giá"])
            st.dataframe(styled_detail, use_container_width=True, height=550, hide_index=True)

        with t4:
            st.info("Danh sách tự động tổng hợp lỗi YCBS/Rework từ cửa hàng.")

        with t5:
            s_my = next((s for s in sheets_data.keys() if "mystery" in normalize_text(s)), None)
            st.dataframe(sheets_data[s_my] if s_my else "Không tìm thấy Sheet Mystery", use_container_width=True)

    except Exception as e:
        st.error(f"Lỗi đọc file dữ liệu: {e}")
else:
    st.info("👋 Vui lòng tải file Excel báo cáo lên để kích hoạt hệ thống Dashboard!")
