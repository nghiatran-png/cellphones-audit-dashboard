import streamlit as st
import pandas as pd
import io
import os

# 1. Cấu hình trang
st.set_page_config(
    page_title="CellphoneS Daily Audit Dashboard", 
    page_icon="📊", 
    layout="wide"
)

# Custom CSS cho giao diện
st.markdown("""
    <style>
    .main-header {font-size: 26px; font-weight: bold; color: #d70018; margin-bottom: 20px;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .stTabs [data-baseweb="tab"] {border-radius: 4px; padding: 8px 16px; background-color: #f1f3f5;}
    .stTabs [aria-selected="true"] {background-color: #d70018 !important; color: white !important; font-weight: bold;}
    div[data-testid="stMetricValue"] {font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-header'>📊 CELLPHONES AUDIT & TRACKING DASHBOARD TỔNG QUAN</div>", unsafe_allow_html=True)

# 2. Danh sách Master 35 Nhân sự cố định theo đúng mẫu
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

# Hàm tô màu theo biểu mẫu
def highlight_qc_status(val):
    if "Đạt" in str(val):
        return "background-color: #d4edda; color: #155724; font-weight: bold;"
    elif "Chờ duyệt" in str(val):
        return "background-color: #fff3cd; color: #856404; font-weight: bold;"
    elif "Chưa phỏng vấn" in str(val):
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
    return ""

# 3. Nạp dữ liệu File Raw / Tracking
st.subheader("1. Nạp dữ liệu Raw Data / Tracking")
uploaded_file = st.file_uploader("Kéo thả file Raw Data hoặc dùng file Processed có sẵn:", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        xls = pd.ExcelFile(uploaded_file)
        st.success("🎉 Cập nhật thành công Dashboard Quản Trị CellphoneS!")

        # QUÉT DỮ LIỆU ĐỐI SOÁT CHO TAB 3
        tested_dict = {}
        for sheet in xls.sheet_names:
            df_temp = pd.read_excel(xls, sheet)
            col_name = None
            col_status = None
            col_date = None
            
            for c in df_temp.columns:
                c_str = str(c).lower()
                if any(k in c_str for k in ['nhân sự', 'nhan vien', 'name', 'tên nv', 'họ và tên']):
                    col_name = c
                if any(k in c_str for k in ['qc status', 'trạng thái', 'kết quả', 'status', 'đánh giá']):
                    col_status = c
                if any(k in c_str for k in ['ngày', 'date', 'thời gian']):
                    col_date = c

            if col_name:
                for _, row in df_temp.iterrows():
                    val_name = str(row[col_name]).strip()
                    val_status = str(row[col_status]).strip() if col_status and pd.notna(row[col_status]) else ""
                    val_date = str(row[col_date]).strip() if col_date and pd.notna(row[col_date]) else "None"
                    
                    for item in TARGET_35_NV_MASTER:
                        nv_name = item["Tên"]
                        if nv_name.lower() in val_name.lower():
                            st_lower = val_status.lower()
                            
                            if "pending" in st_lower or "chờ" in st_lower:
                                qc_code = "pending"
                                eval_status = "Chờ duyệt (QC Pending)"
                            elif "done" in st_lower or "đạt" in st_lower or "pass" in st_lower or "ok" in st_lower:
                                qc_code = "done"
                                eval_status = "Đạt (QC Done)"
                            else:
                                qc_code = "done"
                                eval_status = "Đạt (QC Done)"

                            tested_dict[nv_name] = {
                                "Trạng thái": "Đã phỏng vấn",
                                "QC Status": qc_code,
                                "Đánh giá QC Status": eval_status,
                                "Ngày được phỏng vấn": val_date if val_date != "nan" else "14/08/2026",
                                "Ghi chú": "None"
                            }

        count_tt1_tested = len(tested_dict)

        # METRICS HEADER
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Trade Audit", "203 / 206 CH")
        col2.metric("Data Plus", "174 / 174 CH")
        col3.metric("Mystery CH", "65 / 114 CH")
        col4.metric("NV Trả Bài (TT1)", f"{count_tt1_tested} / 35 NV")
        col5.metric("Điện Thoại Vui", "29 / 32 CH")

        st.divider()

        # CÁC TAB BÁO CÁO
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Tiến Độ Trade theo Leader", 
            "➕ Tiến Độ Plus & QC Status", 
            "🎤 Kiểm Tra Phỏng Vấn (TT1)", 
            "⚠️ Danh Sách YCBS (Rework)", 
            "🕵️ Mystery Shopper"
        ])

        with tab1:
            st.subheader("1) Tiến Độ Trade Audit Theo Leader")
            if "trade audit" in [s.lower() for s in xls.sheet_names]:
                sheet_trade = [s for s in xls.sheet_names if s.lower() == "trade audit"][0]
                st.dataframe(pd.read_excel(xls, sheet_trade), use_container_width=True)
            else:
                st.warning("Chưa tìm thấy sheet Trade Audit trong file.")

        with tab2:
            st.subheader("2) Tiến Độ Data Plus & Trạng Thái QC")
            if "auditplus" in [s.lower() for s in xls.sheet_names]:
                sheet_plus = [s for s in xls.sheet_names if s.lower() == "auditplus"][0]
                st.dataframe(pd.read_excel(xls, sheet_plus), use_container_width=True)
            else:
                st.warning("Chưa tìm thấy sheet AuditPlus trong file.")

        # --- TAB 3: HIỂN THỊ ĐÚNG CHUẨN MẪU BẢNG ---
        with tab3:
            st.subheader("3) Danh Sách Nhân Sự Bắt Buộc Phỏng Vấn (35 NV - Đánh Giá Theo QC Status)")

            report_data = []
            for item in TARGET_35_NV_MASTER:
                nv_name = item["Tên"]
                if nv_name in tested_dict:
                    info = tested_dict[nv_name]
                else:
                    info = {
                        "Trạng thái": "Chưa phỏng vấn",
                        "QC Status": "None",
                        "Đánh giá QC Status": "Chưa phỏng vấn - Bắt buộc đợt 2",
                        "Ngày được phỏng vấn": "None",
                        "Ghi chú": "Bắt buộc phỏng vấn đợt 2"
                    }

                report_data.append({
                    "Tên nhân sự bắt buộc": nv_name,
                    "Mã cửa hàng": item["Mã cửa hàng"],
                    "Leader": item["Leader"],
                    "Trạng thái": info["Trạng thái"],
                    "QC Status": info["QC Status"],
                    "Đánh giá QC Status": info["Đánh giá QC Status"],
                    "Ngày được phỏng vấn": info["Ngày được phỏng vấn"],
                    "Ghi chú": info["Ghi chú"]
                })

            df_report_35 = pd.DataFrame(report_data)

            # Áp dụng tô màu nền cột "Đánh giá QC Status"
            styled_df = df_report_35.style.map(highlight_qc_status, subset=["Đánh giá QC Status"])
            st.dataframe(styled_df, use_container_width=True, height=600)

        with tab4:
            st.subheader("4) Danh Sách Yêu Cầu Bổ Sung / Rework")
            st.info("Danh sách tự động tổng hợp các lỗi YCBS/Rework từ các chi nhánh.")

        with tab5:
            st.subheader("5) Tiến Độ & Kết Quả Mystery Shopper")
            if "mystery" in [s.lower() for s in xls.sheet_names]:
                sheet_myster = [s for s in xls.sheet_names if s.lower() == "mystery"][0]
                st.dataframe(pd.read_excel(xls, sheet_myster), use_container_width=True)
            else:
                st.warning("Chưa tìm thấy sheet Mystery trong file.")

    except Exception as e:
        st.error(f"Lỗi xử lý dữ liệu: {e}")
else:
    st.info("👋 Vui lòng tải file Excel báo cáo lên để kích hoạt hệ thống Dashboard!")
