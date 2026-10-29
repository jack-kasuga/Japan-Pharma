# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sqlite3
import os
import re
import html

# --- 設定項目 ---
DB_NAME = 'jp_pharmacopoeia.db'

# ページの基本設定
st.set_page_config(
    page_title="日本薬局方 検索システム",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# UIおよびCSS設定
app_css = """
<style>
/* 画面全体のスクロールバーを非表示にし、高さをビューポート内に固定 */
html, body, [data-testid="stAppViewContainer"], .main {
    overflow: hidden !important;
    height: 100% !important;
}

/* 1. 全体の余白 */
.block-container { 
    padding-top: 0.5rem !important; 
    padding-bottom: 0.8rem !important; 
    padding-left: 1.5rem !important; 
    padding-right: 1.5rem !important; 
    max-height: 100vh !important;
    box-sizing: border-box !important;
}
header[data-testid="stHeader"] { 
    background-color: transparent !important; 
    height: 1.5rem !important; 
}

/* 2. メインタイトル */
.custom-main-title { 
    font-size: 1.6rem !important; 
    font-weight: 800 !important; 
    color: #1a202c !important; 
    text-align: center !important; 
    margin-top: 0px !important; 
    margin-bottom: 8px !important; 
    line-height: 1.2 !important; 
}

/* 3. 五十音ボタンの横並び配置 */
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
    font-size: clamp(0.68rem, 0.8vw, 0.78rem) !important;
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

/* 4. レスポンシブテーブル */
.custom-table-container { 
    height: calc(100vh - 250px) !important; 
    max-height: calc(100vh - 250px) !important; 
    overflow-y: auto !important; 
    overflow-x: auto !important; 
    border: 1px solid #d0d7de; 
    border-radius: 8px; 
    margin-top: 6px;
    margin-bottom: 12px !important; 
    box-shadow: 0 2px 6px rgba(0,0,0,0.04); 
    background-color: #ffffff; 
}
.custom-table { 
    width: 100%; 
    border-collapse: collapse; 
    font-size: 13px; 
    table-layout: fixed !important; 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
}
.custom-table th { 
    position: sticky; 
    top: 0; 
    background-color: #f6f8fa; 
    color: #24292f; 
    font-weight: 600; 
    padding: 8px 10px; 
    border-bottom: 2px solid #d0d7de; 
    border-right: 1px solid #eaeef2; 
    white-space: nowrap; 
    text-align: center; 
    z-index: 20; 
    user-select: none; 
}
.custom-table th:hover { background-color: #eaeef2; }
.custom-table td { 
    padding: 7px 10px; 
    border-bottom: 1px solid #eaeef2; 
    border-right: 1px solid #f0f3f6; 
    color: #24292f; 
    vertical-align: middle; 
}
.custom-table tr:hover td { background-color: #f8fafc; }

/* 医薬品名（品目）：1行で表示 */
.col-drug-name {
    text-align: left !important;
    font-weight: 600;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    line-height: 1.35;
}

/* 5. 「〇」セル全体の黄色ハイライト */
.cell-circle-yellow {
    background-color: #ffff00 !important;
    color: #000000 !important;
    font-weight: bold !important;
    text-align: center !important;
    font-size: 14px;
}

/* 6. ホバー＆クリックで開く吹き出し（右横展開） */
.popup-container { 
    position: relative; 
    display: inline-block; 
    cursor: pointer; 
    outline: none; 
}
.popup-badge {
    color: #0969da;
    background-color: #ddf4ff;
    border: 1px solid #54aeff;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 500;
    display: inline-block;
    transition: all 0.15s ease;
    white-space: nowrap;
}
.popup-badge:hover {
    background-color: #b6e3ff;
}

/* 吹き出し本体（右横展開） */
.popup-content { 
    visibility: hidden; 
    opacity: 0;
    position: absolute;
    z-index: 9999 !important; 
    top: 50%;
    transform: translateY(-50%);
    left: calc(100% + 12px); 
    width: 480px; 
    max-width: 50vw;
    max-height: 260px;
    overflow-y: auto;
    background-color: #ffffff; 
    color: #24292f; 
    text-align: left; 
    border-radius: 8px; 
    padding: 10px 14px; 
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22); 
    border: 1px solid #0969da; 
    transition: opacity 0.2s ease, visibility 0.2s ease; 
    white-space: normal; 
    font-weight: normal; 
    line-height: 1.45; 
}
.popup-content::after { 
    content: ""; 
    position: absolute; 
    top: 50%; 
    right: 100%; 
    margin-top: -6px;
    border-width: 6px; 
    border-style: solid; 
    border-color: transparent #0969da transparent transparent; 
}

.popup-container:hover .popup-content,
.popup-container:focus .popup-content,
.popup-container:focus-within .popup-content,
.popup-container:active .popup-content { 
    visibility: visible !important; 
    opacity: 1 !important; 
}

.popup-detail-row {
    margin-bottom: 6px;
    padding-bottom: 6px;
    border-bottom: 1px dashed #e1e4e8;
}
.popup-detail-row:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
}
.popup-item-label {
    font-weight: 700;
    color: #0969da;
}
</style>
"""
st.markdown(app_css, unsafe_allow_html=True)

st.markdown('<div class="custom-main-title">💊 第十九改正日本薬局方 新規収載・改正品検索システム</div>', unsafe_allow_html=True)

# --- データベース関連関数 ---
def get_db_connection():
    if os.path.exists(DB_NAME):
        return sqlite3.connect(DB_NAME)
    return None

def load_data():
    conn = get_db_connection()
    if conn:
        df = pd.read_sql("SELECT * FROM pharmaceuticals", conn)
        if '項番（行番号）' in df.columns:
            df = df.rename(columns={'項番（行番号）': '項番'})
        for col in df.columns:
            df[col] = df[col].fillna('').astype(str)
        conn.close()
        return df
    return pd.DataFrame()

# --- 索引データ定義 ---
def load_kana_bounds():
    idx_chem = {
        'ア': 1, 'イ': 142, 'ウ': 222, 'エ': 230, 'オ': 323, 'カ': 354, 'キ': 408, 'ク': 421, 'ケ': 515, 'コ': 536,
        'サ': 556, 'シ': 585, 'ス': 686, 'セ': 732, 'ソ': 816, 'タ': 825, 'チ': 862, 'ツ': 893, 'テ': 896, 'ト': 944,
        'ナ': 1027, 'ニ': 1044, 'ネ': 1077, 'ノ': 1079, 'ハ': 1089, 'ヒ': 1143, 'フ': 1227, 'ヘ': 1404, 'ホ': 1466,
        'マ': 1494, 'ミ': 1510, 'ム': 1530, 'メ': 1532, 'モ': 1592, 'ヤ': 1606, 'ユ': 1608, 'ヨ': 1609, 'ラ': 1626,
        'リ': 1643, 'レ': 1693, 'ロ': 1717, 'ワ': 1737
    }
    idx_bio = {
        'ア': 1, 'イ': 16, 'ウ': 19, 'エ': 28, 'オ': 32, 'カ': 49, 'キ': 72, 'ク': 82, 'ケ': 86, 'コ': 98,
        'サ': 120, 'シ': 138, 'セ': 165, 'ソ': 180, 'タ': 185, 'チ': 197, 'ツ': 208, 'テ': 209, 'ト': 212,
        'ナ': 236, 'ニ': 237, 'ハ': 244, 'ヒ': 257, 'フ': 266, 'ヘ': 270, 'ホ': 274, 'マ': 291, 'ミ': 296,
        'モ': 298, 'ヤ': 301, 'ユ': 304, 'ヨ': 306, 'ラ': 310, 'リ': 313, 'レ': 321, 'ロ': 323
    }
    groups = [
        ("ア行(ア～オ)", "ア"), ("カ行(カ～コ)", "カ"), ("サ行(サ～ソ)", "サ"),
        ("タ行(タ～ト)", "タ"), ("ナ行(ナ～ノ)", "ナ"), ("ハ行(ハ～ホ)", "ハ"),
        ("マ行(マ～モ)", "マ"), ("ヤ行(ヤ～ヨ)", "ヤ"), ("ラ行(ラ～ロ)", "ラ"),
        ("ワ行(ワ)", "ワ")
    ]
    def build(idx_map):
        cat_bounds = {}
        for i in range(len(groups)):
            label, start_kana = groups[i]
            start_num = idx_map.get(start_kana, float('inf'))
            end_num = float('inf')
            for j in range(i + 1, len(groups)):
                next_kana = groups[j][1]
                if next_kana in idx_map:
                    end_num = idx_map[next_kana]
                    break
            cat_bounds[label] = (start_num, end_num)
        return cat_bounds
    return {"化学薬品等": build(idx_chem), "生薬等": build(idx_bio)}

# 変更項目の【】を安全に分割・抽出する堅牢な関数（無限ループ・バックトラック回避版）
def format_change_item(text):
    if not text or text.strip() in ['ー', '-', '']:
        return '<span style="color: #8c959f;">ー</span>'
    
    if '【' not in text:
        return html.escape(text)

    try:
        detailed_items = []
        plain_labels = []

        # 【...】の部分を安全に切り分ける
        pattern = re.compile(r'([^,、\s【]+)?\s*【(.*?)】')
        last_end = 0
        for m in pattern.finditer(text):
            # 【】の前のテキストを処理
            pre = text[last_end:m.start()].strip(' ,、')
            if pre:
                for p in re.split(r'[,、]', pre):
                    p_clean = p.strip()
                    if p_clean and p_clean != 'ー':
                        plain_labels.append(p_clean)

            label = (m.group(1) or '').strip()
            detail = m.group(2).strip()
            if label:
                plain_labels.append(label)
                detailed_items.append((label, detail))
            else:
                detailed_items.append(('詳細', detail))
            last_end = m.end()

        # 【】の後の残りテキストを処理
        post = text[last_end:].strip(' ,、')
        if post:
            for p in re.split(r'[,、]', post):
                p_clean = p.strip()
                if p_clean and p_clean != 'ー':
                    plain_labels.append(p_clean)

        if detailed_items:
            display_summary = "、".join(plain_labels) if plain_labels else "詳細あり"
            
            detail_lines_html = []
            for lbl, det in detailed_items:
                safe_lbl = html.escape(lbl)
                safe_det = html.escape(det)
                detail_lines_html.append(
                    f'<div class="popup-detail-row">'
                    f'<span class="popup-item-label">{safe_lbl}:</span> {safe_det}'
                    f'</div>'
                )
            
            inner_content = "".join(detail_lines_html)
            safe_summary = html.escape(display_summary)
            
            return (
                f'<div class="popup-container" tabindex="0">'
                f'<span class="popup-badge">💬 {safe_summary}</span>'
                f'<div class="popup-content">{inner_content}</div>'
                f'</div>'
            )
    except Exception:
        pass

    return html.escape(text)

# データの読み込み
df_raw = load_data()
if df_raw.empty:
    st.error("❌ データベースが見つかりません。")
    st.stop()

if 'selected_kana' not in st.session_state:
    st.session_state.selected_kana = "全件表示"

# 選択中ボタンの強調CSS
kana_labels = ["ア行(ア～オ)", "カ行(カ～コ)", "サ行(サ～ソ)", "タ行(タ～ト)", "ナ行(ナ～ノ)", "ハ行(ハ～ホ)", "マ行(マ～モ)", "ヤ行(ヤ～ヨ)", "ラ行(ラ～ロ)", "ワ行(ワ)", "全件表示"]
active_idx = kana_labels.index(st.session_state.selected_kana) + 1 

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

# 検索入力
search_word = st.text_input("検索", placeholder="🔍 品目名を入力してください", label_visibility="collapsed")

cols = st.columns(len(kana_labels))
for i, label in enumerate(kana_labels):
    with cols[i]:
        if st.button(label): 
            st.session_state.selected_kana = label
            st.rerun() 

# サイドバー
st.sidebar.header("⚙️ フィルター設定")
selected_cats = [cat for cat in (df_raw['カテゴリー'].unique()) if st.sidebar.checkbox(cat, value=True)]
only_new, only_revised = st.sidebar.checkbox("新規収載品のみ"), st.sidebar.checkbox("改正品目のみ")

st.sidebar.subheader("行非表示フィルター")
remove_chem = st.sidebar.checkbox("「化学名」を含む行を非表示")
remove_seijo = st.sidebar.checkbox("「4.生薬の性状」を含む行を非表示")
remove_kanren = st.sidebar.checkbox("「関連表記」を含む行を非表示")

# フィルタリング
df_filtered = df_raw.copy()
if selected_cats: df_filtered = df_filtered[df_filtered['カテゴリー'].isin(selected_cats)]
if only_new: df_filtered = df_filtered[df_filtered['新規'] == '〇']
if only_revised: df_filtered = df_filtered[df_filtered['改正'] == '〇']
if search_word: df_filtered = df_filtered[df_filtered['医薬品名'].str.contains(search_word, na=False)]

sel_kana = st.session_state.selected_kana
if sel_kana != "全件表示":
    kana_bounds = load_kana_bounds()
    kouban_num = pd.to_numeric(df_filtered['項番'].str.replace(',', ''), errors='coerce')
    mask = pd.Series(False, index=df_filtered.index)
    for cat in df_filtered['カテゴリー'].unique():
        if cat in kana_bounds and sel_kana in kana_bounds[cat]:
            start, end = kana_bounds[cat][sel_kana]
            mask |= (df_filtered['カテゴリー'] == cat) & (kouban_num >= start) & (kouban_num < end)
    df_filtered = df_filtered[mask]

# 行非表示フィルタの適用（スペースの有無に関わらず確実に除外）
if remove_chem: 
    df_filtered = df_filtered[~((df_filtered['カテゴリー'] == '化学薬品等') & (df_filtered['変更項目'].str.contains('化学名', na=False)))]
if remove_seijo: 
    df_filtered = df_filtered[~((df_filtered['カテゴリー'] == '生薬等') & (df_filtered['変更項目'].str.contains('生薬の性状', na=False)))]
if remove_kanren:
    df_filtered = df_filtered[~(df_filtered['変更項目'].str.contains('関連表記', na=False))]

# 結果件数表示
st.caption(f"表示中: **{len(df_filtered)} / {len(df_raw)} 件** （選択中: {sel_kana}）")

if not df_filtered.empty:
    rows_html = []
    for _, row in df_filtered.iterrows():
        is_new = row.get('新規') == '〇'
        new_td_class = ' class="cell-circle-yellow"' if is_new else ' style="text-align: center;"'
        new_text = '〇' if is_new else '<span style="color: #8c959f;">ー</span>'

        is_rev = row.get('改正') == '〇'
        rev_td_class = ' class="cell-circle-yellow"' if is_rev else ' style="text-align: center;"'
        rev_text = '〇' if is_rev else '<span style="color: #8c959f;">ー</span>'

        change_val = format_change_item(str(row.get('変更項目', 'ー')))

        rows_html.append(
            f'<tr>'
            f'<td style="text-align: center; color: #57606a;">{html.escape(str(row.get("項番", "")))}</td>'
            f'<td class="col-drug-name">{html.escape(str(row.get("医薬品名", "")))}</td>'
            f'<td style="text-align: center; font-size: 12px; color: #57606a;">{html.escape(str(row.get("頁", "")))}</td>'
            f'<td{new_td_class}>{new_text}</td>'
            f'<td{rev_td_class}>{rev_text}</td>'
            f'<td style="text-align: center; font-size: 12px;">{html.escape(str(row.get("カテゴリー", "")))}</td>'
            f'<td style="text-align: left;">{change_val}</td>'
            f'</tr>'
        )

    tbody_content = "".join(rows_html)
    # 幅の指定をすべて <th> 側で一元管理（テーブル全体のズレを解消）
    table_html = (
        '<div class="custom-table-container">'
        '<table class="custom-table">'
        '<thead><tr>'
        '<th style="width: 55px;">項番</th>'
        '<th style="width: 500px;">医薬品名</th>'
        '<th style="width: 85px;">頁</th>'
        '<th style="width: 50px;">新規</th>'
        '<th style="width: 50px;">改正</th>'
        '<th style="width: 95px;">カテゴリー</th>'
        '<th>変更項目</th>'
        '</tr></thead>'
        f'<tbody>{tbody_content}</tbody>'
        '</table>'
        '</div>'
    )
    
    if hasattr(st, "html"):
        st.html(table_html)
    else:
        st.markdown(table_html, unsafe_allow_html=True)
else:
    st.info("条件に一致する品目が見つかりませんでした。")