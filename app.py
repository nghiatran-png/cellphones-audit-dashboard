
import io
import re
import unicodedata
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="CellphoneS Audit Platform V3.3",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_VERSION="3.5.0"
PASS_SCORE=50
MYSTERY_TARGET=153

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

# ---------------- Normalize ----------------
def norm(v):
    if pd.isna(v): return ""
    s=str(v).replace("\u200b","").replace("\ufeff","").strip()
    s=unicodedata.normalize("NFD",s)
    s="".join(c for c in s if unicodedata.category(c)!="Mn")
    return re.sub(r"\s+"," ",s.lower()).strip()

def norm_code(v):
    return "" if pd.isna(v) else str(v).strip().upper()

def classify_qc(v):
    s=norm(v)
    if not s or s in {"nan","none"}: return "NONE"
    if any(k in s for k in ["rework","ycbs","yeu cau bo sung","bo sung","thieu"]): return "REWORK"
    if any(k in s for k in ["reject","refused","refuse","fail","failed","khong dat","invalid"]): return "REJECT"
    if any(k in s for k in ["pending_review","pending review"]): return "PENDING_REVIEW"
    if any(k in s for k in ["pending","cho duyet","waiting"]): return "PENDING"
    if s in {"done","pass","passed","approved","approve","ok","dat"}: return "DONE"
    return "UNKNOWN"

def rounded_score(v):
    """Điểm dùng để đánh giá và export Excel. 49.99 -> 50."""
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None

def eval_score(v):
    rounded = rounded_score(v)
    if rounded is None:
        return "CHƯA CÓ ĐIỂM"
    return "ĐẠT" if rounded >= PASS_SCORE else "KHÔNG ĐẠT"

# ---------------- Session/file loading ----------------
for k in ["l1_bytes","l1_name","l2_bytes","l2_name"]:
    if k not in st.session_state: st.session_state[k]=None

USECOLS={
    "Mystery Audit":["Tên Plan","Chấm","Hệ thống","Mã cửa hàng","Tên Leader","Tên nhân viên thực hiện","Ngày update","Status Plan","QC Status","Ngày thực hiện","Hạng mục"],
    "Trade Audit":["Tên Plan","Chấm","Hệ thống","Mã cửa hàng","Tên Leader","Tên nhân viên thực hiện","Ngày update","Status Plan","QC Status","Ngày thực hiện","Hạng mục","Result","Category","Sub-category","KPI","QC note"],
    "Trade Audit Plus":["Tên Plan","Chấm","Hệ thống","Mã cửa hàng","Tên Leader","Tên nhân viên thực hiện","Ngày update","Status Plan","QC Status","Ngày thực hiện","MSNV","Mã câu hỏi","Câu hỏi chính","Câu trả lời","Trả lời ngay","Trả lời Phụ","Trả lời có tài liệu","Có xem tài liệu","Thang điểm","Thực đạt","QC note"],
}

@st.cache_data(show_spinner=False,max_entries=4)
def load_report(file_bytes):
    xls=pd.ExcelFile(io.BytesIO(file_bytes))
    out={}
    for s in xls.sheet_names:
        if s not in USECOLS: 
            continue
        header=pd.read_excel(io.BytesIO(file_bytes),sheet_name=s,nrows=0).columns.tolist()
        cols=[c for c in USECOLS[s] if c in header]
        out[s]=pd.read_excel(io.BytesIO(file_bytes),sheet_name=s,usecols=cols)
    return out

def save_upload(uploaded,prefix):
    if uploaded:
        st.session_state[f"{prefix}_bytes"]=uploaded.getvalue()
        st.session_state[f"{prefix}_name"]=uploaded.name

def get_round(prefix):
    b=st.session_state.get(f"{prefix}_bytes")
    return (load_report(b),st.session_state.get(f"{prefix}_name")) if b else (None,None)

# ---------------- Round filtering ----------------
def filter_round(df,label):
    if df is None or df.empty or "Chấm" not in df.columns: return df
    wanted=norm(label)
    x=df[df["Chấm"].apply(norm).eq(wanted)]
    return x.copy()

def plan_level(df):
    if df is None or df.empty or "Tên Plan" not in df.columns:
        return pd.DataFrame()
    x=df.copy()
    if "Ngày update" in x.columns:
        x["_dt"]=pd.to_datetime(x["Ngày update"],errors="coerce",dayfirst=True)
        x=x.sort_values("_dt")
    return x.drop_duplicates("Tên Plan",keep="last").copy()


