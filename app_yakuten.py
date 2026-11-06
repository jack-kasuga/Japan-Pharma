import base64
import html
import os
import re
import sqlite3
import pandas as pd
import streamlit as st

# --- 設定項目 ---
SOURCE_FILE = 'pharmaceutical_excipients.db'

# ページの基本設定
st.set_page_config(
    page_title='医薬品添加物規格 改正一覧検索システム',
    page_icon='📖',
    layout='wide',
)

# カスタムCSS
st.markdown(
    """
    <style>
    /* === 1. 全体のレイアウト設定 === */
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
    
    /* === 2. メインタイトル === */
    .custom-main-title {
        text-align: center !important;
        font-size: 1.75rem !important; 
        font-weight: 800 !important;
        margin-top: 0px !important; 
        margin-bottom: 4px !important; 
        color: #1a202c !important;
        line-height: 1.3 !important;
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

    /* === 6. 検索ウィンドウの配置調整 === */
    .stTextInput {
        margin-top: 4px !important; 
        margin-bottom: -10px !important; 
    }

    /* === 7. 検索結果件数と改正説明のレイアウト === */
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

    /* === 8. カスタムHTMLテーブル === */
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
        width: max-content !important; /* コンテナ全体への自動引き伸ばしを防止 */
        background-color: white;
        font-size: 14px;
        font-family: sans-serif;
    }
    
    /* ヘッダー固定 */
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
        padding: 6px 8px;
        vertical-align: middle;
        white-space: nowrap !important;
        overflow: visible !important;
    }
    
    /* 各列のクラス定義 */
    .col-idx { text-align: center !important; width: 50px !important; min-width: 50px !important; max-width: 50px !important; }
    .col-kana { text-align: center !important; width: 100px !important; min-width: 100px !important; max-width: 100px !important; }
    .col-name { 
        text-align: left !important; 
        width: 850px !important; 
        min-width: 850px !important;
        max-width: 850px !important;
        overflow: hidden !important; 
        text-overflow: ellipsis !important; 
    }
    .col-rev { 
        text-align: center !important; 
        width: 90px !important; 
        min-width: 90px !important;
        max-width: 90px !important;
    }

    /* === 9. ポップアップ（点線なし・すっきりバッジ） === */
    .popup-container { 
        position: relative; 
        display: inline-block; 
        cursor: pointer; 
        outline: none; 
    }
    
    .popup-badge {
        color: #0366d6;
        background-color: #f1f8ff;
        border: 1px solid #79b8ff;
        border-radius: 6px;
        padding: 2px 10px;
        font-size: 14px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .popup-badge:hover {
        background-color: #0366d6;
        color: #ffffff;
        border-color: #0366d6;
        text-decoration: none !important;
        transform: translateY(-1px);
        box-shadow: 0 3px 6px rgba(3, 102, 214, 0.25);
    }

    /* 吹き出し本体（横スクロールバー禁止・オートハイト） */
    .popup-content { 
        visibility: hidden; 
        opacity: 0;
        position: absolute;
        z-index: 9999 !important; 
        top: 50%;
        transform: translateY(-50%);
        right: calc(100% + 12px);
        width: 520px; 
        max-width: 50vw;
        height: auto !important;
        max-height: 75vh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        box-sizing: border-box !important;
        background-color: #ffffff; 
        color: #24292f; 
        text-align: left; 
        border-radius: 8px; 
        padding: 12px 16px; 
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.18), 0 2px 6px rgba(0,0,0,0.08); 
        border: 1px solid #d0d7de; 
        transition: opacity 0.2s ease, visibility 0.2s ease; 
        white-space: normal !important; 
        word-break: break-word !important;
        font-weight: normal; 
        line-height: 1.5; 
        font-size: 13px;
    }
    .popup-content::after { 
        content: ""; 
        position: absolute; 
        top: 50%; 
        left: 100%; 
        margin-top: -6px;
        border-width: 6px; 
        border-style: solid; 
        border-color: transparent transparent transparent #ffffff; 
        filter: drop-shadow(1px 0 0 #d0d7de);
    }

    .popup-container:hover .popup-content,
    .popup-container:focus .popup-content,
    .popup-container:focus-within .popup-content,
    .popup-container:active .popup-content { 
        visibility: visible !important; 
        opacity: 1 !important; 
    }

    .popup-detail-row {
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px solid #eaeef2;
    }
    .popup-detail-row:last-child {
        margin-bottom: 0;
        padding-bottom: 0;
        border-bottom: none;
    }
    .popup-item-label {
        font-weight: 700;
        color: #0969da;
        background-color: #f6f8fa;
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        margin-bottom: 4px;
        font-size: 12.5px;
        border: 1px solid #e1e4e8;
    }
    .popup-item-body {
        display: block;
        padding-left: 4px;
        color: #333333;
        font-size: 12.5px;
        line-height: 1.45;
    }

    /* === 10. サイドバーのチェックボックス === */
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
""",
    unsafe_allow_html=True,
)

# タイトルの確実なレンダリング
st.markdown('<div class="custom-main-title">🧪医薬品添加物規格 改正一覧検索システム</div>', unsafe_allow_html=True)


