import streamlit as st
import pandas as pd
import sqlite3
import os

# --- 設定項目 ---
SOURCE_FILE = 'pharmaceutical_excipients.db'

# ページの基本設定
st.set_page_config(page_title="医薬品添加物規格2018 改正一覧", page_icon="📖", layout="wide")

# カスタムCSS
st.markdown("""
    <style>
    /* === 1. 全体の余白と横ズレ完全防止 === */
    .block-container {
        padding-top: 4.8rem !important; 
        padding-bottom: 1rem !important;
        padding-left: 1.0rem !important;
        padding-right: 1.0rem !important;
        min-height: 101vh !important; 
    }
    
    /* === 2. メインタイトル === */
    .main-title {
        text-align: center !important;
        font-size: 1.8rem !important; 
        font-weight: bold !important;
        margin-top: 10px !important; 
        margin-bottom: 10px !important; 
        color: #000000 !important;
        line-height: 1.5 !important;
    }

    /* === 3. サイドバーの文字サイズ調整 === */
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        font-size: 0.85rem !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        font-size: 1.0rem !important;
    }

    /* === 4. カタカナ行ボタンの列配置 === */
    [data-testid="column"] {
        padding: 0px 2px !important;
        margin: 0px !important;
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }
    
    /* === 5. ボタンのスタイル === */
    .stButton > button {
        width: 100% !important;
        border-radius: 6px !important; 
        height: 2.4em !important;
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

    /* === 6. カスタムHTMLテーブルのスタイル（項番追加・幅固定） === */
    .table-container {
        width: 100%;
        overflow-x: auto;
        margin-top: 10px;
    }
    .custom-table {
        border-collapse: collapse;
        table-layout: fixed !important;
        /* 項番(50) + カナ(100) + 品目(850) + 改正(90x4) = 1360px で固定 */
        width: 1360px !important; 
        background-color: white;
        font-size: 14px;
        font-family: sans-serif;
    }
    .custom-table th, .custom-table td {
        border: 1px solid #e6e9ef;
        padding: 8px 12px;
        vertical-align: middle;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    .custom-table th {
        background-color: #f0f2f6;
        color: #31333F;
        font-weight: 600;
    }
    
    /* 1列目（項番）: 最小幅で中央揃え */
    .custom-table th:nth-child(1), .custom-table td:nth-child(1) {
        text-align: center;
        width: 50px !important;
    }
    /* 2列目（カタカナ行） */
    .custom-table th:nth-child(2), .custom-table td:nth-child(2) {
        text-align: center;
        width: 100px !important;
    }
    /* 3列目（品目名） */
    .custom-table th:nth-child(3), .custom-table td:nth-child(3) {
        text-align: left;
        width: 850px !important;
    }
    /* 4〜7列目（新規・R1・R4・R6） */
    .custom-table th:nth-child(n+4), .custom-table td:nth-child(n+4) {
        text-align: center;
        width: 90px !important;
    }

    /* === 7. サイドバーのチェックボックス === */
    div[data-testid="stSidebar"] .stCheckbox label {
        background-color: #ffffff;
        border: 1px solid #dcdfe6;
        border-radius: 10px !important;
        padding: 10px 16px !important;
        width: 100%;
        margin-bottom: 5px;
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

    /* === 8. 検索ウィンドウの配置調整 === */
    .stTextInput {
        margin-top: 30px !important; 
        margin-bottom: -10px !important; 
    }

    /* === 9. 検索結果件数と改正説明のレイアウト === */
    .result-info-container {
        display: flex;
        align-items: baseline;
        margin-bottom: 10px;
    }
    .result-count {
        font-size: 1rem;
    }
    .revised-explanation {
        /* ここで文字の大きさを調整できます */
        font-size: 0.875rem;
        margin-left: 20px;
        color: #000000;
    }
    </style>
    <div class="main-title">🧪医薬品添加物規格2018 改正一覧検索システム</div>
""", unsafe_allow_html=True)

def load_data():
    """SQLiteデータベースからデータを読み込み、項番を設定する"""
    if not os.path.exists(SOURCE_FILE):
        st.error(f"エラー: データベースファイル '{SOURCE_FILE}' が見つかりません。")
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

def generate_html_table(df):
    html = '<div class="table-container"><table class="custom-table">'
    html += '<thead><tr>'
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'
    for _, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            val = row[col]
            s_val = str(val) if pd.notna(val) else ""
            bg_style = ""
            if col in ['新規収載', 'R1改正', 'R4改正', 'R6改正']:
                if '〇' in s_val or s_val.startswith('R'):
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

    # --- サイドバー：フィルタ ---
    st.sidebar.header("⚙ フィルター")
    only_any_revised = st.sidebar.checkbox("いずれかの改正があった品目のみ表示")
    st.sidebar.markdown("---")
    st.sidebar.write("**特定の改正時期で絞り込む**")
    
    c_new = st.sidebar.checkbox("新規収載のみ表示")
    c_r1 = st.sidebar.checkbox("R1改正のみ表示")
    c_r4 = st.sidebar.checkbox("R4改正のみ表示")
    c_r6 = st.sidebar.checkbox("R6改正のみ表示")

    df_filtered = df.copy()
    if st.session_state.sel_kana != "全件表示":
        search_val = kana_mapping[st.session_state.sel_kana]
        df_filtered = df_filtered[df_filtered['カタカナ行'] == search_val]
            
    if search_query:
        df_filtered = df_filtered[df_filtered['品目名'].str.contains(search_query, na=False)]
    
    if only_any_revised:
        conds = []
        for col in ['R1改正', 'R4改正', 'R6改正']:
            if col in df_filtered.columns:
                conds.append(df_filtered[col].astype(str).str.contains('〇', na=False))
        if conds:
            final_any = conds[0]
            for c in conds[1:]: final_any |= c
            df_filtered = df_filtered[final_any]

    conditions = []
    if c_new: conditions.append(df_filtered['新規収載'].astype(str).str.contains('〇|R', na=False))
    if c_r1: conditions.append((df_filtered['新規収載'].astype(str).str.contains('R1', na=False)) | (df_filtered['R1改正'] == '〇'))
    if c_r4: conditions.append((df_filtered['新規収載'].astype(str).str.contains('R4', na=False)) | (df_filtered['R4改正'] == '〇'))
    if c_r6: conditions.append((df_filtered['新規収載'].astype(str).str.contains('R6', na=False)) | (df_filtered['R6改正'] == '〇'))

    if conditions:
        final_cond = conditions[0]
        for cond in conditions[1:]: final_cond |= cond
        df_filtered = df_filtered[final_cond]

    # --- 検索結果と説明文の表示 ---
    st.markdown(f"""
        <div class="result-info-container">
            <div class="result-count">📊 検索結果: <b>{len(df_filtered)}</b> 件</div>
            <div class="revised-explanation">
                R1改正：令和元年一部改正（薬生発1210第1号）&nbsp;&nbsp;
                R4改正：令和4年一部改正（薬生発0307第1号）&nbsp;&nbsp;
                R6改正：令和6年一部改正（医薬発0328第1号）
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- データ表示 ---
    display_cols = ['項番', 'カタカナ行', '品目名', '新規収載', 'R1改正', 'R4改正', 'R6改正']
    display_cols = [c for c in display_cols if c in df_filtered.columns]
    
    if not df_filtered.empty:
        html_table = generate_html_table(df_filtered[display_cols])
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.warning("該当する品目が見つかりませんでした。")

if __name__ == "__main__":
    main()