def get_sheet_flexible(sheets, keywords):
    """Tìm sheet theo từ khóa, không phụ thuộc tên sheet tuyệt đối."""
    if not sheets:
        return pd.DataFrame()
    keys = [norm(k) for k in keywords]
    # exact-ish priority
    for name, df in sheets.items():
        n = norm(name)
        if all(k in n for k in keys):
            return df.copy()
    return pd.DataFrame()

def mystery_scenario_series(df):
    """
    Ưu tiên Hạng mục của Mystery.
    Nếu thiếu, suy từ Tên Plan.
    """
    if df is None or df.empty:
        return pd.Series(dtype=str)
    if "Hạng mục" in df.columns:
        s = df["Hạng mục"].fillna("").astype(str).str.strip()
        if s.ne("").any():
            return s
    plan = df["Tên Plan"].fillna("").astype(str) if "Tên Plan" in df.columns else pd.Series("", index=df.index)
    def parse_scenario(v):
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
        return str(v).strip()
    return plan.apply(parse_scenario)

# ---------------- Plus interview engine ----------------
FLAG_COLS=["Trả lời ngay","Trả lời Phụ","Trả lời có tài liệu","Có xem tài liệu"]

def boolish(v):
    if pd.isna(v): return False
    if isinstance(v,bool): return v
    if isinstance(v,(int,float)): return bool(v)
    return norm(v) in {"true","1","yes","y","x","co","ok"}

def plus_interviews(plus_df):
    if plus_df is None or plus_df.empty: return pd.DataFrame()
    x=plus_df.copy()
    if "Mã câu hỏi" not in x.columns or "Tên Plan" not in x.columns: return pd.DataFrame()

    # score per plan
    x["_answered"]=False
    for c in FLAG_COLS:
        if c in x.columns:
            x["_answered"]=x["_answered"] | x[c].apply(boolish)

    if "Thực đạt" in x.columns and pd.to_numeric(x["Thực đạt"],errors="coerce").notna().any():
        score=x.groupby("Tên Plan")["Thực đạt"].apply(lambda s: pd.to_numeric(s,errors="coerce").sum(min_count=1))
    elif "Thang điểm" in x.columns:
        pts=pd.to_numeric(x["Thang điểm"],errors="coerce").fillna(0)
        x["_pts"]=pts.where(x["_answered"],0)
        score=x.groupby("Tên Plan")["_pts"].sum()
    else:
        score=pd.Series(dtype=float)

    tt1=x[x["Mã câu hỏi"].astype(str).str.upper().eq("TT1")].copy()
    if tt1.empty: return pd.DataFrame()

    out=pd.DataFrame({
        "plan_name":tt1["Tên Plan"].astype(str).str.strip(),
        "store_code":tt1["Mã cửa hàng"].apply(norm_code) if "Mã cửa hàng" in tt1.columns else "",
        "leader":tt1["Tên Leader"].fillna("").astype(str).str.strip() if "Tên Leader" in tt1.columns else "",
        "field_name":tt1["Tên nhân viên thực hiện"].fillna("").astype(str).str.strip() if "Tên nhân viên thực hiện" in tt1.columns else "",
        "employee_id":tt1["MSNV"].fillna("").astype(str).str.strip() if "MSNV" in tt1.columns else "",
        "employee_name":tt1["Câu trả lời"].fillna("").astype(str).str.strip() if "Câu trả lời" in tt1.columns else "",
        "qc_status":tt1["QC Status"].apply(classify_qc) if "QC Status" in tt1.columns else "NONE",
        "status_plan":tt1["Status Plan"].fillna("").astype(str).str.strip() if "Status Plan" in tt1.columns else "",
        "updated_at":pd.to_datetime(tt1["Ngày update"],errors="coerce",dayfirst=True) if "Ngày update" in tt1.columns else pd.NaT,
    })
    out["score"]=out["plan_name"].map(score)
    out["evaluation"]=out["score"].apply(eval_score)
    out=out[out["employee_name"].apply(norm).ne("")]
    return out.drop_duplicates("plan_name",keep="last")

