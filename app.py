import streamlit as st
import pandas as pd
import sqlite3
import os

# --- 設定項目 ---
DB_NAME = 'jp_pharmacopoeia.db'

# ページの基本設定
st.set_page_config(page_title="日本薬局方 検索システム", page_icon="📖", layout="wide")

# 固定のCSS設定（ベースのレイアウトとボタンの角丸化）
st.markdown("""
    <style>
    /* 1. 全体の余白 */
    .block-container {
        padding-top: 4.8rem !important; 
        padding-bottom: 1rem !important;
        padding-left: 1.0rem !important;
        padding-right: 1.0rem !important;
    }
    
    /* 2. タイトル */
    .main-title {
        text-align: center !important;
        font-size: 1.3rem !important; 
        font-weight: bold !important;
        margin-top: 10px !important; 
        margin-bottom: 25px !important;
        color: #1E3A8A !important;
        line-height: 1.5 !important;
    }
    
    /* 3. ボタンの列配置（角丸にするため、ほんの少しだけ隙間を作る） */
    [data-testid="column"] {
        padding: 0px 2px !important; /* 左右に2pxの隙間 */
        margin: 0px !important;
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }
    
    /* 4. ボタンのスタイル調整（角丸化） */
    .stButton > button {
        width: 100% !important;
        border-radius: 6px !important; /* 👈 角を丸くしました */
        height: 2.4em !important;
        padding: 0px 2px !important;
        font-size: 0.75rem !important;
        background-color: #f8f9fa !important;
        border: 1px solid #ced4da !important;
        margin: 0px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        transition: all 0.2s ease; /* ホバー時のアニメーション */
    }
    .stButton > button:hover {
        background-color: #e9ecef !important;
        border-color: #adb5bd !important;
    }

    /* 5. 表のヘッダー（題目）を中央揃え */
    div[data-testid="stDataFrame"] div[role="columnheader"] > div {
        justify-content: center !important;
        text-align: center !important;
        width: 100% !important;
    }
    </style>
    
    <div class="main-title">💊 第十九改正日本薬局方 新規収載・改正品検索システム</div>
    """, unsafe_allow_html=True)

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

# --- 索引データ定義（CSV不要・完全自立型） ---
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

    bounds = {"化学薬品等": build(idx_chem), "生薬等": build(idx_bio)}
    return bounds

def highlight_cells(val):
    if val == '〇': return 'background-color: #ffff00; color: black;'
    return ''

# データの読み込み
df_raw = load_data()
if df_raw.empty:
    st.error(f"❌ データベース `{DB_NAME}` が見つかりません。")
    st.stop()

if 'selected_kana' not in st.session_state:
    st.session_state.selected_kana = "全件表示"

# --- 動的なCSSの注入（選択中のボタンを赤枠にする） ---
kana_labels = ["ア行(ア～オ)", "カ行(カ～コ)", "サ行(サ～ソ)", "タ行(タ～ト)", "ナ行(ナ～ノ)", "ハ行(ハ～ホ)", "マ行(マ～モ)", "ヤ行(ヤ～ヨ)", "ラ行(ラ～ロ)", "ワ行(ワ)", "全件表示"]
active_idx = kana_labels.index(st.session_state.selected_kana) + 1 # 何番目のボタンかを取得

st.markdown(f"""
    <style>
    /* 選択されたボタンを狙い撃ちして赤枠・赤文字にする */
    [data-testid="column"]:nth-child({active_idx}) .stButton > button {{
        border: 2px solid #ff4b4b !important;
        background-color: #fff0f0 !important;
        color: #ff4b4b !important;
        font-weight: bold !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- UI: 検索エリア ---
# 虫眼鏡アイコンを枠内（プレースホルダー）に配置する代替案
search_word = st.text_input("検索", placeholder="🔍 品目名を入力してください", label_visibility="collapsed")

# カタカナボタンの配置
cols = st.columns(len(kana_labels))
for i, label in enumerate(kana_labels):
    with cols[i]:
        if st.button(label): 
            st.session_state.selected_kana = label
            st.rerun() # ボタンクリック後に状態を即座に反映させるためリラン

# サイドバー
st.sidebar.header("⚙️ フィルター設定")
selected_cats = [cat for cat in (df_raw['カテゴリー'].unique()) if st.sidebar.checkbox(cat, value=True)]
only_new, only_revised = st.sidebar.checkbox("新規収載品のみ"), st.sidebar.checkbox("改正品目のみ")

st.sidebar.subheader("行削除フィルタ")
remove_chem = st.sidebar.checkbox("「化学名」を含む行を削除")
remove_seijo = st.sidebar.checkbox("「4.生薬の性状」を含む行を削除")
remove_kanren = st.sidebar.checkbox("「関連表記」を含む行を削除")

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

# 行削除フィルタの適用
if remove_chem: 
    df_filtered = df_filtered[~((df_filtered['カテゴリー'] == '化学薬品等') & (df_filtered['変更項目'].str.contains('化学名', na=False)))]
if remove_seijo: 
    df_filtered = df_filtered[~((df_filtered['カテゴリー'] == '生薬等') & (df_filtered['変更項目'].str.contains('4.生薬の性状', na=False)))]
if remove_kanren:
    df_filtered = df_filtered[~(df_filtered['変更項目'].str.contains('関連表記', na=False))]

# 結果表示
st.write(f"📊 検索結果: **{len(df_filtered)}** 件 / 選択中: {sel_kana}")
if not df_filtered.empty:
    display_cols = ['項番', '医薬品名', '頁', '新規', '改正', '変更項目', 'カテゴリー']
    styled_df = df_filtered[display_cols].style.map(highlight_cells, subset=['新規', '改正'])
    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=800,
                 column_config={"項番": st.column_config.Column(width=65, alignment="right"),
                                "医薬品名": st.column_config.Column(width=600),
                                "頁": st.column_config.Column(width=55, alignment="center"),
                                "新規": st.column_config.Column(width=55, alignment="center"),
                                "改正": st.column_config.Column(width=55, alignment="center"),
                                "カテゴリー": st.column_config.Column(width=110, alignment="center"),
                                "変更項目": st.column_config.Column(width="large")})
else:
    st.info("条件に一致する品目が見つかりませんでした。")