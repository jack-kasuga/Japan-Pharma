import streamlit as st
import pandas as pd
import sqlite3
import os

SOURCE_FILE = 'pharmaceutical_excipients.db'

st.set_page_config(page_title="医薬品添加物規格 改正一覧検索システム", page_icon="📖", layout="wide")

st.markdown("""
    <style>
    .block-container {
        padding-top: 0.2rem !important; 
        padding-bottom: 0.8rem !important;
        padding-left: 1.0rem !important;
        padding-right: 1.0rem !important;
        max-width: 100% !important;
    }
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        height: 2.0rem !important;
    }
    
    .custom-main-title {
        text-align: center !important;
        font-size: 1.75rem !important; 
        font-weight: 800 !important;
        margin-top: 0px !important; 
        margin-bottom: 4px !important; 
        color: #1a202c !important;
        line-height: 1.3 !important;
    }

    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        font-size: 0.85rem !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        font-size: 1.0rem !important;
    }

    [data-testid="column"] {
        padding: 0px 2px !important;
        margin: 0px !important;
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }
    
    .stButton > button {
        width: 100% !important;
        border-radius: 6px !important; 
        height: 2.2em !important;
        padding: 0px 2px !important;
        font-size: 0.75rem !important;
        background-color: #f8f9fa !important;
        border: 1px solid #ced4da !important;
        margin: 0px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #e9ecef !important;
        border-color: #adb5bd !important;
    }

    .stTextInput {
        margin-top: 4px !important; 
        margin-bottom: -10px !important; 
    }

    .result-info-container {
        display: flex;
        align-items: baseline;
        flex-wrap: wrap;
        margin-top: 6px;
        margin-bottom: 6px;
    }
    .result-count {
        font-size: 0.95rem;
    }
    .revised-explanation {
        font-size: 0.82rem;
        margin-left: 20px;
        color: #333333;
    }

    .table-container {
        width: 100% !important;
        max-height: calc(100vh - 215px) !important;
        overflow-y: auto !important;
        overflow-x: auto !important;
        margin-top: 4px;
        border: 1px solid #e6e9ef;
        background-color: white;
    }
    .custom-table {
        border-collapse: collapse;
        table-layout: fixed !important;
        background-color: white;
        font-size: 14px;
        font-family: sans-serif;
    }
    
    .custom-table th {
        position: sticky !important;
        top: 0 !important;
        z-index: 2 !important;
        background-color: #f0f2f6;
        color: #31333F;
        font-weight: 600;
        text-align: center;
        line-height: 1.25 !important;
        box-shadow: inset 0 -1px 0 #dcdfe6;
    }
    
    .custom-table th, .custom-table td {
        border: 1px solid #e6e9ef;
        padding: 6px 12px;
        vertical-align: middle;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    .custom-table th:nth-child(1), .custom-table td:nth-child(1) {
        text-align: center;
        width: 50px !important;
    }
    .custom-table th:nth-child(2), .custom-table td:nth-child(2) {
        text-align: center;
        width: 100px !important;
    }
    .custom-table th:nth-child(3), .custom-table td:nth-child(3) {
        text-align: left;
        width: 850px !important;
    }
    .custom-table th:nth-child(n+4), .custom-table td:nth-child(n+4) {
        text-align: center;
        width: 90px !important;
    }

    div[data-testid="stSidebar"] .stCheckbox label {
        background-color: #ffffff;
        border: 1px solid #dcdfe6;
        border-radius: 10px !important;
        padding: 8px 14px !important;
        width: 100%;
        margin-bottom: 4px;
        display: flex;
        transition: all 0.2s;
    }
    div[data-testid="stSidebar"] .stCheckbox div[data-testid="stWidgetLabel"] div:first-child {
        display: none !important;
    }
    div[data-testid="stSidebar"] .stCheckbox label:has(input:checked) {
        background-color: #1E3A8A !important;
        color: #ffffff !important;
        border-color: #1E3A8A !important;
    }
    </style>
    <div class="custom-main-title">🧪医薬品添加物規格 改正一覧検索システム</div>
""", unsafe_allow_html=True)

def load_data():
    if not os.path.exists(SOURCE_FILE):
        st.error(f"エラー: データベースファイル '{SOURCE_FILE}' が見つかりません。先に index.py を実行してください。")
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(SOURCE_FILE)
        query = "SELECT * FROM excipients"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if '番号' in df.columns:
            df = df.rename(columns={'番号': '項番'})
        elif '項番' not in df.columns:
            df['項番'] = range(1, len(df) + 1)
        
        if '品目名' in df.columns:
            df['品目名'] = df['品目名'].str.strip()
        return df
    except Exception as e:
        st.error(f"データベースの読み込み中にエラーが発生しました: {e}")
        return pd.DataFrame()

def format_header_label(col_name):
    """ヘッダーラベルを2段表示（2018や2026が上段、改正・新規が下段）に整形"""
    if '2018' in col_name:
        remainder = col_name.replace('2018', '').strip()
        return f"2018<br>{remainder}"
    if '2026' in col_name:
        remainder = col_name.replace('2026', '').strip()
        if not remainder:
            remainder = "改正"
        return f"2026<br>{remainder}"
    if col_name in ['新規収載', 'R1改正', 'R4改正', 'R6改正']:
        return f"2018<br>{col_name}"
    return col_name

