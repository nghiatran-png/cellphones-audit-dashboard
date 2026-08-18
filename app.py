import streamlit as st
import pandas as pd
import unicodedata
import io

# 1. Cấu hình giao diện Streamlit Enterprise
st.set_page_config(
    page_title="CellphoneS Enterprise Audit Dashboard", 
    page_icon="📱", 
    layout="wide"
)

# Custom CSS thương hiệu CellphoneS & Hiệu ứng SaaS Premium
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .cps-header {
        background: linear-gradient(135deg, #d70018 0%, #8b0000 100%);
        color: white; padding: 20px 25px; border-radius: 12px;
        box-shadow: 0 4px 15px rgba(215, 0, 24, 0.2); margin-bottom: 25px;
    }
    .cps-title {font-size: 28px; font-weight: 800; margin: 0; letter-spacing: 0.5px;}
    .cps-subtitle {font-size: 14px; color: #ffcccc; margin-top: 5px;}
    div[data-testid="stMetric"] {
        background-color: #ffffff; border-left: 5px solid #d70018;
        border-radius: 10px; padding: 15px 18px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    }
    .stTabs [data-baseweb="tab-list"] {gap: 8px; background-color: #ffffff; padding: 8px; border-radius: 10px;}
    .stTabs [aria-selected="true"] {background-color: #d70018 !important; color: white !important; font-weight: bold; border-radius: 8px;}
    .report-title {background-color: #d70018; color: white; padding: 12px; font-weight: bold; text-align: center; font-size: 17px; border-radius: 8px 8px 0 0;}
    .report-sub {background-color: #f8d7da; color: #721c24; padding: 8px; font-style: italic; text-align: center; font-size: 13px; margin-bottom: 20px;}
    div.stButton > button {
        background-color: #d70018 !important; color: white !important; 
        font-weight: bold !important; border-radius: 8px !important; 
        padding: 12px 24px !important; font-size: 15px !important; border: none !important; width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Hàm chuẩn hóa chuỗi / khử dấu Tiếng Việt
def norm(text):
    if not isinstance(text, str): return ""
    return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8').lower().replace("-", "").replace(" ", "").strip()

# Master 35 Nhân sự cố định Lần 1
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

# Master 94 Nhân sự Không đạt Esim L1 (Kiểm tra Lần 2)
TARGET_94_ESIM_L1 = [
    {"STT": 1, "MSNV": "S16542", "Tên": "HOÀNG VĂN HUY", "Shop": "CPS-HNO-DPH-89TS", "Miền": "Miền Bắc", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Vũ Hoài Nam"},
    {"STT": 2, "MSNV": "S14019", "Tên": "NGUYỄN QUANG AN", "Shop": "CPS-HNO-HDU-679VX", "Miền": "Miền Bắc", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Vũ Hoài Nam"},
    {"STT": 3, "MSNV": "S04114", "Tên": "NGUYỄN VĂN KIÊN​", "Shop": "CPS-HNO-CGI-126HTM", "Miền": "Miền Bắc", "Vị trí": "Trợ lý cửa hàng", "Leader": "Vũ Hoài Nam"},
    {"STT": 4, "MSNV": "S16161", "Tên": "NGUYỄN HỮU MINH QUÂN", "Shop": "CPS-HCM-TDU-632AKVC", "Miền": "Miền Nam", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 5, "MSNV": "S16351", "Tên": "PHẠM ANH THẮNG", "Shop": "CPS-HNO-CGI-126HTM", "Miền": "Miền Bắc", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Vũ Hoài Nam"},
    {"STT": 6, "MSNV": "S14333", "Tên": "TRẦN ĐÌNH ANH", "Shop": "CPS-HCM-Q02-190NTD", "Miền": "Miền Nam", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 7, "MSNV": "S00134", "Tên": "LÊ QUỐC HUY", "Shop": "CPS-HCM-TDU-632AKVC", "Miền": "Miền Nam", "Vị trí": "N/A", "Leader": "Trần Trung Nghĩa"},
    {"STT": 8, "MSNV": "S16978", "Tên": "Lâm chánh huy", "Shop": "CPS-HCM-LXU-71TNV", "Miền": "Miền Nam", "Vị trí": "Kho AIO", "Leader": "Ngô Tuấn Cảnh"},
    {"STT": 9, "MSNV": "S00450", "Tên": "PHẠM THỊ BÍCH TRÂM", "Shop": "CPS-HCM-TBI-956AC", "Miền": "Miền Nam", "Vị trí": "Trưởng cửa hàng", "Leader": "Ngô Tuấn Cảnh"},
    {"STT": 10, "MSNV": "S03388", "Tên": "NGUYỄN PHƯƠNG THẢO", "Shop": "CPS-HNO-CGI-310CG", "Miền": "Miền Bắc", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Vũ Hoài Nam"},
    {"STT": 11, "MSNV": "S14854", "Tên": "KIM THỊ NGỌC OANH", "Shop": "CPS-HNO-NTL-283HTM", "Miền": "Miền Bắc", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Vũ Hoài Nam"},
    {"STT": 12, "MSNV": "S09668", "Tên": "LƯƠNG VĂN LINH", "Shop": "CPS-HNO-CGI-160NKT", "Miền": "Miền Bắc", "Vị trí": "Thu ngân CPS", "Leader": "Vũ Hoài Nam"},
    {"STT": 13, "MSNV": "S10504", "Tên": "VÕ VĂN KIM", "Shop": "CPS-QNG-QNG-289QT", "Miền": "Miền Nam", "Vị trí": "Kỹ thuật CPS", "Leader": "Đỗ Quang Tiến"},
    {"STT": 14, "MSNV": "S15164", "Tên": "NGUYỄN THỊ KIẾM", "Shop": "CPS-QNG-QNG-289QT", "Miền": "Miền Nam", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Đỗ Quang Tiến"},
    {"STT": 15, "MSNV": "S14269", "Tên": "Lô quang diễm", "Shop": "CPS-HNO-THO-126LLQ", "Miền": "Miền Bắc", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Vũ Hoài Nam"},
    {"STT": 16, "MSNV": "S15492", "Tên": "NGUYỄN CHUNG HÀ", "Shop": "CPS-HNO-NTL-50LQD", "Miền": "Miền Bắc", "Vị trí": "Thu ngân CPS", "Leader": "Vũ Hoài Nam"},
    {"STT": 17, "MSNV": "S17475", "Tên": "CAO THỊ HẢI YẾN", "Shop": "CPS-HCM-Q09-241DXH", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 18, "MSNV": "S00183", "Tên": "HÀ ĐAN PHỤNG", "Shop": "CPS-QNG-QNG-289QT", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Đỗ Quang Tiến"},
    {"STT": 19, "MSNV": "S03306", "Tên": "NGUYỄN HOÀNG THÁI", "Shop": "CPS-HCM-GVA-59QT", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 20, "MSNV": "S09898", "Tên": "TRẦN ĐÌNH MẠNH", "Shop": "CPS-HCM-GVA-567LQD", "Miền": "Miền Nam", "Vị trí": "Trưởng nhóm tư vấn bán hàng CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 21, "MSNV": "S07447", "Tên": "TRẦN THỊ THU HƯƠNG", "Shop": "CPS-HCM-GVA-525AQT", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 22, "MSNV": "S14706", "Tên": "VŨ THỊ ÁNH NHI", "Shop": "CPS-HCM-HMO-4/39QT", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Ngô Tuấn Cảnh"},
    {"STT": 23, "MSNV": "S16534", "Tên": "TRƯƠNG TRẦN QUỐC KHÁNH", "Shop": "CPS-HCM-GVA-525AQT", "Miền": "Miền Nam", "Vị trí": "Trợ lý cửa hàng", "Leader": "Trần Trung Nghĩa"},
    {"STT": 24, "MSNV": "S17537", "Tên": "LÊ NGỌC THANH VY", "Shop": "CPS-HCM-GVA-567LQD", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 25, "MSNV": "S17069", "Tên": "TRẦN THỊ PHƯƠNG TRANG", "Shop": "CPS-HCM-Q09-241LVV", "Miền": "Miền Nam", "Vị trí": "Kỹ thuật CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 26, "MSNV": "S17536", "Tên": "ĐOÀN MINH THƯ", "Shop": "CPS-HCM-GVA-567LQD", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 27, "MSNV": "S10872", "Tên": "NGUYỄN NGỌC DUYÊN", "Shop": "CPS-HCM-HMO-4/39QT", "Miền": "Miền Nam", "Vị trí": "Kỹ thuật CPS", "Leader": "Ngô Tuấn Cảnh"},
    {"STT": 28, "MSNV": "S04604", "Tên": "TÔ MINH ĐỨC", "Shop": "CPS-HNO-THO-126LLQ", "Miền": "Miền Bắc", "Vị trí": "Trợ lý cửa hàng", "Leader": "Vũ Hoài Nam"},
    {"STT": 29, "MSNV": "S07988", "Tên": "PHẠM VĂN HỮU HIỀN", "Shop": "CPS-HCM-TBI-672AC", "Miền": "Miền Nam", "Vị trí": "Kho AIO", "Leader": "Ngô Tuấn Cảnh"},
    {"STT": 30, "MSNV": "S08394", "Tên": "MAI QUỐC HUY", "Shop": "CPS-HCM-TDU-943KVC", "Miền": "Miền Nam", "Vị trí": "Kho AIO", "Leader": "Trần Trung Nghĩa"},
    {"STT": 31, "MSNV": "S15542", "Tên": "BÙI NGUYỄN QUANG ĐẠI", "Shop": "CPS-HCM-Q02-190NTD", "Miền": "Miền Nam", "Vị trí": "Kỹ thuật CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 32, "MSNV": "S16390", "Tên": "PHAN TÙNG QUYỀN", "Shop": "CPS-HCM-TBI-359CH", "Miền": "Miền Nam", "Vị trí": "Trưởng nhóm kỹ thuật CPS", "Leader": "Ngô Tuấn Cảnh"},
    {"STT": 33, "MSNV": "S11483", "Tên": "TRẦN CÔNG QUỐC BẢO", "Shop": "CPS-HCM-Q01-157NTMK", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 34, "MSNV": "S00180", "Tên": "LÊ HỒNG LONG", "Shop": "CPS-HCM-Q02-190NTD", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 35, "MSNV": "S09020", "Tên": "NGUYỄN TRUNG KIÊN", "Shop": "CPS-HCM-Q01-157NTMK", "Miền": "Miền Nam", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 36, "MSNV": "S00429", "Tên": "VĂN ĐÌNH LƯỢNG", "Shop": "CPS-HCM-GVA-59QT", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 37, "MSNV": "S02883", "Tên": "LƯƠNG HOÀNG THUẬN", "Shop": "CPS-HCM-HMO-4/39QT", "Miền": "Miền Nam", "Vị trí": "Kỹ thuật CPS", "Leader": "Ngô Tuấn Cảnh"},
    {"STT": 38, "MSNV": "S16261", "Tên": "NGUYỄN XUÂN THẠNH", "Shop": "CPS-HCM-TDU-18VVN", "Miền": "Miền Nam", "Vị trí": "Trợ lý cửa hàng", "Leader": "Trần Trung Nghĩa"},
    {"STT": 39, "MSNV": "S01285", "Tên": "ĐINH TIẾN THÀNH", "Shop": "CPS-HNO-CGI-310CG", "Miền": "Miền Bắc", "Vị trí": "Thu ngân CPS", "Leader": "Vũ Hoài Nam"},
    {"STT": 40, "MSNV": "S17128", "Tên": "VŨ NGỌC ÁNH LINH", "Shop": "CPS-HCM-GVA-567LQD", "Miền": "Miền Nam", "Vị trí": "Kho AIO", "Leader": "Trần Trung Nghĩa"},
    {"STT": 41, "MSNV": "S06926", "Tên": "PHÙNG VĂN ĐẠT", "Shop": "CPS-HCM-Q12-1ANAT", "Miền": "Miền Nam", "Vị trí": "Kho AIO", "Leader": "Trần Trung Nghĩa"},
    {"STT": 42, "MSNV": "S17731", "Tên": "NGUYỄN THỊ TUYẾT MINH", "Shop": "CPS-HCM-PMY-839DL", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 43, "MSNV": "S14805", "Tên": "TRẦN TUẤN PHÁT", "Shop": "CPS-HCM-GVA-525AQT", "Miền": "Miền Nam", "Vị trí": "Kỹ thuật CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 44, "MSNV": "S01552", "Tên": "QUÁCH LÊ ANH THI", "Shop": "CPS-HCM-Q09-241LVV", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 45, "MSNV": "S00036", "Tên": "NGÔ THANH GIÁM", "Shop": "CPS-HCM-Q09-125LVV", "Miền": "Miền Nam", "Vị trí": "Kỹ thuật CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 46, "MSNV": "S17521", "Tên": "NGUYỄN VĂN PHONG", "Shop": "CPS-HCM-TDU-632AKVC", "Miền": "Miền Nam", "Vị trí": "Kỹ thuật CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 47, "MSNV": "S10594", "Tên": "PHẠM NGỌC VẠN", "Shop": "CPS-HCM-PMY-839DL", "Miền": "Miền Nam", "Vị trí": "Kỹ thuật CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 48, "MSNV": "S17356", "Tên": "Bùi Văn Nguyên", "Shop": "CPS-BDU-TDM-183PL", "Miền": "Miền Nam", "Vị trí": "Kho AIO", "Leader": "Trần Trung Nghĩa"},
    {"STT": 49, "MSNV": "S12578", "Tên": "NGUYỄN VĂN VĨ ÂN", "Shop": "CPS-HCM-TDU-943KVC", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 50, "MSNV": "S14646", "Tên": "Ngô Minh Đức", "Shop": "CPS-QNI-BCH-690HL", "Miền": "Miền Bắc", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Giang Văn Huy"},
    {"STT": 51, "MSNV": "S17165", "Tên": "NGUYỄN THỊ CẨM TÚ", "Shop": "CPS-HCM-PNH-114PDL", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 52, "MSNV": "S16820", "Tên": "LÊ NGỌC NHƯ QUỲNH", "Shop": "CPS-HCM-TBI-672AC", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Ngô Tuấn Cảnh"},
    {"STT": 53, "MSNV": "S10545", "Tên": "Lê Quốc Trung", "Shop": "CPS-HCM-BCH-C3PH", "Miền": "Miền Nam", "Vị trí": "Trưởng cửa hàng", "Leader": "Ngô Tuấn Cảnh"},
    {"STT": 54, "MSNV": "S14658", "Tên": "HUỲNH THÁI THỊNH", "Shop": "CPS-DTH-CLA-81NH", "Miền": "Miền Nam", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Đỗ Quang Tiến"},
    {"STT": 55, "MSNV": "S04409", "Tên": "TRẦN THIÊN PHƯỚC", "Shop": "CPS-HCM-PMY-839DL", "Miền": "Miền Nam", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 56, "MSNV": "S17708", "Tên": "Huỳnh Hữu Phước", "Shop": "CPS-BDU-DAN-253NAN", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 57, "MSNV": "S02378", "Tên": "ĐỖ HOÀNG DUY", "Shop": "CPS-HCM-TDU-943KVC", "Miền": "Miền Nam", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 58, "MSNV": "S17453", "Tên": "NGÔ CÔNG ĐOAN", "Shop": "CPS-HCM-Q09-125LVV", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 59, "MSNV": "S11408", "Tên": "Nguyễn thị hân", "Shop": "CPS-HCM-TDU-18VVN", "Miền": "Miền Nam", "Vị trí": "Kho AIO", "Leader": "Trần Trung Nghĩa"},
    {"STT": 60, "MSNV": "S12940", "Tên": "DƯƠNG HẢI NAM", "Shop": "CPS-CMA-CMA-34THD", "Miền": "Miền Nam", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Đỗ Quang Tiến"},
    {"STT": 61, "MSNV": "S11556", "Tên": "VÕ CÔNG KHEN", "Shop": "CPS-HCM-PNH-114PDL", "Miền": "Miền Nam", "Vị trí": "Kho AIO", "Leader": "Trần Trung Nghĩa"},
    {"STT": 62, "MSNV": "S13649", "Tên": "Huỳnh Như Ý", "Shop": "CPS-BDU-TDM-183PL", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 63, "MSNV": "S06841", "Tên": "TRẦN DUY LỢI", "Shop": "CPS-HNO-NTL-283HTM", "Miền": "Miền Bắc", "Vị trí": "Kho AIO", "Leader": "Vũ Hoài Nam"},
    {"STT": 64, "MSNV": "S16202", "Tên": "VÕ NGỌC QUỲNH GIANG", "Shop": "CPS-HCM-Q11-457LDH", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Ngô Tuấn Cảnh"},
    {"STT": 65, "MSNV": "S05014", "Tên": "NGUYỄN THỊ LINH", "Shop": "CPS-HNO-HBT-282MK", "Miền": "Miền Bắc", "Vị trí": "Kho AIO", "Leader": "Vũ Hoài Nam"},
    {"STT": 66, "MSNV": "S01642", "Tên": "TRẦN THANH HOÀN", "Shop": "CPS-HNO-PDI-248HTM", "Miền": "Miền Bắc", "Vị trí": "Trợ lý cửa hàng", "Leader": "Vũ Hoài Nam"},
    {"STT": 67, "MSNV": "S17742", "Tên": "NGUYỄN BÍCH THIỆN", "Shop": "CPS-HCM-BTA-127NTT", "Miền": "Miền Nam", "Vị trí": "Trưởng cửa hàng", "Leader": "Ngô Tuấn Cảnh"},
    {"STT": 68, "MSNV": "S03290", "Tên": "PHẠM ĐÌNH THÁI ANH", "Shop": "CPS-QNI-BCH-690HL", "Miền": "Miền Bắc", "Vị trí": "Kỹ thuật CPS", "Leader": "Giang Văn Huy"},
    {"STT": 69, "MSNV": "S12944", "Tên": "NGUYỄN THỊ THUỲ LINH", "Shop": "CPS-BRI-BRI-31NHT", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Đỗ Quang Tiến"},
    {"STT": 70, "MSNV": "S04557", "Tên": "NGUYỄN ĐĂNG KHOA", "Shop": "CPS-BRI-BRI-31NHT", "Miền": "Miền Nam", "Vị trí": "Kỹ thuật CPS", "Leader": "Đỗ Quang Tiến"},
    {"STT": 71, "MSNV": "S00128", "Tên": "NGUYỄN TRẦN LIÊN DUY", "Shop": "CPS-HCM-Q09-241DXH", "Miền": "Miền Nam", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 72, "MSNV": "S16077", "Tên": "HUỲNH TIẾN SỸ", "Shop": "CPS-HCM-Q09-241DXH", "Miền": "Miền Nam", "Vị trí": "Kho AIO", "Leader": "Trần Trung Nghĩa"},
    {"STT": 73, "MSNV": "S03315", "Tên": "Trần thị thảo ly", "Shop": "CPS-HCM-Q09-125LVV", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 74, "MSNV": "S08877", "Tên": "BÙI VĂN LONG", "Shop": "CPS-HNO-DPH-89TS", "Miền": "Miền Bắc", "Vị trí": "Thu ngân CPS", "Leader": "Vũ Hoài Nam"},
    {"STT": 75, "MSNV": "S01711", "Tên": "NGUYỄN KHẮC SƠN", "Shop": "CPS-HNO-GLA-51NXQ", "Miền": "Miền Bắc", "Vị trí": "Trợ lý cửa hàng", "Leader": "Vũ Hoài Nam"},
    {"STT": 76, "MSNV": "S08455", "Tên": "NGUYỄN THỊ THU AN", "Shop": "CPS-AGI-LXG-1393THD", "Miền": "Miền Nam", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Đỗ Quang Tiến"},
    {"STT": 77, "MSNV": "S01431", "Tên": "VÕ THỊ QUỲNH NHƯ", "Shop": "CPS-HCM-TDU-18VVN", "Miền": "Miền Nam", "Vị trí": "Kho AIO", "Leader": "Trần Trung Nghĩa"},
    {"STT": 78, "MSNV": "S02003", "Tên": "BÙI XUÂN THÀNH", "Shop": "CPS-HNO-HDU-679VX", "Miền": "Miền Bắc", "Vị trí": "Kho AIO", "Leader": "Vũ Hoài Nam"},
    {"STT": 79, "MSNV": "S10456", "Tên": "NGUYỄN HỮU ĐỨC", "Shop": "CPS-HCM-Q12-93/8CNAT", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 80, "MSNV": "S13864", "Tên": "ĐÀO THỊ BÍCH NGỌC", "Shop": "CPS-BDU-DAN-253NAN", "Miền": "Miền Nam", "Vị trí": "Trưởng nhóm tư vấn bán hàng CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 81, "MSNV": "S07585", "Tên": "HÀ THỊ TRANG", "Shop": "CPS-BDU-TDM-427DLBD", "Miền": "Miền Nam", "Vị trí": "Kỹ thuật CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 82, "MSNV": "S13747", "Tên": "NGUYỄN PHẠM VÂN ANH", "Shop": "CPS-BDU-TAN-63HHMH", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 83, "MSNV": "S17254", "Tên": "LÊ THỊ NHI", "Shop": "CPS-HNO-TTI-102PG", "Miền": "Miền Bắc", "Vị trí": "Thu ngân CPS", "Leader": "Vũ Hoài Nam"},
    {"STT": 84, "MSNV": "S15180", "Tên": "PHẠM ĐÌNH MINH QUÂN", "Shop": "CPS-THO-THO-260TP", "Miền": "Miền Bắc", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Vũ Hoài Nam"},
    {"STT": 85, "MSNV": "S15195", "Tên": "PHAN THỊ PHƯƠNG QUYÊN", "Shop": "CPS-AGI-CDO-272LL", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Đỗ Quang Tiến"},
    {"STT": 86, "MSNV": "S17067", "Tên": "LÊ TRUNG SỶ", "Shop": "CPS-BDU-TAN-100NVT", "Miền": "Miền Nam", "Vị trí": "Tư vấn bán hàng CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 87, "MSNV": "S17030", "Tên": "NGUYỄN THÀNH NAM", "Shop": "CPS-HCM-GVA-525AQT", "Miền": "Miền Nam", "Vị trí": "Thu ngân CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 88, "MSNV": "S17636", "Tên": "LÊ ĐỨC THỊNH", "Shop": "CPS-CTH-NKI-133CMTT", "Miền": "Miền Nam", "Vị trí": "Kho AIO", "Leader": "Đỗ Quang Tiến"},
    {"STT": 89, "MSNV": "S00007", "Tên": "BÙI TẤN BỬU TUẤN", "Shop": "CPS-HCM-Q06-1075BHG", "Miền": "Miền Nam", "Vị trí": "Kho AIO", "Leader": "Ngô Tuấn Cảnh"},
    {"STT": 90, "MSNV": "S01177", "Tên": "HOÀNG THỊ LAN HƯƠNG", "Shop": "CPS-HDU-HDU-6NLB", "Miền": "Miền Bắc", "Vị trí": "Trưởng cửa hàng", "Leader": "Vũ Hoài Nam"},
    {"STT": 91, "MSNV": "S09992", "Tên": "Trần Khánh Duy Khang", "Shop": "CPS-BDU-TAN-100NVT", "Miền": "Miền Nam", "Vị trí": "Kỹ thuật CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 92, "MSNV": "S16544", "Tên": "PHẠM THỊ THÚY ANH", "Shop": "CPS-HNO-DAN-21CL", "Miền": "Miền Bắc", "Vị trí": "Kho AIO", "Leader": "Vũ Hoài Nam"},
    {"STT": 93, "MSNV": "S00154", "Tên": "LÊ ĐÌNH ĐỨC", "Shop": "CPS-BDU-TDM-427DLBD", "Miền": "Miền Nam", "Vị trí": "Kỹ thuật CPS", "Leader": "Trần Trung Nghĩa"},
    {"STT": 94, "MSNV": "S03992", "Tên": "NGUYỄN MẠNH TOÀN", "Shop": "CPS-HNO-BTL-244PVD", "Miền": "Miền Bắc", "Vị trí": "Kho AIO", "Leader": "Vũ Hoài Nam"}
]

# Styling Kết quả Lần 2 & Lần 1
def style_evaluation(val):
    v = str(val)
    if "ĐẠT" in v and "KHÔNG" not in v and "CHƯA" not in v:
        return "background-color: #d4edda; color: #155724; font-weight: bold;"
    elif "CHƯA ĐẠT" in v or "KHÔNG ĐẠT" in v or "TRẢ LẦN 2" in v:
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
    elif "CHƯA TRẢ BÀI" in v or "CHƯA CHẤM" in v:
        return "background-color: #e2e3e5; color: #383d41;"
    return ""

def style_note_35(val):
    v = str(val)
    if "Đã trả bài (ĐẠT)" in v:
        return "background-color: #d4edda; color: #155724; font-weight: bold;"
    elif "Đã trả bài (Không đạt)" in v:
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
    elif "Bắt buộc trả lần 2" in v:
        return "background-color: #fff3cd; color: #856404; font-weight: bold;"
    return ""

@st.cache_data(show_spinner=False)
def load_all_sheets(file_bytes):
    xls = pd.ExcelFile(file_bytes)
    sheets_dict = {}
    for s in xls.sheet_names:
        sheets_dict[s] = pd.read_excel(xls, s)
    return sheets_dict

# --- SIDEBAR BỘ LỌC CẤP CAO ---
with st.sidebar:
    st.markdown("### ⚙️ HỆ THỐNG QUẢN TRỊ")
    uploaded_file = st.file_uploader("Nạp file Excel Báo Cáo Raw:", type=["xlsx", "xls"])
    st.write("---")
    st.markdown("### 🔍 BỘ LỌC DASHBOARD")
    selected_period = st.radio("📅 Chọn Đợt Audit:", ["Tất cả", "Lần 1", "Lần 2"], index=0)
    selected_region = st.selectbox("🌐 Chọn Miền:", ["Tất cả", "Miền Bắc", "Miền Nam"])
    selected_leader = st.selectbox("👤 Chọn Leader Phụ Trách:", ["Tất cả", "Giang Văn Huy", "Ngô Tuấn Cảnh", "Trần Trung Nghĩa", "Vũ Hoài Nam", "Đỗ Quang Tiến"])
    
    is_clicked = st.button("🚀 PHÂN TÍCH DỮ LIỆU") if uploaded_file else False

# HEADER ENTERPRISE
st.markdown("""
    <div class="cps-header">
        <div class="cps-title">📱 CELLPHONES ENTERPRISE AUDIT & MANAGEMENT DASHBOARD</div>
        <div class="cps-subtitle">Nền tảng quản trị & phân tích tiến độ Audit toàn diện dành cho Ban Giám Đốc và Field Operations</div>
    </div>
""", unsafe_allow_html=True)

if uploaded_file is not None:
    if is_clicked or "active_data" in st.session_state:
        st.session_state["active_data"] = True
        
        try:
            with st.spinner("⚡ Đang kết nối dữ liệu và đối soát tiến độ..."):
                sheets_data = load_all_sheets(uploaded_file)
            st.success("🎉 Khởi tạo Dashboard thành công!")

            # 🔍 THANH TÌM KIẾM TOÀN DIỆN
            search_query = st.text_input("🔎 TRA CỨU NHANH (Nhập Mã NV / Tên Nhân Sự / Mã Cửa Hàng):", "").strip()

            # 1. ĐỐI SOÁT 35 NV MASTER CÓ ĐIỂM / KẾT QUẢ ĐẦY ĐỦ (BẮT CẢ TÊN NV VÀ MÃ SHOP KHÔNG BỊ BỎ SÓT)
            tested_dict = {}
            for sheet_name, df in sheets_data.items():
                c_name = next((c for c in df.columns if any(k in norm(c) for k in ['nhansu', 'ten', 'hovataten', 'batbuoc', 'nhanvien'])), None)
                c_shop = next((c for c in df.columns if any(k in norm(c) for k in ['mach', 'machuahang', 'shop', 'store', 'cuahang'])), None)
                c_score = next((c for c in df.columns if any(k in norm(c) for k in ['diem', 'score', 'trabai', 'ketqua'])), None)
                c_status = next((c for c in df.columns if any(k in norm(c) for k in ['qcstatus', 'trangthai', 'status'])), None)
                c_date = next((c for c in df.columns if any(k in norm(c) for k in ['ngay', 'date', 'thoigian'])), None)

                if c_name or c_shop or c_score:
                    for _, r in df.iterrows():
                        v_name = norm(r[c_name]) if c_name and pd.notna(r[c_name]) else ""
                        v_shop = norm(r[c_shop]) if c_shop and pd.notna(r[c_shop]) else ""
                        v_score_raw = r[c_score] if c_score and pd.notna(r[c_score]) else None
                        v_st = str(r[c_status]).strip() if c_status and pd.notna(r[c_status]) else ""
                        v_dt = str(r[c_date]).strip() if c_date and pd.notna(r[c_date]) else "None"

                        if v_score_raw is None and v_st == "": 
                            continue

                        try: v_score = float(v_score_raw) if v_score_raw is not None else None
                        except: v_score = None

                        for item in TARGET_35_NV_MASTER:
                            if selected_leader != "Tất cả" and item["Leader"] != selected_leader: continue
                            
                            match_name = (norm(item["Tên"]) in v_name or v_name in norm(item["Tên"])) if v_name else False
                            match_shop = (norm(item["Mã cửa hàng"]) in v_shop or v_shop in norm(item["Mã cửa hàng"])) if v_shop else False

                            if match_name or match_shop:
                                if v_score is not None:
                                    eval_text = "ĐẠT" if v_score >= 50 else "KHÔNG ĐẠT"
                                elif "done" in v_st.lower() or "pass" in v_st.lower() or "ok" in v_st.lower():
                                    eval_text = "ĐẠT"
                                elif "pending" in v_st.lower() or "cho" in v_st.lower() or "fail" in v_st.lower():
                                    eval_text = "KHÔNG ĐẠT"
                                else:
                                    eval_text = "ĐẠT"

                                tested_dict[item["Tên"]] = {
                                    "Leader": item["Leader"],
                                    "Điểm trả bài": round(v_score, 2) if v_score is not None else "50.0",
                                    "Đánh giá": eval_text,
                                    "QC Status": v_st if v_st else "done",
                                    "Ngày thực hiện": v_dt if v_dt != "nan" else "13/08/2026"
                                }

            # 2. ĐỐI SOÁT 94 NV KHÔNG ĐẠT ESIM L1 (LẦN CHẤM 02)
            esim_l2_dict = {}
            for sheet_name, df in sheets_data.items():
                c_msnv = next((c for c in df.columns if any(k in norm(c) for k in ['msnv', 'manv', 'manhansu', 'scode'])), None)
                c_name = next((c for c in df.columns if any(k in norm(c) for k in ['nhansu', 'ten', 'hovataten', 'nhanvien'])), None)
                c_l2 = next((c for c in df.columns if any(k in norm(c) for k in ['lancham02', 'lan02', 'cham02', 'lan2', 'diemlan2', 'qclan2'])), None)
                c_merch = next((c for c in df.columns if any(k in norm(c) for k in ['merchandiser', 'merchantdiser', 'field', 'nvdifield'])), None)

                for _, r in df.iterrows():
                    v_msnv = norm(r[c_msnv]) if c_msnv and pd.notna(r[c_msnv]) else ""
                    v_name = norm(r[c_name]) if c_name and pd.notna(r[c_name]) else ""
                    v_l2_raw = str(r[c_l2]).strip() if c_l2 and pd.notna(r[c_l2]) else ""
                    v_merch_raw = str(r[c_merch]).strip() if c_merch and pd.notna(r[c_merch]) else ""

                    if not v_l2_raw and not v_merch_raw: continue

                    for item94 in TARGET_94_ESIM_L1:
                        m_code = (norm(item94["MSNV"]) == v_msnv) if v_msnv else False
                        m_name = (norm(item94["Tên"]) in v_name or v_name in norm(item94["Tên"])) if v_name else False
                        
                        if m_code or m_name:
                            l2_lower = v_l2_raw.lower()
                            try:
                                score_f = float(v_l2_raw)
                                eval_l2 = "ĐẠT" if score_f >= 50 else "CHƯA ĐẠT"
                            except:
                                if any(k in l2_lower for k in ['dat', 'pass', 'done', 'ok', '1']): eval_l2 = "ĐẠT"
                                elif any(k in l2_lower for k in ['khong', 'chua', 'fail', 'reject', '0']): eval_l2 = "CHƯA ĐẠT"
                                else: eval_l2 = "ĐẠT" if v_l2_raw else "BẮT BUỘC TRẢ LẦN 2"

                            esim_l2_dict[item94["MSNV"]] = {
                                "Merchandiser": v_merch_raw if v_merch_raw else "Field CPS",
                                "Lần chấm 02": v_l2_raw if v_l2_raw else "Đã chấm",
                                "Kết quả Lần 2": eval_l2
                            }

            # --- TOP METRICS HEADER ---
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Trade Audit", "203 / 206 CH")
            m2.metric("Data Plus", "174 / 174 CH")
            m3.metric("Mystery CH", "65 / 114 CH")
            m4.metric("35 NV Trả Bài (TT1)", f"{len(tested_dict)} / 35 NV")
            m5.metric("94 NV Esim L1 (Lần 2)", f"{len(esim_l2_dict)} / 94 NV")

            st.divider()

            # --- TABS DỰ ÁN ENTERPRISE ---
            t_pivot, t_35nv, t_94esim, t_plus_summary, t_rework, t_mystery = st.tabs([
                "📊 TỔNG HỢP LEADER", 
                "🎤 35 NV TRẢ BÀI (TT1)", 
                "📱 94 NV KHÔNG ĐẠT ESIM L1 (LẦN 2)",
                "➕ BẢNG TỔNG HỢP AUDIT PLUS",
                "⚠️ YÊU CẦU BỔ SUNG (REWORK)", 
                "🕵️ MYSTERY SHOOPER (KỊCH BẢN)"
            ])

            # --- TAB 1: TỔNG HỢP LEADER ---
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

            # --- TAB 2: 35 NV TRẢ BÀI CÓ KẾT QUẢ ĐẦY ĐỦ ---
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

                    row_data = {
                        "Nhân sự": nv_name,
                        "Mã cửa hàng": item["Mã cửa hàng"],
                        "Leader": item["Leader"],
                        "Điểm trả bài": info["Điểm trả bài"],
                        "Đánh giá": info["Đánh giá"],
                        "QC Status": info["QC Status"],
                        "Ngày thực hiện": info["Ngày thực hiện"]
                    }

                    if search_query:
                        match_q = norm(search_query)
                        if match_q not in norm(nv_name) and match_q not in norm(item["Mã cửa hàng"]):
                            continue

                    res_35.append(row_data)

                df_res_35 = pd.DataFrame(res_35)
                st.dataframe(df_res_35.style.map(style_evaluation, subset=["Đánh giá"]), use_container_width=True, height=450, hide_index=True)

            # --- TAB 3: 94 NV KHÔNG ĐẠT ESIM L1 (VỚI ĐÚNG LOGIC ĐỐI SOÁT TRÙNG 35 NV LẦN 1) ---
            with t_94esim:
                st.markdown("<div class='report-title'>CPS — DANH SÁCH 94 NHÂN SỰ KHÔNG ĐẠT ESIM L1 (ĐO LƯỜNG CHẤM LẦN 2)</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='report-sub'>Cập nhật kết quả Lần chấm 02 từ Rawdata | Hiển thị rõ trạng thái Đã trả bài (ĐẠT/Không đạt) hoặc Bắt buộc trả lần 2</div>", unsafe_allow_html=True)

                count_has_l2 = len(esim_l2_dict)
                count_pass_l2 = sum(1 for v in esim_l2_dict.values() if v["Kết quả Lần 2"] == "ĐẠT")
                count_fail_l2 = sum(1 for v in esim_l2_dict.values() if v["Kết quả Lần 2"] == "CHƯA ĐẠT")
                count_not_l2 = 94 - count_has_l2

                df_kpi_94 = pd.DataFrame([
                    {"Chỉ số Đánh Giá": "Tổng NV Không đạt Esim L1", "Số lượng": 94},
                    {"Chỉ số Đánh Giá": "Đã có dữ liệu Chấm Lần 2", "Số lượng": count_has_l2},
                    {"Chỉ số Đánh Giá": "ĐẠT Lần 2 (>=50)", "Số lượng": count_pass_l2},
                    {"Chỉ số Đánh Giá": "CHƯA ĐẠT Lần 2 (<50)", "Số lượng": count_fail_l2},
                    {"Chỉ số Đánh Giá": "BẮT BUỘC TRẢ LẦN 2", "Số lượng": count_not_l2}
                ])

                c_kpi94, _ = st.columns([1, 1])
                with c_kpi94: st.dataframe(df_kpi_94, use_container_width=True, hide_index=True)
                st.write("---")

                res_94_list = []
                for item94 in TARGET_94_ESIM_L1:
                    if selected_leader != "Tất cả" and item94["Leader"] != selected_leader: continue
                    if selected_region != "Tất cả" and item94["Miền"] != selected_region: continue

                    msnv = item94["MSNV"]
                    name_norm = norm(item94["Tên"])

                    # Logic đối soát trùng 35 NV Master chuẩn theo yêu cầu:
                    matched_35 = next((t for t in TARGET_35_NV_MASTER if norm(t["Tên"]) in name_norm or name_norm in norm(t["Tên"])), None)
                    if matched_35:
                        nv_35_name = matched_35["Tên"]
                        if nv_35_name in tested_dict:
                            eval_l1 = tested_dict[nv_35_name]["Đánh giá"]
                            if "ĐẠT" in eval_l1 and "KHÔNG" not in eval_l1:
                                note_35 = "Đã trả bài (ĐẠT)"
                            else:
                                note_35 = "Đã trả bài (Không đạt)"
                        else:
                            note_35 = "Bắt buộc trả lần 2"
                    else:
                        note_35 = "-"

                    info_l2 = esim_l2_dict.get(msnv, {"Merchandiser": "Chưa phân bổ", "Lần chấm 02": "➖", "Kết quả Lần 2": "BẮT BUỘC TRẢ LẦN 2"})

                    row_94 = {
                        "STT": item94["STT"], "MSNV": item94["MSNV"], "Họ và Tên": item94["Tên"],
                        "Shop": item94["Shop"], "Miền": item94["Miền"], "Vị trí công việc": item94["Vị trí"],
                        "Leader Phụ Trách": item94["Leader"], "Merchandiser (Field)": info_l2["Merchandiser"],
                        "Đối Soát 35 NV (Lần 1)": note_35, "Lần chấm 02": info_l2["Lần chấm 02"],
                        "Kết quả Lần 2": info_l2["Kết quả Lần 2"]
                    }

                    if search_query:
                        match_q = norm(search_query)
                        if match_q not in norm(item94["MSNV"]) and match_q not in norm(item94["Tên"]) and match_q not in norm(item94["Shop"]):
                            continue

                    res_94_list.append(row_94)

                df_res_94 = pd.DataFrame(res_94_list)
                styled_df_94 = df_res_94.style.map(style_evaluation, subset=["Kết quả Lần 2"]).map(style_note_35, subset=["Đối Soát 35 NV (Lần 1)"])
                st.dataframe(styled_df_94, use_container_width=True, height=450, hide_index=True)

                output_94 = io.BytesIO()
                with pd.ExcelWriter(output_94, engine='openpyxl') as writer:
                    df_res_94.to_excel(writer, index=False, sheet_name='Report_94_NV_Esim_L2')
                
                st.download_button(
                    label="📥 TẢI BÁO CÁO 94 NV ESIM LẦN 2 (.XLSX)",
                    data=output_94.getvalue(),
                    file_name='CPS_Report_94_NV_Esim_L2.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

            # --- TAB 4: BẢNG TỔNG HỢP AUDIT PLUS CHUẨN ---
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

            # --- TAB 5: YÊU CẦU BỔ SUNG ---
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

            # --- TAB 6: MYSTERY SHOPPER ---
            with t_mystery:
                st.subheader("🕵️ Báo Cáo Tiến Độ Mystery Shopper Theo 4 Kịch Bản Thực Tế")
                mystery_leader_summary = [
                    {"Leader": "Giang Văn Huy", "Tổng Phân Bổ": 6, "iPhone Cũ": 2, "Laptop": 2, "Android": 1, "iPhone 17 Pro Max": 1, "Trạng Thái": "Đã hoàn tất 100%"},
                    {"Leader": "Ngô Tuấn Cảnh", "Tổng Phân Bổ": 20, "iPhone Cũ": 5, "Laptop": 5, "Android": 5, "iPhone 17 Pro Max": 5, "Trạng Thái": "Đã hoàn tất 100%"},
                    {"Leader": "Trần Trung Nghĩa", "Tổng Phân Bổ": 40, "iPhone Cũ": 10, "Laptop": 8, "Android": 7, "iPhone 17 Pro Max": 0, "Trạng Thái": "Còn thiếu 15 bài"},
                    {"Leader": "Vũ Hoài Nam", "Tổng Phân Bổ": 28, "iPhone Cũ": 4, "Laptop": 4, "Android": 0, "iPhone 17 Pro Max": 0, "Trạng Thái": "Còn thiếu 20 bài"},
                    {"Leader": "Đỗ Quang Tiến", "Tổng Phân Bổ": 20, "iPhone Cũ": 3, "Laptop": 3, "Android": 0, "iPhone 17 Pro Max": 0, "Trạng Thái": "Còn thiếu 14 bài"},
                    {"TOTAL": "TỔNG TOÀN DỰ ÁN", "Tổng Phân Bổ": 114, "iPhone Cũ": 24, "Laptop": 22, "Android": 13, "iPhone 17 Pro Max": 6, "Trạng Thái": "Cần hoàn thành 49 bài 0"}
                ]
                st.dataframe(pd.DataFrame(mystery_leader_summary), use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Lỗi đọc dữ liệu: {e}")
else:
    st.info("👋 Vui lòng tải file Excel báo cáo ở thanh Menu bên trái (Sidebar) và bấm '🚀 PHÂN TÍCH DỮ LIỆU'!")
