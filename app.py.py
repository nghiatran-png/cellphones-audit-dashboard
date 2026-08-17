import streamlit as st
import pandas as pd
import io
import os
import unicodedata

# 1. Cấu hình trang
st.set_page_config(
    page_title="CellphoneS Daily Audit Dashboard", 
    page_icon="📊", 
    layout="wide"
)

# Thêm CSS tùy chỉnh giao diện
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

# 2. Nạp dữ liệu File Raw / Tracking
st.subheader("1. Nạp dữ liệu Raw Data / Tracking")
uploaded_file = st.file_uploader("Kéo thả file Raw Data hoặc dùng file Processed có sẵn:", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        xls = pd.ExcelFile(uploaded_file)
        st.success("🎉 Cập nhật thành công Dashboard Quản Trị CellphoneS!")
        
        # --- DANH SÁCH 35 NV BẮT BUỘC PHỎNG VẤN (TT1) ---
        target_35_nv = [
            "NGUYỄN CÔNG TUẤN ANH", "NGUYỄN HỮU THÀNH", "NGUYỄN PHƯƠNG THẢO", "LÊ VĂN THIÊN", "PHẠM DUY NAM",
            "NGUYỄN QUỐC TRƯỜNG", "VŨ QUANG HUY", "ĐỖ TRƯỜNG GIANG", "ĐẠI LÊ MINH SƠN", "TRẦN THỊ LAN ANH",
            "NGUYỄN CAO KỲ ANH", "LƯU THẾ HUY", "TRẦN TRỌNG TÀI", "LÊ PHƯỚC THANH AN", "NGUYỄN TRẦN LÊ THẢO",
            "HOÀNG GIA KHÁNH", "TÔ NGỌC CHÂN", "TRẦN ĐÌNH ANH", "TRẦN THỤY YẾN NHI", "LÊ THỊ CẨM TÚ",
            "NGUYỄN THANH PHONG", "LÊ QUỐC HUY", "LÊ THỊ KIỀU NGÂN", "NGUYỄN THÚY DUY", "BÙI NGUYỄN TRUNG ĐỨC",
            "LÂM HẠNH LINH", "NGUYỄN TIẾN HƯNG", "TRƯƠNG PHƯƠNG ĐÔNG", "LƯƠNG ĐỨC NGHĨA", "PHẠM THANH TÙNG",
            "NGUYỄN VĂN NAM", "TRƯƠNG TRẦN QUỐC HUY", "LÊ PHI HẬU", "NGUYỄN TRUNG KIÊN", "NGUYỄN HỮU MINH TRÍ"
        ]

        # QUÉT DỮ LIỆU ĐỐI SOÁT CHO TAB 3 & TÍNH METRICS
        tested_dict = {}
        for sheet in xls.sheet_names:
            df_temp = pd.read_excel(xls, sheet)
            col_name = None
            col_status = None
            
            for c in df_temp.columns:
                c_str = str(c).lower()
                if any(k in c_str for k in ['nhân sự', 'nhan vien', 'name', 'tên nv', 'họ và tên']):
                    col_name = c
                if any(k in c_str for k in ['qc status', 'trạng thái', 'kết quả', 'status', 'đánh giá', 'rework']):
                    col_status = c

            if col_name:
                for _, row in df_temp.iterrows():
                    val_name = str(row[col_name]).strip()
                    val_status = str(row[col_status]).strip() if col_status and pd.notna(row[col_status]) else "Đã test"
                    
                    for target in target_35_nv:
                        if target.lower() in val_name.lower():
                            st_lower = val_status.lower()
                            if any(x in st_lower for x in ['không đạt', 'failed', 'rework', 'lỗi', 'fail', 'chưa đạt']):
                                res = "❌ Không đạt"
                            elif any(x in st_lower for x in ['đạt', 'pass', 'ok', 'thành công', 'good']):
                                res = "🎯 Đạt"
                            else:
                                res = f"📋 {val_status}" if val_status != "nan" else "✅ Đã test"
                            
                            tested_dict[target] = {
                                "test_status": "✅ Đã test",
                                "result": res
                            }

        count_tt1_tested = len(tested_dict)

        # HÀNG THỐNG KÊ CHI TIẾT (METRICS HEADER)
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Trade Audit", "203 / 206 CH")
        col2.metric("Data Plus", "174 / 174 CH")
        col3.metric("Mystery CH", "65 / 114 CH")
        col4.metric("NV Trả Bài (TT1)", f"{count_tt1_tested} / 35 NV")
        col5.metric("Điện Thoại Vui", "29 / 32 CH")

        st.divider()

        # THIẾT LẬP CÁC TAB BÁO CÁO
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Tiến Độ Trade theo Leader", 
            "➕ Tiến Độ Plus & QC Status", 
            "🎤 Kiểm Tra Phỏng Vấn (TT1)", 
            "⚠️ Danh Sách YCBS (Rework)", 
            "🕵️ Mystery Shopper"
        ])

        # --- TAB 1 ---
        with tab1:
            st.subheader("1) Tiến Độ Trade Audit Theo Leader")
            if "trade audit" in [s.lower() for s in xls.sheet_names]:
                sheet_trade = [s for s in xls.sheet_names if s.lower() == "trade audit"][0]
                df_trade = pd.read_excel(xls, sheet_trade)
                st.dataframe(df_trade, use_container_width=True)
            else:
                st.warning("Chưa tìm thấy sheet Trade Audit trong file.")

        # --- TAB 2 ---
        with tab2:
            st.subheader("2) Tiến Độ Data Plus & Trạng Thái QC")
            if "auditplus" in [s.lower() for s in xls.sheet_names]:
                sheet_plus = [s for s in xls.sheet_names if s.lower() == "auditplus"][0]
                df_plus = pd.read_excel(xls, sheet_plus)
                st.dataframe(df_plus, use_container_width=True)
            else:
                st.warning("Chưa tìm thấy sheet AuditPlus trong file.")

        # --- TAB 3 (TỰ ĐỘNG ĐỐI SOÁT 35 NV & KẾT QUẢ QC) ---
        with tab3:
            st.subheader("3) Danh Sách Nhân Sự Bắt Buộc Phỏng Vấn (35 NV - Kết Quả QC & Phỏng Vấn)")

            if "Interview Tracking" in xls.sheet_names:
                df_tt1 = pd.read_excel(xls, "Interview Tracking")
                st.dataframe(df_tt1, use_container_width=True)
            else:
                st.info("ℹ️ Tự động đối soát dữ liệu thô: Quét tiến độ & Phân loại kết quả Đạt / Không đạt.")
                
                report_data = []
                for idx, nv in enumerate(target_35_nv, 1):
                    res_info = tested_dict.get(nv, {"test_status": "⏳ Chưa test", "result": "➖ Chưa test"})
                    report_data.append({
                        "STT": idx,
                        "Tên Nhân Sự": nv,
                        "Trạng Thái Test": res_info["test_status"],
                        "Kết Quả QC": res_info["result"]
                    })
                    
                df_report_35 = pd.DataFrame(report_data)
                st.dataframe(df_report_35, use_container_width=True, height=500)

        # --- TAB 4 ---
        with tab4:
            st.subheader("4) Danh Sách Yêu Cầu Bổ Sung / Rework")
            st.info("Danh sách tự động tổng hợp các lỗi YCBS/Rework từ các chi nhánh.")

        # --- TAB 5 ---
        with tab5:
            st.subheader("5) Tiến Độ & Kết Quả Mystery Shopper")
            if "mystery" in [s.lower() for s in xls.sheet_names]:
                sheet_myster = [s for s in xls.sheet_names if s.lower() == "mystery"][0]
                df_mystery = pd.read_excel(xls, sheet_myster)
                st.dataframe(df_mystery, use_container_width=True)
            else:
                st.warning("Chưa tìm thấy sheet Mystery trong file.")

    except Exception as e:
        st.error(f"Lỗi xử lý dữ liệu: {e}")
else:
    st.info("👋 Vui lòng tải file Excel báo cáo lên để kích hoạt hệ thống Dashboard!")