def load_data():
    """SQLiteデータベースからデータを読み込み、列名を標準化する"""
    if not os.path.exists(SOURCE_FILE):
        st.error(f"エラー: データベースファイル '{SOURCE_FILE}' が見つかりません。")
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(SOURCE_FILE)
        df = pd.read_sql_query('SELECT * FROM excipients', conn)
        conn.close()

        if '番号' in df.columns:
            df = df.rename(columns={'番号': '項番'})
        elif '項番' not in df.columns:
            df.insert(0, '項番', range(1, len(df) + 1))

        if '品目名' in df.columns:
            df['品目名'] = df['品目名'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f'データベースの読み込み中にエラーが発生しました: {e}')
        return pd.DataFrame()


def format_header_label(col_name):
    """ヘッダーラベルを2段表示に整形"""
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


def replace_img_tags_with_base64(text):
    """[img:ファイル名.png] を検出し、imageフォルダからBase64形式の <img> タグに置き換える"""
    if not text or '[img:' not in text:
        return text

    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_dir = os.path.join(base_dir, 'image')

    def _sub_func(match):
        img_filename = match.group(1).strip()
        img_path = os.path.join(image_dir, img_filename)

        if os.path.exists(img_path):
            with open(img_path, 'rb') as f:
                b64_data = base64.b64encode(f.read()).decode('utf-8')
            return (
                f'<br><img src="data:image/png;base64,{b64_data}" style="max-width: 100%; '
                f'height: auto; max-height: 55px; vertical-align: middle; margin: 6px 0; '
                f'display: block; border-radius: 4px; background:#fff; padding: 2px;">'
            )
        else:
            return f'<span style="color: red; font-size: 11px;">[画像が見つかりません: {img_filename}]</span>'

    return re.sub(r'\[img:([^\]]+)\]', _sub_func, text)


def format_cell_content(val, col):
    """セル内の値を整形し、【】があれば「、」で項目ごとに分割＆「：」以降を別段落にしてポップアップを生成する"""
    s_val = str(val) if pd.notna(val) else ""
    if not s_val or s_val in ['－', '-', '']:
        return '<span style="color: #8c959f;">－</span>', ""

    # 赤色指定を純原色 #ff0000 に統一
    s_val = (
        s_val.replace('#e02424', '#ff0000')
        .replace('#d73a49', '#ff0000')
        .replace('color: red', 'color: #ff0000')
    )

    m = re.search(r'【(.*?)】', s_val)
    if m:
        detail_text = m.group(1).strip()
        prefix = s_val[:m.start()].strip()
        mark = prefix if prefix else "〇"

        items = [it.strip() for it in detail_text.split('、') if it.strip()]

        detail_lines_html = []
        for it in items:
            if '：' in it:
                k, v = it.split('：', 1)
            elif ':' in it:
                k, v = it.split(':', 1)
            else:
                k, v = None, it

            if k:
                k_clean = k.strip().rstrip('」』')
                v_clean = replace_img_tags_with_base64(v.strip())
                detail_lines_html.append(
                    f'<div class="popup-detail-row">'
                    f'<span class="popup-item-label">{k_clean}</span>'
                    f'<div class="popup-item-body">{v_clean}</div>'
                    f'</div>'
                )
            else:
                v_clean = replace_img_tags_with_base64(v.strip())
                detail_lines_html.append(
                    f'<div class="popup-detail-row">'
                    f'<div class="popup-item-body">{v_clean}</div>'
                    f'</div>'
                )

        inner_content = "".join(detail_lines_html)
        cell_html = (
            f'<div class="popup-container" tabindex="0">'
            f'<span class="popup-badge">{mark}</span>'
            f'<div class="popup-content">{inner_content}</div>'
            f'</div>'
        )
        return cell_html, "background-color: #FFFF00;"

    bg_style = ""
    if any(k in col for k in ['新規', 'R1', 'R4', 'R6', '2026', '改正']):
        if '〇' in s_val or '○' in s_val or s_val.startswith('R'):
            bg_style = 'background-color: #FFFF00;'
    return s_val, bg_style


def generate_html_table(df):
    col_widths = []
    col_classes = []
    
    for col in df.columns:
        if col == '項番':
            col_widths.append(50)
            col_classes.append('col-idx')
        elif col == 'カタカナ行':
            col_widths.append(100)
            col_classes.append('col-kana')
        elif col == '品目名':
            col_widths.append(850)
            col_classes.append('col-name')
        else:
            col_widths.append(90)
            col_classes.append('col-rev')

    # <colgroup> で厳密に各列の幅を固定
    colgroup_html = '<colgroup>'
    for w in col_widths:
        colgroup_html += f'<col style="width: {w}px; min-width: {w}px; max-width: {w}px;">'
    colgroup_html += '</colgroup>'

    html_code = '<div class="table-container"><table class="custom-table">'
    html_code += colgroup_html
    html_code += '<thead><tr>'
    for idx, col in enumerate(df.columns):
        formatted_header = format_header_label(col)
        cls = col_classes[idx]
        html_code += f'<th class="{cls}">{formatted_header}</th>'
    html_code += '</tr></thead><tbody>'

    for _, row in df.iterrows():
        html_code += '<tr>'
        for idx, col in enumerate(df.columns):
            val = row[col]
            cls = col_classes[idx]
            content, bg_style = format_cell_content(val, col)

            if col == '品目名':
                s_val = str(val) if pd.notna(val) else ""
                html_code += f'<td class="{cls}" style="{bg_style}" title="{s_val}">{content}</td>'
            else:
                html_code += f'<td class="{cls}" style="{bg_style}">{content}</td>'
        html_code += '</tr>'
    html_code += '</tbody></table></div>'
    return html_code


