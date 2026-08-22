import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
import os
import io
import re
from datetime import datetime

# 1. Cấu hình giao diện Streamlit Enterprise
st.set_page_config(
    page_title="CellphoneS Audit Platform V3.1 - Lần 1 & Lần 2", 
    page_icon="📱", 
    layout="wide"
)

# File lưu trữ dữ liệu riêng cho 2 đợt
APP_VERSION = "3.1.0"
PASS_SCORE = 50
MYSTERY_TARGET = 153

for _k in ["l1_bytes", "l1_name", "l2_bytes", "l2_name"]:
    if _k not in st.session_state:
        st.session_state[_k] = None

# Custom CSS thương hiệu CellphoneS
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .cps-header {
        background: linear-gradient(135deg, #d70018 0%, #8b0000 100%);
        color: white; padding: 20px 25px; border-radius: 12px;
        box-shadow: 0 4px 15px rgba(215, 0, 24, 0.2); margin-bottom: 20px;
    }
    .cps-title {font-size: 26px; font-weight: 800; margin: 0; letter-spacing: 0.5px;}
    .cps-subtitle {font-size: 13px; color: #ffcccc; margin-top: 5px;}
    div[data-testid="stMetric"] {
        background-color: #ffffff; border-left: 5px solid #d70018;
        border-radius: 10px; padding: 15px 18px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    }
    .stTabs [data-baseweb="tab-list"] {gap: 8px; background-color: #ffffff; padding: 8px; border-radius: 10px;}
    .stTabs [aria-selected="true"] {background-color: #d70018 !important; color: white !important; font-weight: bold; border-radius: 8px;}
    .report-title {background-color: #d70018; color: white; padding: 12px; font-weight: bold; text-align: center; font-size: 17px; border-radius: 8px 8px 0 0;}
    .report-sub {background-color: #f8d7da; color: #721c24; padding: 6px; font-style: italic; text-align: center; font-size: 13px; margin-bottom: 20px;}
    div.stButton > button {
        background-color: #d70018 !important; color: white !important; 
        font-weight: bold !important; border-radius: 8px !important; 
        padding: 12px 24px !important; font-size: 15px !important; border: none !important; width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Hàm chuẩn hóa chuỗi / khử dấu Tiếng Việt
def norm(text):
    if pd.isna(text):
        return ""
    text = str(text).replace("\u200b", "").replace("\ufeff", "").strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", text.lower())

def norm_code(value):
    return "" if pd.isna(value) else str(value).strip().upper()

def find_col(columns, aliases):
    aliases_n = [norm(a) for a in aliases]
    for c in columns:
        if norm(c) in aliases_n:
            return c
    for c in columns:
        nc = norm(c)
        if any(a and a in nc for a in aliases_n):
            return c
    return None

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

# Styling Kết quả
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
    elif "Bắt buộc phỏng vấn lần 2" in v or "Bắt buộc trả lần 2" in v:
        return "background-color: #fff3cd; color: #856404; font-weight: bold;"
    return ""

@st.cache_data(show_spinner=False, max_entries=4)
def load_all_sheets(file_bytes):
    bio = io.BytesIO(file_bytes)
    xls = pd.ExcelFile(bio)
    return {name: pd.read_excel(io.BytesIO(file_bytes), sheet_name=name) for name in xls.sheet_names}

def save_upload(uploaded, prefix):
    if uploaded is None:
        return
    st.session_state[f"{prefix}_bytes"] = uploaded.getvalue()
    st.session_state[f"{prefix}_name"] = uploaded.name

def get_round_data(prefix):
    data = st.session_state.get(f"{prefix}_bytes")
    name = st.session_state.get(f"{prefix}_name")
    return (load_all_sheets(data), name) if data else (None, None)

def derive_store_series(df):
    c = find_col(df.columns, ["Mã cửa hàng", "Store Code", "Store ID", "Shop", "Mã CH"])
    if c:
        return df[c].apply(norm_code)
    c_plan = find_col(df.columns, ["Tên Plan", "Plan Name", "Plan"])
    if c_plan:
        return df[c_plan].fillna("").astype(str).str.extract(r"((?:CPS|DTV)-[A-Za-z0-9/.-]+)", expand=False).fillna("").str.upper()
    return pd.Series([""] * len(df), index=df.index)

def compute_progress_metrics(sheets):
    m = {"trade_cps": 0, "trade_dtv": 0, "plus_stores": 0, "mystery_plans": 0, "qc_done": 0, "qc_pending": 0, "rework": 0}
    for sname, df in sheets.items():
        if df.empty:
            continue
        sn = norm(sname)
        stores = derive_store_series(df)
        c_qc = find_col(df.columns, ["QC Status", "Trạng thái QC", "Kết quả QC"])
        if c_qc:
            q = df[c_qc].fillna("").astype(str).str.lower()
            m["qc_done"] += int(q.isin(["done", "pass", "passed", "approved", "ok"]).sum())
            m["qc_pending"] += int(q.str.contains("pending|chờ|cho duyet", regex=True, na=False).sum())
            m["rework"] += int(q.str.contains("rework|reject|refuse|fail|bổ sung|bo sung|ycbs", regex=True, na=False).sum())
        if "trade" in sn and "plus" not in sn:
            valid = stores[stores.ne("")]
            m["trade_cps"] = max(m["trade_cps"], int(valid[valid.str.startswith("CPS-")].nunique()))
            m["trade_dtv"] = max(m["trade_dtv"], int(valid[valid.str.startswith("DTV-")].nunique()))
        if "plus" in sn:
            m["plus_stores"] = max(m["plus_stores"], int(stores[stores.ne("")].nunique()))
        if "mystery" in sn:
            c_plan = find_col(df.columns, ["Tên Plan", "Plan Name", "Plan"])
            if c_plan:
                m["mystery_plans"] = max(m["mystery_plans"], int(df[c_plan].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()))
    return m

def build_leader_summary(sheets, tested_dict):
    rows = []
    for leader in ["Giang Văn Huy", "Ngô Tuấn Cảnh", "Trần Trung Nghĩa", "Vũ Hoài Nam", "Đỗ Quang Tiến"]:
        stores, done, pending, rework = set(), 0, 0, 0
        for _, df in sheets.items():
            c_lead = find_col(df.columns, ["Leader", "Lead", "Leader Phụ Trách", "Quản lý"])
            if not c_lead:
                continue
            mask = df[c_lead].fillna("").astype(str).str.strip().eq(leader)
            if not mask.any():
                continue
            ss = derive_store_series(df.loc[mask])
            stores.update(x for x in ss if x)
            c_qc = find_col(df.columns, ["QC Status", "Trạng thái QC", "Kết quả QC"])
            if c_qc:
                q = df.loc[mask, c_qc].fillna("").astype(str).str.lower()
                done += int(q.isin(["done", "pass", "passed", "approved", "ok"]).sum())
                pending += int(q.str.contains("pending|chờ|cho duyet", regex=True, na=False).sum())
                rework += int(q.str.contains("rework|reject|refuse|fail|bổ sung|bo sung|ycbs", regex=True, na=False).sum())
        tt1 = sum(1 for v in tested_dict.values() if v.get("Leader") == leader)
        rows.append({"Leader": leader, "Shop nhận diện": len(stores), "QC Done rows": done, "QC Pending rows": pending, "Rework rows": rework, "35 NV đã trả bài": tt1})
    return pd.DataFrame(rows)

def build_mystery_summary(sheets):
    frames = []
    for sname, df in sheets.items():
        if "mystery" not in norm(sname) or df.empty:
            continue
        c_plan = find_col(df.columns, ["Tên Plan", "Plan Name", "Plan"])
        c_lead = find_col(df.columns, ["Leader", "Lead", "Leader Phụ Trách"])
        if not c_plan:
            continue
        tmp = pd.DataFrame({"Plan": df[c_plan].fillna("").astype(str).str.strip(), "Leader": df[c_lead].fillna("Chưa gán").astype(str).str.strip() if c_lead else "Chưa gán"})
        tmp = tmp[tmp["Plan"].ne("")].drop_duplicates(["Plan"])
        frames.append(tmp)
    if not frames:
        return pd.DataFrame(columns=["Leader", "Hoàn thành", "Tỷ trọng"])
    x = pd.concat(frames, ignore_index=True).drop_duplicates(["Plan"])
    out = x.groupby("Leader", dropna=False).size().reset_index(name="Hoàn thành")
    total = int(out["Hoàn thành"].sum())
    out["Tỷ trọng"] = out["Hoàn thành"].apply(lambda v: f"{v/total:.1%}" if total else "0%")
    return out.sort_values("Hoàn thành", ascending=False)

# --- SIDEBAR QUẢN TRỊ MÀN HÌNH ĐỘC LẬP LẦN 1 & LẦN 2 ---
with st.sidebar:
    st.markdown("### 🖥️ CHỌN MÀN HÌNH ĐIỀU HÀNH")
    
    view_mode = st.radio(
        "Chế độ hiển thị Giao diện:",
        [
            "📌 MÀN HÌNH LẦN 1", 
            "📌 MÀN HÌNH LẦN 2", 
            "📊 TỔNG HỢP SO SÁNH 2 LẦN (CEO VIEW)"
        ],
        index=0
    )
    
    st.write("---")
    st.markdown("### ⚙️ QUẢN TRỊ NẠP FILE MỚI")
    
    up_l1 = st.file_uploader("Nạp Excel Raw Data (LẦN 1):", type=["xlsx", "xls"], key="up1")
    if up_l1 is not None:
        save_upload(up_l1, "l1")
        st.success(f"✅ L1 đã refresh: {up_l1.name}")

    up_l2 = st.file_uploader("Nạp Excel Raw Data (LẦN 2):", type=["xlsx", "xls"], key="up2")
    if up_l2 is not None:
        save_upload(up_l2, "l2")
        st.success(f"✅ L2 đã refresh: {up_l2.name}")

    st.write("---")
    st.markdown("### 🔍 BỘ LỌC CHI TIẾT")
    selected_region = st.selectbox("🌐 Chọn Miền:", ["Tất cả", "Miền Bắc", "Miền Nam"])
    selected_leader = st.selectbox("👤 Chọn Leader Phụ Trách:", ["Tất cả", "Giang Văn Huy", "Ngô Tuấn Cảnh", "Trần Trung Nghĩa", "Vũ Hoài Nam", "Đỗ Quang Tiến"])

# HEADER ENTERPRISE THEO MÀN HÌNH ĐANG CHỌN
header_sub = "Đang hiển thị Màn hình Lần 1" if "LẦN 1" in view_mode else ("Đang hiển thị Màn hình Lần 2" if "LẦN 2" in view_mode else "Màn hình So Sánh 2 Lần dành cho CEO")
st.markdown(f"""
    <div class="cps-header">
        <div class="cps-title">📱 CELLPHONES ENTERPRISE AUDIT — {view_mode}</div>
        <div class="cps-subtitle">{header_sub} (Session-safe • v3.1.0)</div>
    </div>
""", unsafe_allow_html=True)

target_key = "l1" if "LẦN 1" in view_mode else ("l2" if "LẦN 2" in view_mode else None)
target_sheets, target_file_name = get_round_data(target_key) if target_key else (None, None)

if view_mode == "📊 TỔNG HỢP SO SÁNH 2 LẦN (CEO VIEW)":
    sheets_l1, name_l1 = get_round_data("l1")
    sheets_l2, name_l2 = get_round_data("l2")
    has_l1 = sheets_l1 is not None
    has_l2 = sheets_l2 is not None
    col1, col2 = st.columns(2)
    with col1:
        st.info("📌 **LẦN 1:** " + (f"🟢 {name_l1}" if has_l1 else "🔴 Chưa nạp file"))
    with col2:
        st.info("📌 **LẦN 2:** " + (f"🟢 {name_l2}" if has_l2 else "🔴 Chưa nạp file"))
    if has_l1 or has_l2:
        p1 = compute_progress_metrics(sheets_l1) if has_l1 else {}
        p2 = compute_progress_metrics(sheets_l2) if has_l2 else {}
        rows = []
        labels = [("trade_cps","Trade Audit CPS"),("trade_dtv","Trade Audit DTV"),("plus_stores","Audit Plus Store"),("mystery_plans","Mystery unique Plan"),("qc_done","QC Done rows"),("rework","Rework/Reject rows")]
        for key, label in labels:
            v1, v2 = p1.get(key,0), p2.get(key,0)
            rows.append({"Hạng mục":label,"Lần 1":v1,"Lần 2":v2,"Chênh lệch L2-L1":v2-v1})
        ceo_df = pd.DataFrame(rows)
        st.dataframe(ceo_df, use_container_width=True, hide_index=True)
        st.plotly_chart(px.bar(ceo_df, x="Hạng mục", y=["Lần 1","Lần 2"], barmode="group", title="So sánh L1 vs L2 từ dữ liệu thực"), use_container_width=True)
    else:
        st.warning("Chưa có dữ liệu L1/L2 để so sánh.")

elif target_sheets is not None:

    try:
        sheets_data = target_sheets

        search_query = st.text_input("🔎 TRA CỨU NHANH (Nhập Mã NV / Tên Nhân Sự / Mã Cửa Hàng):", "").strip()

        # 1. ĐỐI SOÁT 35 NV MASTER (SỬA LỖI ĐỂ TÍNH ĐÚNG KẾT QUẢ VÀ TỰ ĐỘNG HIGHLIGHT PV LẦN 2)
        tested_dict = {}
        for sheet_name, df in sheets_data.items():
            c_name = find_col(df.columns, ['Nhân sự', 'Tên nhân viên', 'Họ và tên', 'Tên NV'])
            c_score = find_col(df.columns, ['Điểm trả bài', 'Score', 'Thực đạt'])
            c_status = next((c for c in df.columns if any(k in norm(c) for k in ['qcstatus', 'trangthai', 'status'])), None)
            c_date = next((c for c in df.columns if any(k in norm(c) for k in ['ngay', 'date', 'thoigian'])), None)

            if c_name or c_score:
                for _, r in df.iterrows():
                    v_name = norm(r[c_name]) if c_name and pd.notna(r[c_name]) else ""
                    v_score_raw = r[c_score] if c_score and pd.notna(r[c_score]) else None
                    v_st = str(r[c_status]).strip() if c_status and pd.notna(r[c_status]) else ""
                    v_dt = str(r[c_date]).strip() if c_date and pd.notna(r[c_date]) else "None"

                    if v_score_raw is None and v_st == "": continue

                    try: v_score = float(v_score_raw) if v_score_raw is not None else None
                    except: v_score = None

                    for item in TARGET_35_NV_MASTER:
                        if selected_leader != "Tất cả" and item["Leader"] != selected_leader: continue
                        match_name = (norm(item["Tên"]) == v_name) if v_name else False

                        if match_name:
                            # Sửa chuẩn quy tắc điểm >= 50
                            if v_score is not None:
                                eval_text = "ĐẠT" if v_score >= PASS_SCORE else "KHÔNG ĐẠT"
                            else:
                                eval_text = "CHƯA CÓ ĐIỂM"

                            if eval_text == "ĐẠT":
                                note_pv2 = "Đã hoàn thành"
                            elif eval_text == "KHÔNG ĐẠT":
                                note_pv2 = "Bắt buộc trả/phỏng vấn lại"
                            else:
                                note_pv2 = "Cần xác minh điểm - không suy từ QC Status"

                            tested_dict[item["Tên"]] = {
                                "Leader": item["Leader"],
                                "Điểm trả bài": round(v_score, 2) if v_score is not None else "N/A",
                                "Đánh giá": eval_text,
                                "Ghi chú PV2": note_pv2,
                                "QC Status": v_st if v_st else "done",
                                "Ngày thực hiện": v_dt if v_dt != "nan" else "None"
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
                    m_name = (norm(item94["Tên"]) == v_name) if v_name else False
                    
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
        progress = compute_progress_metrics(sheets_data)
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Trade CPS Stores", progress["trade_cps"])
        m2.metric("Trade DTV Stores", progress["trade_dtv"])
        m3.metric("Plus Stores", progress["plus_stores"])
        m4.metric("Mystery", f'{progress["mystery_plans"]} / {MYSTERY_TARGET}')
        m5.metric("35 NV đã có dữ liệu", f"{len(tested_dict)} / 35")
        m6.metric("Rework / Reject", progress["rework"])

        st.divider()

        # --- TABS DỰ ÁN ENTERPRISE ---
        t_pivot, t_35nv, t_94esim, t_plus_summary, t_rework, t_mystery = st.tabs([
            "📊 TỔNG HỢP LEADER", 
            "🎤 35 NV TRẢ BÀI (TT1)", 
            "📱 94 NV KHÔNG ĐẠT ESIM L1 (LẦN 2)",
            "➕ BẢNG TỔNG HỢP AUDIT PLUS",
            "⚠️ YÊU CẦU BỔ SUNG (REWORK)", 
            "🕵️ MYSTERY SHOOPER (153 KỊCH BẢN)"
        ])

        # --- TAB 1: TỔNG HỢP LEADER (CẬP NHẬT CHUẨN SỐ LƯỢNG GỐC THEO TỪNG LEADER) ---
        with t_pivot:
            st.subheader(f"📌 Tiến độ & chất lượng theo Leader ({view_mode})")
            leader_df = build_leader_summary(sheets_data, tested_dict)
            st.dataframe(leader_df, use_container_width=True, hide_index=True)
            if not leader_df.empty:
                fig_lead = px.bar(leader_df, x="Leader", y=["QC Done rows", "QC Pending rows", "Rework rows"], barmode="stack", title="QC workload theo Leader")
                st.plotly_chart(fig_lead, use_container_width=True)

        # --- TAB 2: 35 NV TRẢ BÀI CÓ HIGHLIGHT PHỎNG VẤN LẦN 2 ---
        with t_35nv:
            st.markdown(f"<div class='report-title'>CPS — 35 NHÂN SỰ BẮT BUỘC TRẢ BÀI ({view_mode.upper()})</div>", unsafe_allow_html=True)

            count_pass_35 = sum(1 for v in tested_dict.values() if v["Đánh giá"] == "ĐẠT")
            count_fail_35 = sum(1 for v in tested_dict.values() if v["Đánh giá"] == "KHÔNG ĐẠT")
            count_unknown_score_35 = sum(1 for v in tested_dict.values() if v["Đánh giá"] == "CHƯA CÓ ĐIỂM")
            count_not_35 = 35 - len(tested_dict)

            df_kpi = pd.DataFrame([
                {"Chỉ số": "Tổng NV bắt buộc", "Kết quả": 35},
                {"Chỉ số": "Đã có dữ liệu trả bài", "Kết quả": len(tested_dict)},
                {"Chỉ số": "ĐẠT (>=50 điểm)", "Kết quả": count_pass_35},
                {"Chỉ số": "KHÔNG ĐẠT (<50 điểm)", "Kết quả": count_fail_35},
                {"Chỉ số": "CHƯA CÓ ĐIỂM (cần xác minh)", "Kết quả": count_unknown_score_35},
                {"Chỉ số": "CẦN ACTION / PV L2", "Kết quả": count_not_35 + count_fail_35 + count_unknown_score_35}
            ])
            
            c_kpi, _ = st.columns([1, 1])
            with c_kpi: st.dataframe(df_kpi, use_container_width=True, hide_index=True)
            st.write("---")

            res_35 = []
            for item in TARGET_35_NV_MASTER:
                if selected_leader != "Tất cả" and item["Leader"] != selected_leader: continue
                nv_name = item["Tên"]
                
                if nv_name in tested_dict:
                    info = tested_dict[nv_name]
                    note_pv = info["Ghi chú PV2"]
                else:
                    info = {"Điểm trả bài": "➖", "Đánh giá": "CHƯA TRẢ BÀI", "QC Status": "None", "Ngày thực hiện": "None"}
                    note_pv = "Bắt buộc phỏng vấn lần 2"

                row_data = {
                    "Nhân sự": nv_name,
                    "Mã cửa hàng": item["Mã cửa hàng"],
                    "Leader": item["Leader"],
                    "Điểm trả bài": info["Điểm trả bài"],
                    "Đánh giá": info["Đánh giá"],
                    "Ghi chú PV Lần 2": note_pv,
                    "QC Status": info["QC Status"],
                    "Ngày thực hiện": info["Ngày thực hiện"]
                }

                if search_query:
                    match_q = norm(search_query)
                    if match_q not in norm(nv_name) and match_q not in norm(item["Mã cửa hàng"]):
                        continue

                res_35.append(row_data)

            df_res_35 = pd.DataFrame(res_35)
            st.dataframe(df_res_35.style.map(style_evaluation, subset=["Đánh giá"]).map(style_note_35, subset=["Ghi chú PV Lần 2"]), use_container_width=True, height=450, hide_index=True)

        # --- TAB 3: 94 NV KHÔNG ĐẠT ESIM L1 (ĐO LƯỜNG LẦN 2) ---
        with t_94esim:
            st.markdown(f"<div class='report-title'>CPS — DANH SÁCH 94 NHÂN SỰ KHÔNG ĐẠT ESIM L1 ({view_mode.upper()})</div>", unsafe_allow_html=True)

            count_has_l2 = len(esim_l2_dict)
            count_pass_l2 = sum(1 for v in esim_l2_dict.values() if v["Kết quả Lần 2"] == "ĐẠT")
            count_fail_l2 = sum(1 for v in esim_l2_dict.values() if v["Kết quả Lần 2"] == "CHƯA ĐẠT")
            count_not_l2 = 94 - count_has_l2

            df_kpi_94 = pd.DataFrame([
                {"Chỉ số Đánh Giá": "Tổng NV Không đạt Esim L1", "Số lượng": 94},
                {"Chỉ số Đánh Giá": "Đã có dữ liệu Chấm Lần 2", "Số lượng": count_has_l2},
                {"Chỉ số Đánh Giá": "ĐẠT Lần 2 (>=50 điểm)", "Số lượng": count_pass_l2},
                {"Chỉ số Đánh Giá": "CHƯA ĐẠT Lần 2 (<50 điểm)", "Số lượng": count_fail_l2},
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

                matched_35 = next((t for t in TARGET_35_NV_MASTER if norm(t["Tên"]) == name_norm), None)
                if matched_35:
                    nv_35_name = matched_35["Tên"]
                    if nv_35_name in tested_dict:
                        eval_l1 = tested_dict[nv_35_name]["Đánh giá"]
                        note_35 = "Đã trả bài (ĐẠT)" if eval_l1 == "ĐẠT" else "Đã trả bài (Không đạt)"
                    else:
                        note_35 = "Bắt buộc phỏng vấn lần 2"
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

        # --- TAB 4: BẢNG AUDIT PLUS TỔNG QUAN CHUẨN CẤU TRÚC CODE CỦI ---
        with t_plus_summary:
            st.subheader(f"➕ Bảng Tổng Hợp Tiến Độ Audit Plus Theo Cửa Hàng ({view_mode})")
            s_plus_key = next((s for s in sheets_data.keys() if "plus" in norm(s)), None)
            if s_plus_key:
                st.dataframe(sheets_data[s_plus_key], use_container_width=True)
            else:
                st.warning("Không tìm thấy sheet Audit Plus trong file hiện tại. Không hiển thị dữ liệu mẫu giả.")

        # --- TAB 5: YÊU CẦU BỔ SUNG ---
        with t_rework:
            st.subheader(f"⚠️ Danh Sách Cửa Hàng QC Note Yêu Cầu Bổ Sung / Lỗi Refuse ({view_mode})")
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

        # --- TAB 6: MYSTERY SHOPPER ĐẾM THEO TỔNG 153 KỊCH BẢN CHUẨN ---
        with t_mystery:
            st.subheader("🕵️ Báo Cáo Tiến Độ Mystery Shopper (Tổng 153 Kịch Bản Đo Lường)")
            
            mystery_df = build_mystery_summary(sheets_data)
            if mystery_df.empty:
                st.warning("Không nhận diện được dữ liệu Mystery trong file.")
            else:
                total_mystery = int(mystery_df["Hoàn thành"].sum())
                c1, c2 = st.columns(2)
                c1.metric("Đã nhận diện", total_mystery)
                c2.metric("Target", MYSTERY_TARGET)
                st.progress(min(total_mystery / MYSTERY_TARGET, 1.0))
                st.dataframe(mystery_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Lỗi đọc dữ liệu: {e}")
else:
    st.info("👋 Chưa tìm thấy dữ liệu báo cáo cho màn hình này. Vui lòng nạp file Excel ở thanh Sidebar bên trái!")