# ---------------- 35 / 94 matching ----------------
def match35(interviews):
    rows=[]
    x=interviews.copy()
    if not x.empty:
        x["_name"]=x["employee_name"].apply(norm)
        x["_store"]=x["store_code"].apply(norm_code)
    for m in TARGET_35_NV_MASTER:
        cand=pd.DataFrame()
        if not x.empty:
            cand=x[(x["_name"]==norm(m["Tên"])) & (x["_store"]==norm_code(m["Mã cửa hàng"]))]
            if cand.empty and "..." in m["Mã cửa hàng"]:
                cand=x[x["_name"]==norm(m["Tên"])]
        if cand.empty:
            rows.append({"Nhân sự":m["Tên"],"Mã cửa hàng":m["Mã cửa hàng"],"Leader":m["Leader"],
                         "Điểm gốc":pd.NA,"Điểm trả bài":pd.NA,"Đánh giá":"CHƯA TRẢ BÀI",
                         "QC Status":"NONE","Field":"","Ngày thực hiện":pd.NaT})
        else:
            r=cand.sort_values("updated_at").iloc[-1]
            raw_score = r["score"]
            rows.append({"Nhân sự":m["Tên"],"Mã cửa hàng":m["Mã cửa hàng"],"Leader":m["Leader"],
                         "Điểm gốc":raw_score,"Điểm trả bài":rounded_score(raw_score),
                         "Đánh giá":eval_score(raw_score),"QC Status":r["qc_status"],
                         "Field":r["field_name"],"Ngày thực hiện":r["updated_at"]})
    return pd.DataFrame(rows)

def match94(interviews):
    rows=[]
    x=interviews.copy()
    if not x.empty:
        x["_id"]=x["employee_id"].apply(lambda v:norm(str(v).lstrip("0")))
        x["_name"]=x["employee_name"].apply(norm)
        x["_store"]=x["store_code"].apply(norm_code)
    for m in TARGET_94_ESIM_L1:
        cand=pd.DataFrame()
        if not x.empty:
            target_id=norm(str(m["MSNV"]).lstrip("0"))
            cand=x[x["_id"]==target_id]
            if cand.empty:
                cand=x[(x["_name"]==norm(m["Tên"])) & (x["_store"]==norm_code(m["Shop"]))]
        if cand.empty:
            rows.append({"STT":m["STT"],"MSNV":m["MSNV"],"Họ và Tên":m["Tên"],"Shop":m["Shop"],"Miền":m["Miền"],
                         "Leader":m["Leader"],"Field":"","Điểm L2 gốc":pd.NA,"Điểm L2":pd.NA,
                         "Kết quả L2":"BẮT BUỘC TRẢ LẦN 2"})
        else:
            r=cand.sort_values("updated_at").iloc[-1]
            raw_score = r["score"]
            rows.append({"STT":m["STT"],"MSNV":m["MSNV"],"Họ và Tên":m["Tên"],"Shop":m["Shop"],"Miền":m["Miền"],
                         "Leader":m["Leader"],"Field":r["field_name"],
                         "Điểm L2 gốc":raw_score,"Điểm L2":rounded_score(raw_score),
                         "Kết quả L2":eval_score(raw_score)})
    return pd.DataFrame(rows)