def main():
    df = load_data()
    if df.empty:
        return

    search_query = st.text_input(
        "検索",
        placeholder="🔍 品目名を入力して検索（例：アクリル酸）",
        label_visibility="collapsed",
    )

    kana_mapping = {
        "ア行(ア～オ)": "ア行",
        "カ行(カ～コ)": "カ行",
        "サ行(サ～ソ)": "サ行",
        "タ行(タ～ト)": "タ行",
        "ナ行(ナ～ノ)": "ナ行",
        "ハ行(ハ～ホ)": "ハ行",
        "マ行(マ～モ)": "マ行",
        "ヤ行(ヤ～ヨ)": "ヤ行",
        "ラ行(ラ～ロ)": "ラ行",
        "ワ行(ワ)": "ワ行",
        "全件表示": "全件表示",
    }
    kana_labels = list(kana_mapping.keys())

    if 'sel_kana' not in st.session_state:
        st.session_state.sel_kana = "全件表示"

    active_idx = kana_labels.index(st.session_state.sel_kana) + 1
    st.markdown(
        f"""
        <style>
        [data-testid="column"]:nth-child({active_idx}) .stButton > button {{
            border: 2px solid #ff4b4b !important;
            background-color: #fff0f0 !important;
            color: #ff4b4b !important;
            font-weight: bold !important;
        }}
        </style>
    """,
        unsafe_allow_html=True,
    )

    def set_kana(label):
        st.session_state.sel_kana = label

    cols = st.columns(len(kana_labels))
    for i, label in enumerate(kana_labels):
        with cols[i]:
            st.button(label, on_click=set_kana, args=(label,))

    # カラムの自動検出
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
        df_filtered = df_filtered[
            df_filtered['品目名'].str.contains(search_query, na=False)
        ]

    # 改正対象品目を全て表示のロジック
    revision_cols = [
        c for c in [col_r1, col_r4, col_r6, col_2026] if c and c in df_filtered.columns
    ]
    if only_any_revised and revision_cols:
        conds = [
            df_filtered[c].astype(str).str.contains('〇|○', na=False)
            for c in revision_cols
        ]
        final_any = conds[0]
        for c in conds[1:]:
            final_any |= c
        df_filtered = df_filtered[final_any]

    # 個別チェックボックスによる絞り込み
    conditions = []
    if c_new and col_new:
        conditions.append(df_filtered[col_new].astype(str).str.contains('〇|○|R', na=False))
    if c_r1 and col_r1:
        conditions.append(
            (df_filtered[col_new].astype(str).str.contains('R1', na=False) if col_new else False)
            | df_filtered[col_r1].astype(str).str.contains('〇|○', na=False)
        )
    if c_r4 and col_r4:
        conditions.append(
            (df_filtered[col_new].astype(str).str.contains('R4', na=False) if col_new else False)
            | df_filtered[col_r4].astype(str).str.contains('〇|○', na=False)
        )
    if c_r6 and col_r6:
        conditions.append(
            (df_filtered[col_new].astype(str).str.contains('R6', na=False) if col_new else False)
            | df_filtered[col_r6].astype(str).str.contains('〇|○', na=False)
        )
    if c_2026 and col_2026:
        conditions.append(df_filtered[col_2026].astype(str).str.contains('〇|○', na=False))

    if conditions:
        final_cond = conditions[0]
        for cond in conditions[1:]:
            final_cond |= cond
        df_filtered = df_filtered[final_cond]

    # --- 検索結果と説明文の表示 ---
    st.markdown(
        f"""
        <div class="result-info-container">
            <div class="result-count">📊 検索結果: <b>{len(df_filtered)}</b> 件</div>
            <div class="revised-explanation">
                R1改正：令和元年一部改正&nbsp;&nbsp;
                R4改正：令和4年一部改正&nbsp;&nbsp;
                R6改正：令和6年一部改正&nbsp;&nbsp;
                2026改正：2026年一部改正
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # --- 表示列の指定 ---
    base_cols = [c for c in ['項番', 'カタカナ行', '品目名'] if c in df_filtered.columns]
    rev_cols = [
        c for c in [col_new, col_r1, col_r4, col_r6, col_2026] if c and c in df_filtered.columns
    ]
    display_cols = base_cols + rev_cols

    if len(display_cols) < 4:
        display_cols = list(df_filtered.columns)

    if not df_filtered.empty:
        html_table = generate_html_table(df_filtered[display_cols])
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.warning("該当する品目が見つかりませんでした。")


if __name__ == '__main__':
    main()