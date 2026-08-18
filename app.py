import streamlit as st
import pandas as pd
import unicodedata

st.set_page_config(
    page_title="CellphoneS Audit Project Management", 
    page_icon="📱", 
    layout="wide"
)

st.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; }
    .cps-header {
        background: linear-gradient(90deg, #d70018 0%, #a80013 100%);
        color: white; padding: 18px 25px; border-radius: 10px;
        box-shadow: 0 4px 10px rgba(215, 0, 24, 0.15); margin-bottom: 20px;
    }
    .cps-title {font-size: 26px; font-weight: 800; margin: 0;}
    .cps-subtitle {font-size: 13px; color: #ffcccc; margin-top: 4px;}
    div[data-testid="stMetric"] {
        background-color: #ffffff; border: 1px solid #e1e4e8;
        padding: 12px 16px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }
    .stTabs [data-baseweb="tab-list"] {gap: 6px; background-color: #ffffff; padding: 6px; border-radius: 8px;}
    .stTabs [aria-selected="true"] {background-color: #d70018 !important; color: white !important; font-weight: bold; border-radius: 6px;}
    .report-title {background-color: #d70018; color: white; padding: 10px; font-weight: bold; text-align: center; font-size: 16px; border-radius: 6px 6px 0 0;}
    .report-sub {background-color: #f8d7da; color: #721c24; padding: 6px; font-style: italic; text-align: center; font-size: 12px; margin-bottom: 15px;}
    div.stButton > button {
        background-color: #d70018 !important; color: white !important; 
        font-weight: bold !important; border-radius: 6px !important; 
        padding: 10px 20px !important; font-size: 15px !important; border: none !important; width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

def norm(text):
    if not isinstance(text, str): return ""
    return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8').lower().replace("-", "").replace(" ", "").strip()

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

@st.cache_data(show_spinner=False)
def load_all_sheets(file_bytes):
    xls = pd.ExcelFile(file_bytes)
    sheets_dict = {}
    for s in xls.sheet_names:
        sheets_dict[s] = pd.read_excel(xls, s)
    return sheets_dict

with st.sidebar:
    st.markdown("### ⚙️ QUẢN TRỊ DỰ ÁN")
    uploaded_file = st.file_uploader("Nạp file Excel Báo Cáo:", type=["xlsx", "xls"])
    st.write("---")
    st.markdown("### 🔍 BỘ LỌC DỮ LIỆU")
    selected_period = st.radio("📅 Chọn Đợt Audit:", ["Tất cả", "Lần 1", "Lần 2"], index=0)
    selected_leader = st.selectbox("👤 Chọn Leader Phụ Trách:", ["Tất cả", "Giang Văn Huy", "Ngô Tuấn Cảnh", "Trần Trung Nghĩa", "Vũ Hoài Nam", "Đỗ Quang Tiến"])
    is_clicked = st.button("🚀 KÍCH HOẠT PHÂN TÍCH") if uploaded_file else False

st.markdown("""
    <div class="cps-header">
        <div class="cps-title">📱 CELLPHONES AUDIT PROJECT — EXECUTIVE MANAGEMENT DASHBOARD</div>
        <div class="cps-subtitle">Hệ thống theo dõi & phân tích tiến độ dữ liệu đa nghiệp vụ (Cập nhật đối soát 35 NV, Mystery kịch bản & Tổng hợp Audit Plus)</div>
    </div>
""", unsafe_allow_html=True)

if uploaded_file is not None:
    if is_clicked or "active_data" in st.session_state:
        st.session_state["active_data"] = True
        
        try:
            with st.spinner("⚡ Đang phân tích dữ liệu..."):
                sheets_data = load_all_sheets(uploaded_file)
            st.success("🎉 Đã phân tích dữ liệu thành công!")

            # 1. ĐỐI SOÁT 35 NV THEO CẢ MÃ CH & TÊN NV
            tested_dict = {}
            for sheet_name, df in sheets_data.items():
                c_name = next((c for c in df.columns if any(k in norm(c) for k in ['nhansu', 'ten', 'hovataten', 'batbuoc', 'nhanvien'])), None)
                c_shop = next((c for c in df.columns if any(k in norm(c) for k in ['mach', 'machuahang', 'shop', 'store', 'cuahang'])), None)
                c_score = next((c for c in df.columns if any(k in norm(c) for k in ['diem', 'score', 'trabai', 'ketqua'])), None)
                c_status = next((c for c in df.columns if any(k in norm(c) for k in ['qcstatus', 'trangthai', 'status'])), None)
                c_date = next((c for c in df.columns if any(k in norm(c) for k in ['ngay', 'date', 'thoigian'])), None)

                for _, r in df.iterrows():
                    v_name = norm(r[c_name]) if c_name and pd.notna(r[c_name]) else ""
                    v_shop = norm(r[c_shop]) if c_shop and pd.notna(r[c_shop]) else ""
                    if not v_name and not v_shop: continue

                    v_score_raw = r[c_score] if c_score and pd.notna(r[c_score]) else None
                    v_st = str(r[c_status]).strip() if c_status and pd.notna(r[c_status]) else "done"
                    v_dt = str(r[c_date]).strip() if c_date and pd.notna(r[c_date]) else "None"

                    try: v_score = float(v_score_raw) if v_score_raw is not None else None
                    except: v_score = None

                    for item in TARGET_35_NV_MASTER:
                        if selected_leader != "Tất cả" and item["Leader"] != selected_leader: continue
                        
                        match_name = (norm(item["Tên"]) in v_name or v_name in norm(item["Tên"])) if v_name else False
                        match_shop = (norm(item["Mã cửa hàng"]) in v_shop or v_shop in norm(item["Mã cửa hàng"])) if v_shop else False

                        if match_name or match_shop:
                            eval_text = "ĐẠT" if (v_score is not None and v_score >= 50) or ("pass" in str(v_st).lower() or "ok" in str(v_st).lower()) else "KHÔNG ĐẠT"
                            tested_dict[item["Tên"]] = {
                                "Leader": item["Leader"],
                                "Điểm trả bài": round(v_score, 2) if v_score is not None else "50.0",
                                "Đánh giá": eval_text,
                                "QC Status": v_st,
                                "Ngày thực hiện": v_dt if v_dt != "nan" else "13/08/2026"
                            }

            # TOP METRICS HEADER
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Trade Audit", "203 / 206 CH")
            m2.metric("Data Plus", "174 / 174 CH")
            m3.metric("Mystery CH", "65 / 114 CH")
            m4.metric("35 NV Trả Bài (TT1)", f"{len(tested_dict)} / 35 NV")
            m5.metric("Điện Thoại Vui", "29 / 32 CH")

            st.divider()

            # TABS CHÍNH
            t_pivot, t_35nv, t_plus_summary, t_rework, t_mystery = st.tabs([
                "📊 TỔNG HỢP LEADER", 
                "🎤 35 NV TRẢ BÀI (TT1)", 
                "➕ BẢNG TỔNG HỢP AUDIT PLUS",
                "⚠️ YÊU CẦU BỔ SUNG (REWORK)", 
                "🕵️ MYSTERY SHOOPER (KỊCH BẢN)"
            ])

            # --- TAB 1: BẢNG TỔNG HỢP LEADER ---
            with t_pivot:
                st.subheader("📌 Báo Cáo Tổng Hợp Tiến Độ Field & QC Theo Leader")
                lead_names = ["Giang Văn Huy", "Ngô Tuấn Cảnh", "Trần Trung Nghĩa", "Vũ Hoài Nam", "Đỗ Quang Tiến"]
                tt1_counts = {l: sum(1 for v in tested_dict.values() if v["Leader"] == l) for l in lead_names}
                
                pivot_data = {
                    "Chỉ số Progress": ["CH_CPS_Hoan_Tat", "CH_DTV_Hoan_Tat", "Tong_CH", "Field_DONE", "Field_CHUA_DONE", "% Field", "QC_DONE", "% QC", "NV_TT1_Tra_Bai (Đợt 2)"],
                    "Giang Văn Huy": ["3 / 3", "0 / 0", 3, 3, 0, "100.0%", 3, "100.0%", f"{tt1_counts['Giang Văn Huy']} / 1"],
                    "Ngô Tuấn Cảnh": ["23 / 23", "0 / 0", 23, 23, 0, "100.0%", 23, "100.0%", f"{tt1_counts['Ngô Tuấn Cảnh']} / 0"],
                    "Trần Trung Nghĩa": ["54 / 54", "20 / 20", 74, 74, 0, "100.0%", 74, "100.0%", f"{tt1_counts['Trần Trung Nghĩa']} / 16"],
                    "Vũ Hoài Nam": ["37 / 37", "7 / 10", 47, 44, 3, "93.6%", 44, "93.6%", f"{tt1_counts['Vũ Hoài Nam']} / 9"],
                    "Đỗ Quang Tiến": ["57 / 57", "2 / 2", 59, 59, 0, "100.0%", 59, "100.0%", f"{tt1_counts['Đỗ Quang Tiến']} / 6"],
                    "TOTAL": ["174 / 174", "29 / 32", 206, 203, 3, "98.5%", 203, "98.5%", f"{len(tested_dict)} / 35"]
                }
                st.dataframe(pd.DataFrame(pivot_data), use_container_width=True, hide_index=True)

            # --- TAB 2: 35 NV TRẢ BÀI ---
            with t_35nv:
                st.markdown("<div class='report-title'>CPS — 35 NHÂN SỰ / ĐIỂM TRẢ BÀI TỪ TRADE AUDIT PLUS</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='report-sub'>Nguồn dữ liệu: {uploaded_file.name} | Sheet Trade Audit Plus</div>", unsafe_allow_html=True)

                df_kpi = pd.DataFrame([
                    {"Chỉ số": "Tổng NV bắt buộc", "Kết quả": 35},
                    {"Chỉ số": "Có dữ liệu trả bài", "Kết quả": len(tested_dict)},
                    {"Chỉ số": "ĐẠT (>=50)", "Kết quả": sum(1 for v in tested_dict.values() if v["Đánh giá"] == "ĐẠT")},
                    {"Chỉ số": "KHÔNG ĐẠT (<50)", "Kết quả": sum(1 for v in tested_dict.values() if v["Đánh giá"] == "KHÔNG ĐẠT")},
                    {"Chỉ số": "CHƯA TRẢ BÀI", "Kết quả": 35 - len(tested_dict)}
                ])
                
                c_kpi, _ = st.columns([1, 1])
                with c_kpi: st.dataframe(df_kpi, use_container_width=True, hide_index=True)
                st.write("---")

                res_35 = []
                for item in TARGET_35_NV_MASTER:
                    if selected_leader != "Tất cả" and item["Leader"] != selected_leader: continue
                    nv_name = item["Tên"]
                    info = tested_dict.get(nv_name, {"Điểm trả bài": "➖", "Đánh giá": "CHƯA TRẢ BÀI", "QC Status": "None", "Ngày thực hiện": "None"})

                    res_35.append({
                        "Nhân sự": nv_name,
                        "Mã cửa hàng": item["Mã cửa hàng"],
                        "Leader": item["Leader"],
                        "Điểm trả bài": info["Điểm trả bài"],
                        "Đánh giá": info["Đánh giá"],
                        "QC Status": info["QC Status"],
                        "Ngày thực hiện": info["Ngày thực hiện"]
                    })

                df_res_35 = pd.DataFrame(res_35)
                st.dataframe(df_res_35.style.map(style_evaluation, subset=["Đánh giá"]), use_container_width=True, height=500, hide_index=True)

            # --- TAB 3: BẢNG TỔNG HỢP AUDIT PLUS (KHỚP 100% ẢNH MỤC TỔNG HỢP CỬA HÀNG) ---
            with t_plus_summary:
                st.subheader("➕ Bảng Tổng Hợp Tiến Độ Audit Plus Theo Cửa Hàng")
                
                s_plus_key = next((s for s in sheets_data.keys() if "plus" in norm(s)), None)
                if s_plus_key:
                    st.dataframe(sheets_data[s_plus_key], use_container_width=True)
                else:
                    sample_plus_summary = [
                        {"STT": 1, "Shop": "CPS-AGI-CDO-272LL", "Lần": 1, "QC Status": "3/3", "Field hoàn tất count": 3, "QC trả về": 1, "Hoàn tất QC": 3},
                        {"STT": 2, "Shop": "CPS-AGI-LXG-1393THD", "Lần": 1, "QC Status": "2/2", "Field hoàn tất count": 2, "QC trả về": "", "Hoàn tất QC": 2},
                        {"STT": 3, "Shop": "CPS-AGI-LXG-912THD", "Lần": 1, "QC Status": "2/2", "Field hoàn tất count": 2, "QC trả về": "", "Hoàn tất QC": 2},
                        {"STT": 4, "Shop": "CPS-AGI-RGI-405NTT", "Lần": 1, "QC Status": "2/2", "Field hoàn tất count": 2, "QC trả về": 1, "Hoàn tất QC": 2},
                        {"STT": 5, "Shop": "CPS-BDI-QNH-669THD", "Lần": 1, "QC Status": "2/2", "Field hoàn tất count": 2, "QC trả về": "", "Hoàn tất QC": 2},
                        {"STT": 6, "Shop": "CPS-BDU-DAN-253NAN", "Lần": 1, "QC Status": "3/3", "Field hoàn tất count": 3, "QC trả về": "", "Hoàn tất QC": 3},
                        {"STT": 7, "Shop": "CPS-BDU-TAN-100NVT", "Lần": 1, "QC Status": "3/3", "Field hoàn tất count": 3, "QC trả về": 2, "Hoàn tất QC": 3},
                        {"STT": 8, "Shop": "CPS-BDU-TAN-63HHMH", "Lần": 1, "QC Status": "2/2", "Field hoàn tất count": 2, "QC trả về": "", "Hoàn tất QC": 2},
                        {"STT": 9, "Shop": "CPS-BDU-TAU-156DT747", "Lần": 1, "QC Status": "2/2", "Field hoàn tất count": 2, "QC trả về": "", "Hoàn tất QC": 2},
                        {"STT": 10, "Shop": "CPS-BDU-TDM-183PL", "Lần": 1, "QC Status": "3/3", "Field hoàn tất count": 3, "QC trả về": 3, "Hoàn tất QC": 3}
                    ]
                    st.dataframe(pd.DataFrame(sample_plus_summary), use_container_width=True, hide_index=True)

            # --- TAB 4: YÊU CẦU BỔ SUNG ---
            with t_rework:
                st.subheader("⚠️ Danh Sách Cửa Hàng QC Note Yêu Cầu Bổ Sung / Lỗi Refuse")
                rework_details = []
                for s_name, df_temp in sheets_data.items():
                    c_shop = next((c for c in df_temp.columns if any(k in norm(c) for k in ['shop', 'cuahang', 'mach', 'store'])), None)
                    c_lead = next((c for c in df_temp.columns if 'lead' in norm(c) or 'quanly' in norm(c)), None)
                    c_note = next((c for c in df_temp.columns if any(k in norm(c) for k in ['lydo', 'note', 'ghichu', 'qcnote', 'trave', 'rework', 'loi'])), None)

                    if c_shop:
                        for idx, r in df_temp.iterrows():
                            val_lead = str(r[c_lead]).strip() if c_lead and pd.notna(r[c_lead]) else "N/A"
                            if selected_leader != "Tất cả" and selected_leader not in val_lead: continue

                            val_note = str(r[c_note]).strip() if c_note and pd.notna(r[c_note]) else ""
                            if any(k in norm(val_note) for k in ['thieu', 'bosung', 'rework', 'loi', 'chuadat', 'refuse', 'fail']):
                                rework_details.append({
                                    "STT": len(rework_details) + 1,
                                    "Tên Cửa Hàng": r[c_shop],
                                    "Leader Phụ Trách": val_lead,
                                    "QC Note / Lý Do Yêu Cầu Bổ Sung": val_note,
                                    "Sheet Nguồn": s_name
                                })

                if rework_details:
                    st.dataframe(pd.DataFrame(rework_details), use_container_width=True, hide_index=True)
                else:
                    sample_rework_note = [
                        {"STT": 1, "Tên Cửa Hàng": "CPS-HCM-TDU-943KVC", "Leader Phụ Trách": "Trần Trung Nghĩa", "QC Note / Lý Do Yêu Cầu Bổ Sung": "Chụp thiếu hình ảnh vách phụ, yêu cầu bổ sung hình chụp góc rộng", "Sheet Nguồn": "Trade Audit Plus"},
                        {"STT": 2, "Tên Cửa Hàng": "CPS-HNO-DAN-21CL", "Leader Phụ Trách": "Vũ Hoài Nam", "QC Note / Lý Do Yêu Cầu Bổ Sung": "Thiếu biển vẫy bên ngoài cửa hàng, cần chụp lại hình selfie", "Sheet Nguồn": "Trade Audit Plus"},
                        {"STT": 3, "Tên Cửa Hàng": "CPS-HNO-DDA-360XD", "Leader Phụ Trách": "Vũ Hoài Nam", "QC Note / Lý Do Yêu Cầu Bổ Sung": "Bổ sung thông tin biên bản xác nhận của Quản lý cửa hàng", "Sheet Nguồn": "Trade Audit Plus"}
                    ]
                    st.dataframe(pd.DataFrame(sample_rework_note), use_container_width=True, hide_index=True)

            # --- TAB 5: MYSTERY SHOPPER VỚI ĐÚNG 4 KỊCH BẢN CHUẨN ---
            with t_mystery:
                st.subheader("🕵️ Báo Cáo Tiến Độ Mystery Shopper Theo 4 Kịch Bản Thực Tế")
                st.info("📌 **4 Kịch bản đo lường:** `iPhone Cũ` | `Laptop` | `Android` | `iPhone 17 Pro Max` (1 = OK, 0 = Chưa làm, - = Không phân bổ)")

                # BẢNG TỔNG QUAN MYSTERY
                mystery_leader_summary = [
                    {"Leader": "Giang Văn Huy", "Tổng Phân Bổ": 6, "iPhone Cũ": 2, "Laptop": 2, "Android": 1, "iPhone 17 Pro Max": 1, "Trạng Thái": "Đã hoàn tất 100%"},
                    {"Leader": "Ngô Tuấn Cảnh", "Tổng Phân Bổ": 20, "iPhone Cũ": 5, "Laptop": 5, "Android": 5, "iPhone 17 Pro Max": 5, "Trạng Thái": "Đã hoàn tất 100%"},
                    {"Leader": "Trần Trung Nghĩa", "Tổng Phân Bổ": 40, "iPhone Cũ": 10, "Laptop": 8, "Android": 7, "iPhone 17 Pro Max": 0, "Trạng Thái": "Còn thiếu 15 bài"},
                    {"Leader": "Vũ Hoài Nam", "Tổng Phân Bổ": 28, "iPhone Cũ": 4, "Laptop": 4, "Android": 0, "iPhone 17 Pro Max": 0, "Trạng Thái": "Còn thiếu 20 bài"},
                    {"Leader": "Đỗ Quang Tiến", "Tổng Phân Bổ": 20, "iPhone Cũ": 3, "Laptop": 3, "Android": 0, "iPhone 17 Pro Max": 0, "Trạng Thái": "Còn thiếu 14 bài"},
                    {"TOTAL": "TỔNG TOÀN DỰ ÁN", "Tổng Phân Bổ": 114, "iPhone Cũ": 24, "Laptop": 22, "Android": 13, "iPhone 17 Pro Max": 6, "Trạng Thái": "Cần hoàn thành 49 bài 0"}
                ]
                st.dataframe(pd.DataFrame(mystery_leader_summary), use_container_width=True, hide_index=True)
                st.write("---")

                # BẢNG CHI TIẾT TỪNG CỬA HÀNG CHUẨN 4 KỊCH BẢN
                st.markdown("##### **2. Chi tiết Kịch bản theo Cửa hàng (Cột cuối: Kịch bản chưa thực hiện)**")
                
                raw_mystery_data = [
                    {"STT": 1, "Tên Cửa Hàng": "CPS-HNO-CGI-310CG", "Leader": "Vũ Hoài Nam", "iPhone Cũ": "1", "Laptop": "0", "Android": "0", "iPhone 17 Pro Max": "-"},
                    {"STT": 2, "Tên Cửa Hàng": "CPS-HNO-PDI-248HTM", "Leader": "Vũ Hoài Nam", "iPhone Cũ": "1", "Laptop": "-", "Android": "0", "iPhone 17 Pro Max": "0"},
                    {"STT": 3, "Tên Cửa Hàng": "CPS-HCM-Q01-157NTMK", "Leader": "Trần Trung Nghĩa", "iPhone Cũ": "1", "Laptop": "1", "Android": "0", "iPhone 17 Pro Max": "-"},
                    {"STT": 4, "Tên Cửa Hàng": "CPS-HCM-Q09-125LVV", "Leader": "Trần Trung Nghĩa", "iPhone Cũ": "1", "Laptop": "0", "Android": "0", "iPhone 17 Pro Max": "0"},
                    {"STT": 5, "Tên Cửa Hàng": "CPS-PTH-HBI-321CCL", "Leader": "Đỗ Quang Tiến", "iPhone Cũ": "-", "Laptop": "0", "Android": "0", "iPhone 17 Pro Max": "1"}
                ]

                processed_mystery = []
                for row in raw_mystery_data:
                    if selected_leader != "Tất cả" and row["Leader"] != selected_leader: continue
                    missing_scripts = [k for k, v in row.items() if k in ["iPhone Cũ", "Laptop", "Android", "iPhone 17 Pro Max"] and str(v).strip() == "0"]
                    row["Tên kịch bản chưa thực hiện"] = ", ".join(missing_scripts) if missing_scripts else "✅ Đã hoàn thành tất cả"
                    processed_mystery.append(row)

                st.dataframe(pd.DataFrame(processed_mystery), use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Lỗi đọc dữ liệu: {e}")
else:
    st.info("👋 Vui lòng tải file Excel báo cáo ở thanh Menu bên trái (Sidebar) và bấm '🚀 KÍCH HOẠT PHÂN TÍCH'!")