# ---------------- Plan-level metrics ----------------
def metrics(sheets,round_label):
    # Trade + Plus theo đúng vòng.
    trade_all = get_sheet_flexible(sheets, ["trade", "audit"])
    plus_all = get_sheet_flexible(sheets, ["trade", "audit", "plus"])
    # Mystery là luồng KPI 153 riêng, luôn lấy data mới nhất toàn sheet,
    # KHÔNG filter theo L1/L2.
    mystery = get_sheet_flexible(sheets, ["mystery"])

    # tránh lấy nhầm Trade Audit Plus cho Trade Audit
    if not trade_all.empty and "plus" in norm(next((n for n in sheets if sheets[n] is trade_all), "")):
        trade_all = pd.DataFrame()

    # Chọn Trade Audit chính xác hơn
    for name, df in sheets.items():
        n = norm(name)
        if "trade audit" in n and "plus" not in n:
            trade_all = df.copy()
            break
    for name, df in sheets.items():
        n = norm(name)
        if "trade audit plus" in n or ("trade" in n and "plus" in n):
            plus_all = df.copy()
            break
    for name, df in sheets.items():
        if "mystery" in norm(name):
            mystery = df.copy()
            break

    trade = filter_round(trade_all, round_label)
    plus = filter_round(plus_all, round_label)

    tplan = plan_level(trade)
    pplan = plan_level(plus)
    mplan = plan_level(mystery)
    interviews = plus_interviews(plus)

    def qc_counts(pl):
        if pl.empty or "QC Status" not in pl.columns:
            return {"DONE":0,"PENDING":0,"PENDING_REVIEW":0,"REJECT":0,"REWORK":0}
        q=pl["QC Status"].apply(classify_qc)
        return {k:int((q==k).sum()) for k in ["DONE","PENDING","PENDING_REVIEW","REJECT","REWORK"]}

    def field_done(pl):
        if pl.empty or "Status Plan" not in pl.columns:
            return 0
        return int(pl["Status Plan"].apply(norm).eq("done").sum())

    system = tplan["Hệ thống"].fillna("").astype(str).str.upper() if not tplan.empty and "Hệ thống" in tplan.columns else pd.Series(dtype=str)
    cps_stores = tplan.loc[system.eq("CPS"),"Mã cửa hàng"].nunique() if len(system) else 0
    dtv_stores = tplan.loc[system.eq("DTV"),"Mã cửa hàng"].nunique() if len(system) else 0

    # L2: loại DTV khỏi Trade KPI vận hành
    if round_label == "Lần 2" and not tplan.empty and "Hệ thống" in tplan.columns:
        tplan_cps = tplan[tplan["Hệ thống"].fillna("").astype(str).str.upper().eq("CPS")].copy()
    else:
        tplan_cps = tplan.copy()

    return {
        "trade_raw":trade,"plus_raw":plus,"mystery_raw":mystery,
        "trade_plan":tplan_cps,"trade_plan_all":tplan,
        "plus_plan":pplan,"mystery_plan":mplan,"interviews":interviews,
        "trade_cps_stores":int(cps_stores),
        "trade_dtv_stores":0 if round_label=="Lần 2" else int(dtv_stores),
        "trade_plans":len(tplan_cps),"plus_plans":len(pplan),"mystery_plans":len(mplan),
        "plus_stores":int(pplan["Mã cửa hàng"].nunique()) if not pplan.empty and "Mã cửa hàng" in pplan.columns else 0,
        "trade_field_done":field_done(tplan_cps),"plus_field_done":field_done(pplan),"mystery_field_done":field_done(mplan),
        "trade_qc":qc_counts(tplan_cps),"plus_qc":qc_counts(pplan),"mystery_qc":qc_counts(mplan),
    }

def mystery_by_leader_scenario(m):
    x = m["mystery_plan"].copy()
    if x.empty:
        return pd.DataFrame(columns=["Leader","Kịch bản","Tổng Plan","Field Done","QC Done","QC Pending","Chưa hoàn thành"])
    x["Leader"] = x["Tên Leader"].fillna("Chưa gán").astype(str).str.strip() if "Tên Leader" in x.columns else "Chưa gán"
    x["Kịch bản"] = mystery_scenario_series(x)
    x["_field_done"] = x["Status Plan"].apply(norm).eq("done") if "Status Plan" in x.columns else False
    x["_qc"] = x["QC Status"].apply(classify_qc) if "QC Status" in x.columns else "NONE"
    g = x.groupby(["Leader","Kịch bản"], dropna=False).agg(
        Tổng_Plan=("Tên Plan","nunique"),
        Field_Done=("_field_done","sum"),
        QC_Done=("_qc",lambda s:int((s=="DONE").sum())),
        QC_Pending=("_qc",lambda s:int(s.isin(["PENDING","PENDING_REVIEW"]).sum())),
    ).reset_index()
    g["Chưa hoàn thành"] = g["Tổng_Plan"] - g["QC_Done"]
    return g.rename(columns={"Tổng_Plan":"Tổng Plan","Field_Done":"Field Done","QC_Done":"QC Done","QC_Pending":"QC Pending"})

