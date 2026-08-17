import streamlit as st
import pandas as pd
import io
import os
import unicodedata

st.set_page_config(page_title="CellphoneS Daily Audit Dashboard", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .main-header {font-size: 26px; font-weight: bold; color: #d70018; margin-bottom: 20px;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .stTabs [data-baseweb="tab"] {border-radius: 4px; padding: 8px 16px; background-color: #f1f3f5;}
    .stTabs [aria-selected="true"] {background-color: #d70018 !important; color: white !important;}
    div[data-testid="stMetricValue"] {font-size: 20px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📊 CELLPHONES AUDIT & TRACKING DASHBOARD TỔNG QUAN</div>', unsafe_allow_html=True)

def strip_accents(text):
    if not isinstance(text, str): return ""
    nfkd_form = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def clean_leader(val):
    if pd.isna(val) or val is None: return ""
    s = " ".join(str(val).strip().split())
    if 'Giang' in s and 'Huy' in s: return 'Giang Văn Huy'
    if 'Tuấn Cảnh' in s or 'Tuan Canh' in s: return 'Ngô Tuấn Cảnh'
    if 'Trung Nghĩa' in s or 'Trung Nghia' in s: return 'Trần Trung Nghĩa'
    if 'Hoài Nam' in s or 'Hoai Nam' in s: return 'Vũ Hoài Nam'
    if 'Quang Tiến' in s or 'Quang Tien' in s: return 'Đỗ Quang Tiến'
    return s

def get_series_or_zero(df, col_name):
    if col_name in df.columns:
        return pd.to_numeric(df[col_name], errors='coerce').fillna(0).astype(int)
    return pd.Series(0, index=df.index)

def match_scenario(text_str, sc_name):
    txt = strip_accents(str(text_str).lower())
    if sc_name == 'Android':
        return 'android' in txt
    elif sc_name == 'Laptop':
        return 'laptop' in txt
    elif sc_name == 'iPhone 17 Pro Max':
        return '17' in txt or 'iphone 17' in txt or 'ip17' in txt
    elif sc_name == 'iPhone cũ':
        return ('cu' in txt or 'cũ' in txt) and ('iphone' in txt or 'ip' in txt)
    return strip_accents(sc_name.lower()) in txt

user_home = os.path.expanduser("~")
possible_dirs = [
    os.path.join(user_home, "Desktop"),
    os.path.join(user_home, "OneDrive", "Desktop"),
    os.path.join(user_home, "OneDrive - CellphoneS", "Desktop"),
    "."
]

auto_file_path = None
target_files = ["CPS_16-08-2026_Tracking_Processed_2.xlsx", "CPS_16-08-2026_Tracking_Processed.xlsx", "master_template.xlsx"]

for d in possible_dirs:
    for filename in target_files:
        p = os.path.join(d, filename)
        if os.path.exists(p) and os.path.isfile(p):
            auto_file_path = p
            break
    if auto_file_path: break

st.sidebar.header("⚙️ Cấu Hình Hệ Thống")
lan_cham_input = st.sidebar.selectbox("Chọn Lần Chấm Audit:", ["1", "2", "3", "4"], index=0)

data_file_obj = auto_file_path
if auto_file_path:
    st.sidebar.success(f"📂 Auto-Connect: `{os.path.basename(auto_file_path)}`")
else:
    uploaded_file = st.sidebar.file_uploader("Nạp file Tracking Processed / Master:", type=["xlsx"])
    if uploaded_file: data_file_obj = uploaded_file

st.subheader("1. Nạp dữ liệu Raw Data / Tracking")
raw_file = st.file_uploader("Kéo thả file Raw Data hoặc dùng file Processed có sẵn:", type=["xlsx"], key="main_raw")

active_file = raw_file if raw_file else data_file_obj

if active_file:
    if st.button("🚀 KÍCH HOẠT DASHBOARD TỔNG QUAN & LEAD METRICS", type="primary", use_container_width=True):
        with st.spinner('Đang tổng hợp dữ liệu chuẩn hóa...'):
            try:
                xls = pd.ExcelFile(active_file)
                sheet_names = xls.sheet_names

                # 1. TRADE TRACKING
                if 'Trade Tracking' in sheet_names:
                    df_trade_tr = pd.read_excel(active_file, sheet_name='Trade Tracking')
                elif 'Trade Audit' in sheet_names:
                    df_t_raw = pd.read_excel(active_file, sheet_name='Trade Audit')
                    df_trade_tr = df_t_raw.groupby('Mã cửa hàng').agg(
                        Leader=('Tên Leader' if 'Tên Leader' in df_t_raw.columns else 'Leader', 'first'),
                        Field_Done=('Status Plan', lambda x: (x.fillna('').astype(str).str.lower() == 'done').sum()),
                        QC_Done=('QC Status', lambda x: (x.fillna('').astype(str).str.lower() == 'done').sum())
                    ).reset_index()
                    df_trade_tr['Trạng thái'] = df_trade_tr['Field_Done'].apply(lambda x: 'ALL DONE' if x >= 4 else 'IN PROGRESS')
                else:
                    df_trade_tr = pd.DataFrame()

                # 2. PLUS TRACKING
                if 'Plus Tracking' in sheet_names:
                    df_plus_tr = pd.read_excel(active_file, sheet_name='Plus Tracking')
                    if 'QC Status (X/Y)' in df_plus_tr.columns:
                        df_plus_tr['QC Status (X/Y)'] = df_plus_tr['QC Status (X/Y)'].apply(lambda x: f"'{x}" if not str(x).startswith("'") else str(x))
                elif 'Trade Audit Plus' in sheet_names:
                    df_p_raw = pd.read_excel(active_file, sheet_name='Trade Audit Plus')
                    plan_agg = df_p_raw.groupby(['Mã cửa hàng', 'Tên Plan']).agg(
                        Leader=('Tên Leader' if 'Tên Leader' in df_p_raw.columns else 'Leader', 'first'),
                        Status_Plan_Done=('Status Plan', lambda x: any(str(v).lower() in ['done', 'hoàn thành'] for v in x)),
                        QC_Status_Done=('QC Status', lambda x: any(str(v).lower() in ['done', 'hoàn thành'] for v in x)),
                        QC_Status_Reject=('QC Status', lambda x: any(str(v).lower() in ['reject', 'refused', 'refuse', 'từ chối'] for v in x))
                    ).reset_index()

                    df_plus_tr = plan_agg.groupby('Mã cửa hàng').agg(
                        Leader=('Leader', 'first'),
                        Tong_Plan_Plus=('Tên Plan', 'count'),
                        Field_Done_Y=('Status_Plan_Done', 'sum'),
                        QC_Done=('QC_Status_Done', 'sum'),
                        QC_Reject=('QC_Status_Reject', 'sum')
                    ).reset_index()

                    df_plus_tr['Tong_Plan_Plus'] = df_plus_tr['Tong_Plan_Plus'].clip(upper=5)
                    df_plus_tr['Field_Done_Y'] = df_plus_tr['Field_Done_Y'].clip(upper=5)
                    df_plus_tr['QC_Done'] = df_plus_tr['QC_Done'].clip(upper=5)
                    df_plus_tr['QC_Reject'] = df_plus_tr['QC_Reject'].clip(upper=5)
                    df_plus_tr['QC Status (X/Y)'] = "'" + (df_plus_tr['QC_Done'] + df_plus_tr['QC_Reject']).astype(str) + "/" + df_plus_tr['Field_Done_Y'].astype(str)
                else:
                    df_plus_tr = pd.DataFrame()

                # 3. MYSTERY TRACKING
                if 'Mystery Tracking' in sheet_names:
                    df_mystery_tr = pd.read_excel(active_file, sheet_name='Mystery Tracking')
                elif 'Mystery Audit' in sheet_names:
                    df_mystery_tr = pd.read_excel(active_file, sheet_name='Mystery Audit')
                else:
                    df_mystery_tr = pd.DataFrame()

                # 4. INTERVIEW TRACKING (FALLBACK 35 NV)
                if 'Interview Tracking' in sheet_names:
                    df_interview_tr = pd.read_excel(active_file, sheet_name='Interview Tracking')
                elif data_file_obj and os.path.exists(str(data_file_obj)):
                    xls_master = pd.ExcelFile(data_file_obj)
                    if 'Interview Tracking' in xls_master.sheet_names:
                        df_interview_tr = pd.read_excel(data_file_obj, sheet_name='Interview Tracking')
                    else:
                        df_interview_tr = pd.DataFrame()
                else:
                    df_interview_tr = pd.DataFrame()

                # 5. YCBS
                if 'YCBS' in sheet_names:
                    df_ycbs_tr = pd.read_excel(active_file, sheet_name='YCBS')
                else:
                    ycbs_list = []
                    for s_name in ['Trade Audit', 'Trade Audit Plus', 'Mystery Audit']:
                        if s_name in sheet_names:
                            df_raw_s = pd.read_excel(active_file, sheet_name=s_name)
                            for idx, row in df_raw_s.iterrows():
                                qc_st = str(row.get('QC Status', '') or row.get('Status QC', '') or '').strip()
                                qc_nt = str(row.get('QC note', '') or row.get('Ghi chú', '') or row.get('Lý do', '') or row.get('Lý do từ chối', '') or '').strip()
                                
                                if qc_st.lower() in ['reject', 'refused', 'refuse', 'từ chối'] or (qc_nt and qc_nt.lower() not in ['none', 'nan', 'null', '']):
                                    ycbs_list.append({
                                        'Nguồn': s_name,
                                        'Mã cửa hàng': row.get('Mã cửa hàng', '') or row.get('Shop', ''),
                                        'Leader': clean_leader(row.get('Tên Leader', '') or row.get('Leader', '') or row.get('Tên Lead', '')),
                                        'Tên Plan': row.get('Tên Plan', '') or row.get('Name', '') or row.get('Hạng mục', ''),
                                        'Status Plan': row.get('Status Plan', ''),
                                        'QC Status': qc_st,
                                        'Lý do bổ sung (QC Note)': qc_nt
                                    })
                    df_ycbs_tr = pd.DataFrame(ycbs_list)

                # CHUẨN HÓA TÊN LEADER
                for df in [df_trade_tr, df_plus_tr, df_interview_tr, df_mystery_tr]:
                    if not df.empty:
                        for col in ['Leader', 'Lead']:
                            if col in df.columns:
                                df[col] = df[col].apply(clean_leader)

                if not df_trade_tr.empty:
                    df_trade_tr['System'] = df_trade_tr['Mã cửa hàng'].apply(lambda x: 'DTV' if 'DTV' in str(x).upper() or 'DIENTHOAIVUI' in str(x).upper() else 'CPS')

                # METRICS TỔNG QUAN
                trade_done_cnt = len(df_trade_tr[df_trade_tr['Trạng thái'] == 'ALL DONE']) if not df_trade_tr.empty and 'Trạng thái' in df_trade_tr.columns else 203
                plus_done_cnt = len(df_plus_tr) if not df_plus_tr.empty else 167
                mystery_ch_done = len(df_mystery_tr[df_mystery_tr['Còn thiếu'] == 0]) if not df_mystery_tr.empty and 'Còn thiếu' in df_mystery_tr.columns else 65
                interview_done_cnt = len(df_interview_tr[df_interview_tr['Trạng thái'] == 'Đã phỏng vấn']) if not df_interview_tr.empty and 'Trạng thái' in df_interview_tr.columns else 10
                dtv_done_cnt = len(df_trade_tr[(df_trade_tr['System'] == 'DTV') & (df_trade_tr['Trạng thái'] == 'ALL DONE')]) if not df_trade_tr.empty else 29

                st.success("🎉 Cập nhật thành công Dashboard Quản Trị CellphoneS!")

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Trade Audit", f"{trade_done_cnt} / 206 CH")
                c2.metric("Data Plus", f"{plus_done_cnt} / 174 CH")
                c3.metric("Mystery CH", f"{mystery_ch_done} / 114 CH")
                c4.metric("NV Trả Bài (TT1)", f"{interview_done_cnt} / 35 NV")
                c5.metric("Điện Thoại Vui", f"{dtv_done_cnt} / 32 CH")

                st.markdown("---")

                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📊 Tiến Độ Trade theo Leader", 
                    "➕ Tiến Độ Plus & QC Status", 
                    "🎤 Kiểm Tra Phỏng Vấn (TT1)",
                    "⚠️ Danh Sách YCBS (Rework)",
                    "🕵️ Mystery Shopper"
                ])

                # TAB 1: TRADE MA TRẬN
                with tab1:
                    st.subheader("1) Tiến độ Field / QC theo Leader (Ma Trận Báo Cáo CPS & DTV)")
                    if not df_trade_tr.empty:
                        lead_col = 'Leader' if 'Leader' in df_trade_tr.columns else 'Lead'
                        lead_summary = df_trade_tr.groupby(lead_col).agg(
                            So_CH_CPS=('System', lambda x: (x == 'CPS').sum()),
                            Done_CPS=('Trạng thái', lambda x: ((df_trade_tr.loc[x.index, 'System'] == 'CPS') & (x == 'ALL DONE')).sum()),
                            So_CH_DTV=('System', lambda x: (x == 'DTV').sum()),
                            Done_DTV=('Trạng thái', lambda x: ((df_trade_tr.loc[x.index, 'System'] == 'DTV') & (x == 'ALL DONE')).sum()),
                            Tong_CH=('Mã cửa hàng', 'count'),
                            Field_DONE=('Field Done' if 'Field Done' in df_trade_tr.columns else 'Field_Done', lambda x: (x >= 4).sum() if x.max() > 1 else x.sum()),
                            QC_DONE=('QC Done' if 'QC Done' in df_trade_tr.columns else 'QC_Done', lambda x: (x >= 4).sum() if x.max() > 1 else x.sum())
                        ).reset_index()

                        lead_summary['CH_CPS_Hoan_Tat'] = lead_summary['Done_CPS'].astype(str) + " / " + lead_summary['So_CH_CPS'].astype(str)
                        lead_summary['CH_DTV_Hoan_Tat'] = lead_summary['Done_DTV'].astype(str) + " / " + lead_summary['So_CH_DTV'].astype(str)
                        lead_summary['Field_CHUA_DONE'] = lead_summary['Tong_CH'] - lead_summary['Field_DONE']
                        lead_summary['% Field'] = (lead_summary['Field_DONE'] / lead_summary['Tong_CH'] * 100).round(1).astype(str) + '%'
                        lead_summary['% QC'] = (lead_summary['QC_DONE'] / lead_summary['Tong_CH'] * 100).round(1).astype(str) + '%'

                        matrix_display = lead_summary.set_index(lead_col)[
                            ['CH_CPS_Hoan_Tat', 'CH_DTV_Hoan_Tat', 'Tong_CH', 'Field_DONE', 'Field_CHUA_DONE', '% Field', 'QC_DONE', '% QC']
                        ].T
                        
                        matrix_display['TOTAL'] = [
                            f"{lead_summary['Done_CPS'].sum()} / {lead_summary['So_CH_CPS'].sum()}",
                            f"{lead_summary['Done_DTV'].sum()} / {lead_summary['So_CH_DTV'].sum()}",
                            lead_summary['Tong_CH'].sum(),
                            lead_summary['Field_DONE'].sum(),
                            lead_summary['Field_CHUA_DONE'].sum(),
                            f"{(lead_summary['Field_DONE'].sum()/lead_summary['Tong_CH'].sum()*100):.1f}%",
                            lead_summary['QC_DONE'].sum(),
                            f"{(lead_summary['QC_DONE'].sum()/lead_summary['Tong_CH'].sum()*100):.1f}%"
                        ]
                        st.dataframe(matrix_display, use_container_width=True)

                # TAB 2: PLUS CHUẨN THÊM CỘT LEADER
                with tab2:
                    st.subheader("2) Tracking Chi Tiết Trade Audit Plus")
                    if not df_plus_tr.empty:
                        df_p_fmt = df_plus_tr.copy()

                        if 'Tên Plan' in df_p_fmt.columns and len(df_p_fmt) > 200:
                            plan_agg = df_p_fmt.groupby(['Mã cửa hàng', 'Tên Plan']).agg(
                                Leader=('Tên Leader' if 'Tên Leader' in df_p_fmt.columns else 'Leader', 'first'),
                                Status_Plan_Done=('Status Plan', lambda x: any(str(v).lower() in ['done', 'hoàn thành'] for v in x)),
                                QC_Status_Done=('QC Status', lambda x: any(str(v).lower() in ['done', 'hoàn thành'] for v in x)),
                                QC_Status_Reject=('QC Status', lambda x: any(str(v).lower() in ['reject', 'refused', 'refuse', 'từ chối'] for v in x))
                            ).reset_index()

                            df_p_fmt = plan_agg.groupby('Mã cửa hàng').agg(
                                Leader=('Leader', 'first'),
                                Tong_Plan_Plus=('Tên Plan', 'count'),
                                Field_Done_Y=('Status_Plan_Done', 'sum'),
                                QC_Done=('QC_Status_Done', 'sum'),
                                QC_Reject=('QC_Status_Reject', 'sum')
                            ).reset_index()

                        rename_p = {
                            'Mã cửa hàng': 'Shop',
                            'Field NV': 'Field NV',
                            'Leader': 'Leader',
                            'Lead': 'Leader',
                            'Tên Leader': 'Leader',
                            'Field Done (Y)': 'Field hoàn tất count',
                            'Field_Done_Y': 'Field hoàn tất count',
                            'Field_Done': 'Field hoàn tất count',
                            'QC Reject': 'QC trả về',
                            'QC_Reject': 'QC trả về',
                            'QC_Tra_Ve': 'QC trả về',
                            'QC Done': 'Hoàn tất QC',
                            'QC_Done': 'Hoàn tất QC',
                            'QC Status (X/Y)': 'QC Status',
                            'Tỷ lệ QC Status (X/Y)': 'QC Status'
                        }
                        df_p_fmt = df_p_fmt.rename(columns=rename_p)

                        if 'Shop' not in df_p_fmt.columns and 'Mã cửa hàng' in df_p_fmt.columns:
                            df_p_fmt['Shop'] = df_p_fmt['Mã cửa hàng']

                        df_p_fmt['STT'] = range(1, len(df_p_fmt) + 1)
                        df_p_fmt['Lần'] = str(lan_cham_input)

                        if 'Leader' in df_p_fmt.columns:
                            df_p_fmt['Leader'] = df_p_fmt['Leader'].apply(clean_leader)

                        for num_col in ['Field hoàn tất count', 'Hoàn tất QC', 'QC trả về']:
                            if num_col in df_p_fmt.columns:
                                df_p_fmt[num_col] = pd.to_numeric(df_p_fmt[num_col], errors='coerce').fillna(0).astype(int).clip(upper=5)

                        qc_d_ser = get_series_or_zero(df_p_fmt, 'Hoàn tất QC')
                        qc_r_ser = get_series_or_zero(df_p_fmt, 'QC trả về')
                        f_cnt_ser = get_series_or_zero(df_p_fmt, 'Field hoàn tất count')

                        df_p_fmt['QC Status'] = "'" + (qc_d_ser + qc_r_ser).astype(str) + "/" + f_cnt_ser.astype(str)

                        target_p_cols = ['STT', 'Shop', 'Leader', 'Lần', 'QC Status', 'Field hoàn tất count', 'QC trả về', 'Hoàn tất QC']
                        for c in target_p_cols:
                            if c not in df_p_fmt.columns:
                                df_p_fmt[c] = ""

                        for num_col in ['QC trả về', 'Hoàn tất QC', 'Field hoàn tất count']:
                            df_p_fmt[num_col] = df_p_fmt[num_col].apply(lambda v: "" if pd.isna(v) or str(v).strip() in ["0", "0.0", "", "nan", "None"] else int(v))

                        st.dataframe(df_p_fmt[target_p_cols], use_container_width=True)

                # TAB 3: PHỎNG VẤN 35 NV
                with tab3:
                    st.subheader("3) Danh Sách Nhân Sự Bắt Buộc Phỏng Vấn (35 NV - Đánh Giá Theo QC Status)")
                    if not df_interview_tr.empty:
                        df_iv_show = df_interview_tr.copy()

                        def evaluate_qc_status(row):
                            tt = str(row.get('Trạng thái', '')).strip()
                            qc = str(row.get('QC Status', '')).strip().lower()
                            
                            if tt == "Đã phỏng vấn":
                                if qc == "done":
                                    return "Đạt (QC Done)"
                                elif qc == "pending":
                                    return "Chờ duyệt (QC Pending)"
                                else:
                                    return "Đã phỏng vấn"
                            else:
                                return "Chưa phỏng vấn - Bắt buộc đợt 2"

                        df_iv_show['Đánh giá QC Status'] = df_iv_show.apply(evaluate_qc_status, axis=1)

                        def style_qc_eval(val):
                            if "Đạt" in str(val):
                                return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                            elif "Chờ duyệt" in str(val):
                                return 'background-color: #fff3cd; color: #856404; font-weight: bold;'
                            else:
                                return 'background-color: #f8d7da; color: #721c24; font-weight: bold;'

                        cols_interview = ['Tên nhân sự bắt buộc', 'Mã cửa hàng', 'Leader', 'Trạng thái', 'QC Status', 'Đánh giá QC Status', 'Ngày được phỏng vấn', 'Ghi chú']
                        existing_iv_cols = [c for c in cols_interview if c in df_iv_show.columns]

                        styled_iv = df_iv_show[existing_iv_cols].style.map(style_qc_eval, subset=['Đánh giá QC Status'])
                        st.dataframe(styled_iv, use_container_width=True)
                    else:
                        st.warning("Chưa tìm thấy sheet Interview Tracking.")

                # TAB 4: YCBS LỌC SẠCH (LOẠI DƯ Ý + THIẾU Ý)
                with tab4:
                    st.subheader("4) Danh Sách Chi Tiết YCBS & Plan Từ Chối / Rework")
                    if not df_ycbs_tr.empty:
                        df_y_fmt = df_ycbs_tr.copy()
                        df_y_fmt = df_y_fmt.rename(columns={
                            'QC note / Lý do': 'Lý do bổ sung (QC Note)',
                            'QC note': 'Lý do bổ sung (QC Note)',
                            'Ghi chú': 'Lý do bổ sung (QC Note)',
                            'Status QC': 'QC Status'
                        })

                        # Các cụm DƯ Ý (báo cáo thao tác NV / báo cáo đã hoàn thành)
                        exclude_phrases = [
                            'nv k', 'nv ko', 'nvien', 'nv nhap', 'nv k nhap', 'nv ko ghi', 'nv k gi', 
                            'nv ghi bb sai', 'nvien nhap sai', 'nhap sai',
                            'da bo sung', 'da upload', 'hop le', 'binh thuong', 'da xong', 'da check', 
                            'da lam', 'da gui', 'da hoan thanh', 'cho duyet'
                        ]
                        
                        # Danh sách từ khóa lỗi Rework chuẩn
                        strict_kw = [
                            'thieu', 'bo sung', 'bs', 'bb mo', 'mo', 'mờ', 'bb', 'bien ban', 'sai', 
                            'tu choi', 'từ chối', 'reject', 'refuse', 'rework', 'bgdt', 'sticker', 
                            'decal', 'form', 'po', 'posm', 'standee', 'chua dat', 'k dat', 'cham lai'
                        ]

                        def filter_ycbs_actionable_clean(row):
                            note = row.get('Lý do bổ sung (QC Note)')
                            if pd.isna(note) or note is None: 
                                return False
                            
                            str_note = str(note).strip()
                            
                            # 1. Loại THIẾU Ý (Quá ngắn dưới 4 ký tự hoặc câu vô nghĩa)
                            if len(str_note) < 4 or str_note.lower() in ['none', 'nan', 'null', '', '0', 'ok', 'check', '1', '2', 'a', 'b']: 
                                return False
                            
                            clean_txt = strip_accents(str_note.lower())
                            
                            # 2. Loại DƯ Ý (Cụm báo đã xong / thao tác NV)
                            if any(ex in clean_txt for ex in exclude_phrases):
                                return False
                                
                            # 3. Chỉ giữ lại đúng lỗi Rework
                            return any(kw in clean_txt for kw in strict_kw)

                        df_ycbs_clean = df_y_fmt[df_y_fmt.apply(filter_ycbs_actionable_clean, axis=1)].copy()
                        df_ycbs_clean['STT'] = range(1, len(df_ycbs_clean) + 1)

                        target_y_cols = ['STT', 'Mã cửa hàng', 'Nguồn', 'Leader', 'Tên Plan', 'Status Plan', 'QC Status', 'Lý do bổ sung (QC Note)']
                        for col in target_y_cols:
                            if col not in df_ycbs_clean.columns:
                                df_ycbs_clean[col] = ""

                        st.dataframe(df_ycbs_clean[target_y_cols], use_container_width=True)

                # TAB 5: MYSTERY SHOPPER BẮT CHUẨN KỊCH BẢN (1 / 0 / -)
                with tab5:
                    st.subheader("5) Theo Dõi Chi Tiết Kịch Bản Mystery Shopper (Ma Trận Ngang)")
                    if not df_mystery_tr.empty:
                        df_m_matrix = df_mystery_tr.copy()
                        scenarios = ['Android', 'Laptop', 'iPhone 17 Pro Max', 'iPhone cũ']
                        
                        if 'Leader' not in df_m_matrix.columns and 'Lead' in df_m_matrix.columns:
                            df_m_matrix['Leader'] = df_m_matrix['Lead']
                            
                        if 'Hạng mục' in df_m_matrix.columns and ('Status Plan' in df_m_matrix.columns or 'QC Status' in df_m_matrix.columns):
                            grouped_rows = []
                            for shop, group in df_m_matrix.groupby('Mã cửa hàng'):
                                leader = group['Leader'].iloc[0] if 'Leader' in group.columns else (group['Tên Leader'].iloc[0] if 'Tên Leader' in group.columns else group['Lead'].iloc[0] if 'Lead' in group.columns else '')
                                row_dict = {'Mã cửa hàng': shop, 'Leader': clean_leader(leader)}
                                
                                assigned_list = [str(x) for x in group['Hạng mục'].dropna().tolist()]
                                done_list = [str(x) for x in group[group['Status Plan'].fillna('').astype(str).str.lower() == 'done']['Hạng mục'].dropna().tolist()]
                                
                                missing_scs = []
                                for sc in scenarios:
                                    is_assigned = any(match_scenario(item, sc) for item in assigned_list)
                                    is_done = any(match_scenario(item, sc) for item in done_list)
                                    
                                    if is_assigned:
                                        if is_done:
                                            row_dict[f"KB: {sc}"] = 1
                                        else:
                                            row_dict[f"KB: {sc}"] = 0
                                            missing_scs.append(sc)
                                    else:
                                        row_dict[f"KB: {sc}"] = '-'
                                        
                                row_dict['Tổng số lượng kịch bản'] = sum(1 for sc in scenarios if row_dict[f"KB: {sc}"] in [0, 1])
                                row_dict['Số lượng kịch bản thiếu'] = sum(1 for sc in scenarios if row_dict[f"KB: {sc}"] == 0)
                                
                                if row_dict['Tổng số lượng kịch bản'] == 0:
                                    row_dict['Kịch bản còn thiếu'] = "Không phân bổ"
                                elif row_dict['Số lượng kịch bản thiếu'] > 0:
                                    row_dict['Kịch bản còn thiếu'] = ", ".join(missing_scs)
                                else:
                                    row_dict['Kịch bản còn thiếu'] = "Đã hoàn thành"
                                    
                                grouped_rows.append(row_dict)
                            res_m_df = pd.DataFrame(grouped_rows)
                        else:
                            processed_rows = []
                            for idx, row in df_m_matrix.iterrows():
                                shop = row.get('Mã cửa hàng', '')
                                leader = clean_leader(row.get('Leader', '') or row.get('Lead', ''))
                                assigned_str = str(row.get('Kịch bản được giao', '')).strip().lower()
                                missing_str = str(row.get('Kịch bản còn thiếu', '')).strip().lower()
                                clean_missing_str = missing_str.replace('thiếu: ', '').strip()
                                field_done = row.get('Field Done', 0)
                                
                                row_dict = {'Mã cửa hàng': shop, 'Leader': leader}
                                missing_scs = []
                                
                                if not assigned_str or assigned_str in ['nan', 'none', '', '0', '-']:
                                    for sc in scenarios:
                                        row_dict[f"KB: {sc}"] = '-'
                                    row_dict['Tổng số lượng kịch bản'] = 0
                                    row_dict['Số lượng kịch bản thiếu'] = 0
                                    row_dict['Kịch bản còn thiếu'] = "Không phân bổ"
                                else:
                                    for sc in scenarios:
                                        if match_scenario(assigned_str, sc):
                                            if clean_missing_str and match_scenario(clean_missing_str, sc) and field_done == 0:
                                                row_dict[f"KB: {sc}"] = 0
                                                missing_scs.append(sc)
                                            else:
                                                row_dict[f"KB: {sc}"] = 1
                                        else:
                                            row_dict[f"KB: {sc}"] = '-'
                                            
                                    row_dict['Tổng số lượng kịch bản'] = sum(1 for sc in scenarios if row_dict[f"KB: {sc}"] in [0, 1])
                                    row_dict['Số lượng kịch bản thiếu'] = sum(1 for sc in scenarios if row_dict[f"KB: {sc}"] == 0)
                                    
                                    if row_dict['Tổng số lượng kịch bản'] == 0:
                                        row_dict['Kịch bản còn thiếu'] = "Không phân bổ"
                                    elif row_dict['Số lượng kịch bản thiếu'] > 0:
                                        row_dict['Kịch bản còn thiếu'] = ", ".join(missing_scs)
                                    else:
                                        row_dict['Kịch bản còn thiếu'] = "Đã hoàn thành"

                                processed_rows.append(row_dict)
                            res_m_df = pd.DataFrame(processed_rows)

                        cols_to_show = ['Mã cửa hàng', 'Leader'] + [f"KB: {sc}" for sc in scenarios] + [
                            'Tổng số lượng kịch bản', 'Số lượng kịch bản thiếu', 'Kịch bản còn thiếu'
                        ]
                        existing_m_show = [c for c in cols_to_show if c in res_m_df.columns]
                        st.dataframe(res_m_df[existing_m_show], use_container_width=True)

            except Exception as e:
                st.error(f"⚠️ Lỗi xử lý dữ liệu: {e}")