def generate_html_table(df):
    num_rev_cols = max(0, len(df.columns) - 3)
    table_width = 50 + 100 + 850 + (90 * num_rev_cols)
    
    html = f'<div class="table-container"><table class="custom-table" style="width: {table_width}px !important;">'
    html += '<thead><tr>'
    for col in df.columns:
        formatted_header = format_header_label(col)
        html += f'<th>{formatted_header}</th>'
    html += '</tr></thead><tbody>'
    for _, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            val = row[col]
            s_val = str(val) if pd.notna(val) else ""
            bg_style = ""
            if any(k in col for k in ['新規', 'R1', 'R4', 'R6', '2026', '改正']):
                if '〇' in s_val or '○' in s_val or s_val.startswith('R'):
                    bg_style = 'background-color: #FFFF00;'
            
            if col == '品目名':
                html += f'<td style="{bg_style}" title="{s_val}">{s_val}</td>'
            else:
                html += f'<td style="{bg_style}">{s_val}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    return html

def main():
    df = load_data()
    if df.empty: return

    search_query = st.text_input("検索", placeholder="🔍 品目名を入力して検索（例：アクリル酸）", label_visibility="collapsed")

    kana_mapping = {
        "ア行(ア～オ)": "ア行", "カ行(カ～コ)": "カ行", "サ行(サ～ソ)": "サ行",
        "タ行(タ～ト)": "タ行", "ナ行(ナ～ノ)": "ナ行", "ハ行(ハ～ホ)": "ハ行",
        "マ行(マ～モ)": "マ行", "ヤ行(ヤ～ヨ)": "ヤ行", "ラ行(ラ～ロ)": "ラ行",
        "ワ行(ワ)": "ワ行", "全件表示": "全件表示"
    }
    kana_labels = list(kana_mapping.keys())

    if 'sel_kana' not in st.session_state: 
        st.session_state.sel_kana = "全件表示"
        
    active_idx = kana_labels.index(st.session_state.sel_kana) + 1 
    st.markdown(f"""
        <style>
        [data-testid="column"]:nth-child({active_idx}) .stButton > button {{
            border: 2px solid #ff4b4b !important;
            background-color: #fff0f0 !important;
            color: #ff4b4b !important;
            font-weight: bold !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    def set_kana(label):
        st.session_state.sel_kana = label

    cols = st.columns(len(kana_labels))
    for i, label in enumerate(kana_labels):
        with cols[i]:
            st.button(label, on_click=set_kana, args=(label,))

    col_new = next((c for c in df.columns if '新規' in c), None)
    col_r1 = next((c for c in df.columns if 'R1' in c), None)
    col_r4 = next((c for c in df.columns if 'R4' in c), None)
    col_r6 = next((c for c in df.columns if 'R6' in c), None)
    col_2026 = next((c for c in df.columns if '2026' in c), None)

    # --- サイドバー：フィルタ ---
    st.sidebar.header("⚙ フィルター")
    only_any_revised = st.sidebar.checkbox("改正対象品目を全て表示")
    st.sidebar.markdown("---")
    st.sidebar.write("**特定の改正時期で絞り込む**")
    
    c_new = st.sidebar.checkbox("新規収載品目を表示")
    c_r1 = st.sidebar.checkbox("R1改正対象品目を表示")
    c_r4 = st.sidebar.checkbox("R4改正対象品目を表示")
    c_r6 = st.sidebar.checkbox("R6改正対象品目を表示")
    c_2026 = st.sidebar.checkbox("2026改正対象品目を表示")

    df_filtered = df.copy()
    if st.session_state.sel_kana != "全件表示":
        search_val = kana_mapping[st.session_state.sel_kana]
        if 'カタカナ行' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['カタカナ行'] == search_val]
            
    if search_query:
        df_filtered = df_filtered[df_filtered['品目名'].str.contains(search_query, na=False)]
    
    revision_cols = [c for c in [col_r1, col_r4, col_r6, col_2026] if c and c in df_filtered.columns]
    if only_any_revised and revision_cols:
        conds = [df_filtered[c].astype(str).str.contains('〇|○', na=False) for c in revision_cols]
        final_any = conds[0]
        for c in conds[1:]: final_any |= c
        df_filtered = df_filtered[final_any]

    conditions = []
    if c_new and col_new:
        conditions.append(df_filtered[col_new].astype(str).str.contains('〇|○|R', na=False))
    if c_r1 and col_r1:
        conditions.append((df_filtered[col_new].astype(str).str.contains('R1', na=False) if col_new else False) | df_filtered[col_r1].astype(str).str.contains('〇|○', na=False))
    if c_r4 and col_r4:
        conditions.append((df_filtered[col_new].astype(str).str.contains('R4', na=False) if col_new else False) | df_filtered[col_r4].astype(str).str.contains('〇|○', na=False))
    if c_r6 and col_r6:
        conditions.append((df_filtered[col_new].astype(str).str.contains('R6', na=False) if col_new else False) | df_filtered[col_r6].astype(str).str.contains('〇|○', na=False))
    if c_2026 and col_2026:
        conditions.append(df_filtered[col_2026].astype(str).str.contains('〇|○', na=False))

    if conditions:
        final_cond = conditions[0]
        for cond in conditions[1:]: final_cond |= cond
        df_filtered = df_filtered[final_cond]

    st.markdown(f"""
        <div class="result-info-container">
            <div class="result-count">📊 検索結果: <b>{len(df_filtered)}</b> 件</div>
            <div class="revised-explanation">
                R1改正：令和元年一部改正&nbsp;&nbsp;
                R4改正：令和4年一部改正&nbsp;&nbsp;
                R6改正：令和6年一部改正&nbsp;&nbsp;
                2026改正：2026年一部改正
            </div>
        </div>
    """, unsafe_allow_html=True)

    display_cols = [c for c in ['項番', 'カタカナ行', '品目名', col_new, col_r1, col_r4, col_r6, col_2026] if c and c in df_filtered.columns]
    
    if not df_filtered.empty:
        html_table = generate_html_table(df_filtered[display_cols])
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.warning("該当する品目が見つかりませんでした。")

if __name__ == "__main__":
    main()