def store_completion(m, round_label):
    """
    1 dòng / cửa hàng:
    - Trade: all existing L2 CPS plans Field+QC done
    - Plus: all existing L2 plans Field+QC done
    - Mystery: all existing Mystery plans Field+QC done
    Không giả định plan không có trong raw là hoàn thành.
    """
    modules = []
    for mod, key in [("Trade","trade_plan"),("Plus","plus_plan"),("Mystery","mystery_plan")]:
        x = m[key].copy()
        if x.empty or "Mã cửa hàng" not in x.columns:
            continue
        x = x[x["Mã cửa hàng"].fillna("").astype(str).str.strip().ne("")]
        if x.empty:
            continue
        x["_field_done"] = x["Status Plan"].apply(norm).eq("done") if "Status Plan" in x.columns else False
        x["_qc_done"] = x["QC Status"].apply(classify_qc).eq("DONE") if "QC Status" in x.columns else False
        x["Leader"] = x["Tên Leader"].fillna("").astype(str).str.strip() if "Tên Leader" in x.columns else ""
        g = x.groupby(["Mã cửa hàng","Leader"], dropna=False).agg(
            Plans=("Tên Plan","nunique"),
            Field_Done=("_field_done","sum"),
            QC_Done=("_qc_done","sum"),
        ).reset_index()
        g["Module"] = mod
        modules.append(g)

    if not modules:
        return pd.DataFrame()

    allm = pd.concat(modules, ignore_index=True)
    stores = sorted(allm["Mã cửa hàng"].unique())
    rows = []
    for store in stores:
        s = allm[allm["Mã cửa hàng"]==store]
        leader = next((v for v in s["Leader"] if str(v).strip()), "")
        row = {"Mã cửa hàng":store,"Leader":leader}
        overall_parts=[]
        for mod in ["Trade","Plus","Mystery"]:
            z=s[s["Module"]==mod]
            if z.empty:
                row[f"{mod}"] = "Chưa có data"
                row[f"{mod} Plan"] = 0
                continue
            plans=int(z["Plans"].sum())
            fd=int(z["Field_Done"].sum())
            qd=int(z["QC_Done"].sum())
            done = plans>0 and fd>=plans and qd>=plans
            row[f"{mod}"] = "✅ Hoàn thành" if done else "⏳ Chưa hoàn thành"
            row[f"{mod} Plan"] = plans
            overall_parts.append(done)
        row["Tổng trạng thái"] = "✅ HOÀN THÀNH" if overall_parts and all(overall_parts) else "⏳ CHƯA HOÀN THÀNH"
        rows.append(row)
    return pd.DataFrame(rows)

def leader_summary(m):
    frames=[]
    for label,key in [("Trade","trade_plan"),("Plus","plus_plan"),("Mystery","mystery_plan")]:
        x=m[key]
        if x.empty: continue
        y=x.copy()
        y["Leader"]=y["Tên Leader"].fillna("Chưa gán").astype(str).str.strip() if "Tên Leader" in y.columns else "Chưa gán"
        y["QC"]=y["QC Status"].apply(classify_qc) if "QC Status" in y.columns else "NONE"
        y["Nghiệp vụ"]=label
        frames.append(y[["Tên Plan","Mã cửa hàng","Leader","QC","Nghiệp vụ"]])
    if not frames:return pd.DataFrame()
    z=pd.concat(frames,ignore_index=True).drop_duplicates(["Tên Plan","Nghiệp vụ"])
    return z.groupby("Leader").agg(
        Shop=("Mã cửa hàng","nunique"),
        Plan=("Tên Plan","nunique"),
        QC_Done=("QC",lambda s:int((s=="DONE").sum())),
        QC_Pending=("QC",lambda s:int(s.isin(["PENDING","PENDING_REVIEW"]).sum())),
        QC_Reject_Rework=("QC",lambda s:int(s.isin(["REJECT","REWORK"]).sum()))
    ).reset_index()


def dataframe_to_excel_bytes(df, sheet_name):
    """
    Export đúng dữ liệu đang hiển thị.
    Không dùng formula Excel để tự đánh giá lại -> tránh 49.99 bị đổi thành KHÔNG ĐẠT.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        wb = writer.book
        ws = writer.sheets[sheet_name]

        header_fmt = wb.add_format({
            "bold": True, "font_color": "white", "bg_color": "#D70018",
            "border": 1, "align": "center", "valign": "vcenter"
        })
        pass_fmt = wb.add_format({"bg_color": "#D1E7DD", "font_color": "#0F5132", "bold": True})
        fail_fmt = wb.add_format({"bg_color": "#F8D7DA", "font_color": "#842029", "bold": True})
        wait_fmt = wb.add_format({"bg_color": "#FFF3CD", "font_color": "#664D03", "bold": True})

        for col_num, col_name in enumerate(df.columns):
            ws.write(0, col_num, col_name, header_fmt)
            width = min(max(len(str(col_name)) + 2,
                            int(df[col_name].astype(str).map(len).quantile(.90)) + 2 if len(df) else 12), 42)
            ws.set_column(col_num, col_num, width)

        # Highlight kết quả nếu có
        for candidate in ["Kết quả L2", "Đánh giá"]:
            if candidate in df.columns:
                c = df.columns.get_loc(candidate)
                first_row, last_row = 1, max(len(df), 1)
                ws.conditional_format(first_row, c, last_row, c, {
                    "type": "text", "criteria": "containing", "value": "ĐẠT", "format": pass_fmt
                })
                ws.conditional_format(first_row, c, last_row, c, {
                    "type": "text", "criteria": "containing", "value": "KHÔNG ĐẠT", "format": fail_fmt
                })
                ws.conditional_format(first_row, c, last_row, c, {
                    "type": "text", "criteria": "containing", "value": "BẮT BUỘC", "format": wait_fmt
                })

        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, len(df), len(df.columns)-1)

    return output.getvalue()


# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown("### 🖥️ MÀN HÌNH ĐIỀU HÀNH")
    view=st.radio("Chế độ",["📌 LẦN 1","📌 LẦN 2","📊 CEO VIEW"],index=1)
    st.divider()
    u1=st.file_uploader("Raw Data Lần 1",type=["xlsx","xls"],key="l1")
    if u1: save_upload(u1,"l1"); st.success("Đã nạp L1")
    u2=st.file_uploader("Raw Data Lần 2",type=["xlsx","xls"],key="l2")
    if u2: save_upload(u2,"l2"); st.success("Đã nạp L2")
    st.divider()
    leaders=sorted({x["Leader"] for x in TARGET_35_NV_MASTER}|{x["Leader"] for x in TARGET_94_ESIM_L1})
    selected_leader=st.selectbox("Leader",["Tất cả"]+leaders)
    selected_region=st.selectbox("Miền",["Tất cả","Miền Bắc","Miền Nam"])
    search=st.text_input("Tìm NV / MSNV / Shop","")

st.markdown(f"""
<div class="hero"><div><div class="hero-title">📱 CELLPHONES ENTERPRISE AUDIT — {view}</div>
<div class="hero-sub">Plan-level engine • Trade • Plus • Mystery • Interview • QC</div></div>
<div class="hero-pill">v{APP_VERSION}</div></div>
""",unsafe_allow_html=True)

def render_round(sheets,fname,label):
    m=metrics(sheets,label)
    if not any([m["trade_plans"],m["plus_plans"],m["mystery_plans"]]):
        st.error(f"File {fname} không có dữ liệu '{label}' trong cột Chấm. Không dùng dữ liệu vòng khác để giả lập {label}.")
        st.stop()

    t35=match35(m["interviews"])
    t94=match94(m["interviews"])
    tested=int((t35["Đánh giá"]!="CHƯA TRẢ BÀI").sum())
    passed=int((t35["Đánh giá"]=="ĐẠT").sum())

    rework_count = (
        m["trade_qc"]["REJECT"]+m["trade_qc"]["REWORK"]+
        m["plus_qc"]["REJECT"]+m["plus_qc"]["REWORK"]+
        m["mystery_qc"]["REJECT"]+m["mystery_qc"]["REWORK"]
    )
    if label == "Lần 2":
        c1,c2,c3,c4,c5=st.columns(5)
        c1.metric("Trade CPS Stores",m["trade_cps_stores"])
        c2.metric("Plus Stores",m["plus_stores"])
        c3.metric("Mystery Field Done",f'{m["mystery_field_done"]} / {MYSTERY_TARGET}')
        c4.metric("35 NV đã trả bài",f"{tested} / 35")
        c5.metric("Rework/Reject Plans",rework_count)
    else:
        c1,c2,c3,c4,c5,c6=st.columns(6)
        c1.metric("Trade CPS Stores",m["trade_cps_stores"])
        c2.metric("Trade DTV Stores",m["trade_dtv_stores"])
        c3.metric("Plus Stores",m["plus_stores"])
        c4.metric("Mystery Field Done",f'{m["mystery_field_done"]} / {MYSTERY_TARGET}')
        c5.metric("35 NV đã trả bài",f"{tested} / 35")
        c6.metric("Rework/Reject Plans",rework_count)

    tabs=st.tabs(["📊 Executive","🏪 Shop Status","🎤 35 NV","📱 94 eSIM","➕ Audit Plus","🕵️ Mystery","👤 Leader","⚠️ Rework","🧪 Validation"])

    with tabs[0]:
        overview=pd.DataFrame([
            {"Nghiệp vụ":"Trade CPS" if label=="Lần 2" else "Trade","Plan":m["trade_plans"],"Field Done":m["trade_field_done"],"QC Done":m["trade_qc"]["DONE"],"QC Pending":m["trade_qc"]["PENDING"]+m["trade_qc"]["PENDING_REVIEW"],"Reject/Rework":m["trade_qc"]["REJECT"]+m["trade_qc"]["REWORK"]},
            {"Nghiệp vụ":"Plus","Plan":m["plus_plans"],"Field Done":m["plus_field_done"],"QC Done":m["plus_qc"]["DONE"],"QC Pending":m["plus_qc"]["PENDING"]+m["plus_qc"]["PENDING_REVIEW"],"Reject/Rework":m["plus_qc"]["REJECT"]+m["plus_qc"]["REWORK"]},
            {"Nghiệp vụ":"Mystery (toàn kỳ)","Plan":m["mystery_plans"],"Field Done":m["mystery_field_done"],"QC Done":m["mystery_qc"]["DONE"],"QC Pending":m["mystery_qc"]["PENDING"]+m["mystery_qc"]["PENDING_REVIEW"],"Reject/Rework":m["mystery_qc"]["REJECT"]+m["mystery_qc"]["REWORK"]},
        ])
        st.dataframe(overview,use_container_width=True,hide_index=True)
        st.plotly_chart(px.bar(overview,x="Nghiệp vụ",y=["Field Done","QC Done","QC Pending"],barmode="group",title="Tiến độ plan-level"),use_container_width=True)

    with tabs[1]:
        ss = store_completion(m,label)
        if selected_leader!="Tất cả" and not ss.empty:
            ss=ss[ss["Leader"]==selected_leader]
        q=norm(search)
        if q and not ss.empty:
            ss=ss[ss.apply(lambda r:q in norm(r["Mã cửa hàng"]) or q in norm(r["Leader"]),axis=1)]
        st.subheader("🏪 Trạng thái hoàn thành theo từng cửa hàng")
        st.caption("Hoàn thành module = tất cả Plan hiện có của module tại shop đều Field Done và QC Done.")
        st.dataframe(ss,use_container_width=True,hide_index=True,height=650)

    with tabs[2]:
        v=t35.copy()
        if selected_leader!="Tất cả":v=v[v["Leader"]==selected_leader]
        q=norm(search)
        if q:v=v[v.apply(lambda r:q in norm(r["Nhân sự"]) or q in norm(r["Mã cửa hàng"]),axis=1)]
        a,b,c,d=st.columns(4)
        a.metric("Đã trả bài",tested)
        b.metric("ĐẠT (49.99→50)",passed)
        c.metric("Không đạt/Chưa điểm",int(t35["Đánh giá"].isin(["KHÔNG ĐẠT","CHƯA CÓ ĐIỂM"]).sum()))
        d.metric("Chưa trả bài",int((t35["Đánh giá"]=="CHƯA TRẢ BÀI").sum()))
        st.dataframe(v,use_container_width=True,hide_index=True,height=600)
        st.download_button(
            "📥 Xuất Excel 35 NV",
            data=dataframe_to_excel_bytes(v, "35_NV"),
            file_name=f"CPS_35NV_{label.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with tabs[3]:
        v=t94.copy()
        if selected_leader!="Tất cả":v=v[v["Leader"]==selected_leader]
        if selected_region!="Tất cả":v=v[v["Miền"]==selected_region]
        q=norm(search)
        if q:v=v[v.apply(lambda r:q in norm(r["MSNV"]) or q in norm(r["Họ và Tên"]) or q in norm(r["Shop"]),axis=1)]
        st.dataframe(v,use_container_width=True,hide_index=True,height=600)
        st.caption("Quy tắc export: Điểm L2 = điểm làm tròn; 49.99 → 50 → ĐẠT. Cột Điểm L2 gốc giữ để đối chiếu.")
        st.download_button(
            "📥 Xuất Excel 94 NV eSIM",
            data=dataframe_to_excel_bytes(v, "94_ESIM_L2"),
            file_name=f"CPS_94NV_eSIM_{label.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with tabs[4]:
        st.caption(f'Có nhân viên trả bài: {len(m["interviews"])} / {m["plus_plans"]} plan Plus')
        st.dataframe(m["interviews"],use_container_width=True,hide_index=True,height=620)

    with tabs[5]:
        mp=m["mystery_plan"].copy()
        scen=mystery_by_leader_scenario(m)
        if selected_leader!="Tất cả" and not scen.empty:
            scen=scen[scen["Leader"]==selected_leader]

        a,b,c,d=st.columns(4)
        a.metric("Mystery unique Plan",m["mystery_plans"])
        b.metric("Field Done",m["mystery_field_done"])
        c.metric("QC Done",m["mystery_qc"]["DONE"])
        d.metric("QC Pending",m["mystery_qc"]["PENDING"]+m["mystery_qc"]["PENDING_REVIEW"])

        st.markdown("#### Kịch bản theo từng Leader")
        st.dataframe(scen,use_container_width=True,hide_index=True)

        if not scen.empty:
            fig=px.bar(scen,x="Leader",y="Tổng Plan",color="Kịch bản",barmode="stack",title="Cơ cấu kịch bản Mystery theo Leader")
            st.plotly_chart(fig,use_container_width=True)

        st.markdown("#### Chi tiết Plan Mystery")
        cols=[c for c in ["Tên Plan","Mã cửa hàng","Tên Leader","Hạng mục","Status Plan","QC Status","Ngày update","Ngày thực hiện"] if c in mp.columns]
        st.dataframe(mp[cols],use_container_width=True,hide_index=True,height=560)

    with tabs[6]:
        ls=leader_summary(m)
        st.dataframe(ls,use_container_width=True,hide_index=True)
        if not ls.empty:
            st.plotly_chart(px.bar(ls,x="Leader",y=["QC_Done","QC_Pending","QC_Reject_Rework"],barmode="stack",title="QC theo unique Plan"),use_container_width=True)

    with tabs[7]:
        parts=[]
        for key,name in [("trade_plan","Trade"),("plus_plan","Plus"),("mystery_plan","Mystery")]:
            x=m[key]
            if x.empty:continue
            q=x["QC Status"].apply(classify_qc) if "QC Status" in x.columns else pd.Series("NONE",index=x.index)
            r=x[q.isin(["REJECT","REWORK"])].copy()
            if not r.empty:
                r["Nghiệp vụ"]=name
                parts.append(r)
        rw=pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()
        if rw.empty:
            st.success("Không có Plan Rework/Reject theo dữ liệu hiện tại.")
        else:
            st.dataframe(rw,use_container_width=True,hide_index=True,height=600)

    with tabs[8]:
        mystery_sheet_found = any("mystery" in norm(n) for n in sheets)
        checks=pd.DataFrame([
            {"Check":"Trade Audit sheet","Value":"PASS" if any("trade audit" in norm(n) and "plus" not in norm(n) for n in sheets) else "FAIL"},
            {"Check":"Trade Audit Plus sheet","Value":"PASS" if any("trade" in norm(n) and "plus" in norm(n) for n in sheets) else "FAIL"},
            {"Check":"Mystery sheet","Value":"PASS" if mystery_sheet_found else "FAIL"},
            {"Check":f"Round {label} Trade CPS plans","Value":m["trade_plans"]},
            {"Check":f"Round {label} Plus plans","Value":m["plus_plans"]},
            {"Check":"Mystery plans (không filter L1/L2)","Value":m["mystery_plans"]},
            {"Check":"Master 35 store có ...","Value":"FAIL" if any("..." in x["Mã cửa hàng"] for x in TARGET_35_NV_MASTER) else "PASS"},
        ])
        st.dataframe(checks,use_container_width=True,hide_index=True)
        st.info("V3.4: L2 bỏ DTV; Mystery đọc toàn kỳ; QC đếm unique Plan; 49.99 làm tròn 50 = ĐẠT.")

if view=="📊 CEO VIEW":
    l1,n1=get_round("l1");l2,n2=get_round("l2")
    rows=[]
    for label,sheets,name in [("Lần 1",l1,n1),("Lần 2",l2,n2)]:
        if sheets is None:continue
        m=metrics(sheets,label)
        row={"Đợt":label,"Trade CPS":m["trade_cps_stores"],"Plus Stores":m["plus_stores"],
             "Mystery Field Done":m["mystery_field_done"],"Mystery QC Done":m["mystery_qc"]["DONE"],
             "Trade QC Done":m["trade_qc"]["DONE"],"Plus QC Done":m["plus_qc"]["DONE"]}
        if label!="Lần 2":
            row["Trade DTV"]=m["trade_dtv_stores"]
        rows.append(row)
    if not rows:st.info("Nạp L1/L2 để so sánh.")
    else:
        df=pd.DataFrame(rows);st.dataframe(df,use_container_width=True,hide_index=True)
        st.plotly_chart(px.bar(df,x="Đợt",y=["Trade QC Done","Plus QC Done","Mystery QC Done"],barmode="group"),use_container_width=True)
else:
    prefix="l1" if view=="📌 LẦN 1" else "l2"
    label="Lần 1" if prefix=="l1" else "Lần 2"
    sheets,fname=get_round(prefix)
    if sheets is None:st.info(f"Chưa nạp file {label}.")
    else:render_round(sheets,fname,label)
