# -*- coding: utf-8 -*-
"""
PDG 医薬品各条（添加物）4局調和ステータス ダッシュボード
- 「調和作業中」の全バッジデザイン（ステータス/日付/詳細項目）を完全統一
- カード表示の一括開閉（🔼 すべて閉じる / 🔽 すべて開く）
- 4局横並びの段ずれ完全解消（水平同期）
- 【不採用項目】【独自例外】見出しの視認性強化
- 調和中止アイコンをバツマーク（❌）に変更
- サイドバー参照版注記の左端配置
- 調和状況チェックボックスの双方向連動＆件数【〇】表示
- E-55 3段表示・セル幅最適化
- 単一マスターCSV(pdg_excipients_3regions_ja.csv)の直接読み込み
"""

import os
import re
import html
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="PDG 4局調和ステータス(医薬品添加物)",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

def find_col(columns, keywords):
    for c in columns:
        for kw in keywords:
            if kw.lower() in c.lower():
                return c
    return None

@st.cache_data
def load_data():
    target_csv = "pdg_excipients_3regions_ja.csv"

    if not os.path.exists(target_csv):
        return pd.DataFrame()

    try:
        df = pd.read_csv(target_csv, encoding="utf-8-sig", dtype=str)
        df.columns = [c.replace("\ufeff", "").strip() for c in df.columns]
        df = df.fillna("ー")

        if "コード" not in df.columns:
            c_col = find_col(df.columns, ["コード", "code"])
            df["コード"] = df[c_col] if c_col else [f"E-{i+1:02d}" for i in range(len(df))]

        if "品目名(日本語)" not in df.columns:
            n_col = find_col(df.columns, ["品目名", "添加物名", "試験法名"])
            df["品目名(日本語)"] = df[n_col] if n_col else "ー"

        if "PDG 品目名" not in df.columns:
            en_col = find_col(df.columns, ["pdg", "英語名", "英名"])
            df["PDG 品目名"] = df[en_col] if en_col else "ー"

        if "全体調和ステータス" not in df.columns:
            df["全体調和ステータス"] = "調和（局間差異あり）"
        if "非調和属性" not in df.columns:
            df["非調和属性"] = "なし"
        if "サインオフ日" not in df.columns:
            df["サインオフ日"] = "ー"
        if "施行日" not in df.columns:
            df["施行日"] = "ー"
        if "PMDA_PDF_URL" not in df.columns:
            df["PMDA_PDF_URL"] = "ー"

        def extract_num(val):
            m = re.search(r"\d+", str(val))
            return int(m.group()) if m else 999

        df["_sort_num"] = df["コード"].apply(extract_num)
        df = df.sort_values(by="_sort_num", ascending=True).drop(columns=["_sort_num"])

        def determine_harmonization_status(row):
            raw_status = str(row.get("全体調和ステータス", "")).replace("極間", "局間")
            if "作業中" in raw_status or "未確定" in raw_status or str(row.get("品目名(日本語)", "")).startswith("調和作業中"):
                return "調和作業中"
            if "中止" in raw_status or "削除" in raw_status or "非調和" in raw_status:
                return "調和中止（非調和）"
            if "一部調和" in raw_status or "局間差異" in raw_status or "差異" in raw_status or "局間の差異" in raw_status:
                return "調和（局間差異あり）"

            ip_reject = str(row.get("🇮🇳 IP不採用項目", "")).strip()
            if ip_reject in ["なし", "ー", ""]:
                return "4局調和（IP反映済）"
            else:
                return "3局完全調和（IP未反映）"

        df["表示調和ステータス"] = df.apply(determine_harmonization_status, axis=1)
        return df
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return pd.DataFrame()

def main():
    app_css = """
    <style>
    .block-container {
        padding-top: 0.2rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        height: 2.2rem !important;
    }
    .custom-main-title {
        font-size: 1.75rem !important;
        font-weight: 800 !important;
        color: #1a202c !important;
        text-align: center !important;
        margin-top: 0px !important;
        margin-bottom: 2px !important;
        line-height: 1.3 !important;
    }
    .custom-main-caption {
        font-size: 0.85rem !important;
        color: #64748b !important;
        text-align: center !important;
        margin-top: 0px !important;
        margin-bottom: 8px !important;
    }
    
    .custom-table-container {
        max-height: calc(100vh - 160px);
        overflow-y: auto;
        overflow-x: auto;
        border: 1px solid #d0d7de;
        border-radius: 8px;
        margin-bottom: 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        background-color: #ffffff;
    }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12.5px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .custom-table th {
        position: sticky;
        top: 0;
        background-color: #f6f8fa;
        color: #24292f;
        font-weight: 600;
        padding: 7px 8px;
        border-bottom: 2px solid #d0d7de;
        border-right: 1px solid #eaeef2;
        white-space: nowrap;
        text-align: center;
        z-index: 2;
        user-select: none;
    }
    .custom-table th:hover { background-color: #eaeef2; }
    .custom-table td {
        padding: 6px 8px;
        border-bottom: 1px solid #eaeef2;
        border-right: 1px solid #f0f3f6;
        color: #24292f;
        vertical-align: middle;
        text-align: center;
    }
    .custom-table tr:hover td { background-color: #f8fafc; }
    
    .sticky-col1 {
        position: sticky !important;
        left: 0;
        min-width: 60px;
        max-width: 60px;
        white-space: nowrap;
        font-weight: 600;
        text-align: center;
        box-sizing: border-box;
    }
    .sticky-col2 {
        position: sticky !important;
        left: 60px;
        min-width: 230px; 
        box-shadow: 3px 0 5px -2px rgba(0,0,0,0.1);
        box-sizing: border-box;
    }
    .custom-table td.sticky-col1, .custom-table td.sticky-col2 {
        background-color: #fff;
        z-index: 1;
    }
    .custom-table th.sticky-col1, .custom-table th.sticky-col2 {
        background-color: #f6f8fa !important;
        z-index: 4 !important;
    }
    .custom-table tr:hover td.sticky-col1, .custom-table tr:hover td.sticky-col2 {
        background-color: #f2f7fc;
    }
    
    .col-status { white-space: normal; text-align: center; line-height: 1.35; min-width: 155px; } 
    .col-date { white-space: normal; text-align: center; font-size: 12px; line-height: 1.35; min-width: 125px; } 
    .col-detail { white-space: nowrap; text-align: center; min-width: 80px; position: relative; }
    
    .sub-text {
        font-size: 0.7rem;
        color: #57606a;
        display: block;
        margin-top: 2px;
    }

    .popup-container {
        position: relative;
        display: inline-block;
        cursor: pointer;
        outline: none;
    }
    .text-red-active {
        color: #ff0000 !important;
        font-weight: 700;
        font-size: 13px;
        text-decoration: none !important;
        padding: 2px 6px;
    }
    .text-gray-active {
        color: #64748b !important;
        font-weight: 600;
        font-size: 12px;
        text-decoration: none !important;
        padding: 2px 4px;
    }

    .badge-in-progress {
        background-color: #ede9fe !important;
        color: #5b21b6 !important;
        border: 1px solid #c4b5fd !important;
        padding: 3px 8px !important;
        border-radius: 6px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        display: inline-block !important;
        line-height: 1.35 !important;
        white-space: nowrap !important;
        box-sizing: border-box !important;
    }
    .text-none { color: #8c959f; font-size: 12px; }

    .popup-content {
        visibility: hidden;
        width: 450px;
        background-color: #fff;
        color: #333;
        text-align: left;
        border-radius: 6px;
        padding: 12px;
        position: absolute;
        z-index: 100;
        top: 125%; 
        left: 50%;
        margin-left: -225px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border: 1px solid #ccc;
        opacity: 0;
        transition: opacity 0.2s;
        white-space: normal;
        font-weight: normal;
        line-height: 1.4;
    }
    .popup-content::after {
        content: "";
        position: absolute;
        bottom: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: transparent transparent #ccc transparent;
    }

    .popup-container:focus .popup-content,
    .popup-container:focus-within .popup-content,
    .popup-container:active .popup-content,
    .popup-container:hover .popup-content {
        visibility: visible;
        opacity: 1;
    }

    .status-badge-4p { background-color: #ddf4ff; color: #0969da; border: 1px solid #54aeff; padding: 4px 8px; border-radius: 8px; font-size: 12px; font-weight: 600; display: inline-block; line-height: 1.3; }
    .status-badge-3p { background-color: #dafbe1; color: #1a7f37; padding: 4px 8px; border-radius: 8px; font-size: 12px; font-weight: 500; display: inline-block; line-height: 1.3; }
    .status-badge-diff { background-color: #fff8c5; color: #9a6700; padding: 4px 8px; border-radius: 8px; font-size: 12px; font-weight: 500; display: inline-block; line-height: 1.3; }
    .status-badge-discontinued { background-color: #f1f3f5; color: #495057; border: 1px solid #ced4da; padding: 4px 8px; border-radius: 8px; font-size: 12px; font-weight: 600; display: inline-block; line-height: 1.3; }

    .icon-legend {
        font-size: 0.85rem;
        color: #4a5568;
        display: flex;
        gap: 15px;
        align-items: center;
        justify-content: flex-end;
    }
    
    .stCheckbox { margin-bottom: -10px; }

    [data-testid="stExpander"] summary p {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }
    </style>
    """
    st.markdown(app_css, unsafe_allow_html=True)

    st.markdown(
        '<div class="custom-main-title">🌐 PDG 4局調和ステータス(医薬品添加物)</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="custom-main-caption">日本薬局方(JP)、米国薬局方(USP)、欧州薬局方(EP)、インド薬局方(IP)の4局における添加物モノグラフの調和状況およびローカル要件一覧</div>',
        unsafe_allow_html=True,
    )

    df = load_data()
    if df.empty:
        st.warning("表示できるデータがありません。マスターデータ(pdg_excipients_3regions_ja.csv)を確認してください。")
        return

    st.sidebar.header("⚙️ 検索・設定")
    search_query = st.sidebar.text_input("🔍 検索", "", placeholder="コード、品目名など")

    st.sidebar.markdown("**調和状況**")
    
    status_options = [
        "4局調和（IP反映済）",
        "3局完全調和（IP未反映）",
        "調和（局間差異あり）",
        "調和作業中",
        "調和中止（非調和）",
    ]

    status_counts = df["表示調和ステータス"].value_counts().to_dict()
    total_count = len(df)

    if "cb_all" not in st.session_state:
        st.session_state["cb_all"] = True
    for opt in status_options:
        key = f"cb_{opt}"
        if key not in st.session_state:
            st.session_state[key] = True

    def on_all_change():
        val = st.session_state["cb_all"]
        for opt in status_options:
            st.session_state[f"cb_{opt}"] = val

    def on_item_change():
        all_checked = all(st.session_state.get(f"cb_{opt}", False) for opt in status_options)
        st.session_state["cb_all"] = all_checked

    st.sidebar.checkbox(
        f"すべて【{total_count}】",
        key="cb_all",
        on_change=on_all_change
    )

    selected_statuses = []
    for opt in status_options:
        count = status_counts.get(opt, 0)
        is_chk = st.sidebar.checkbox(
            f"{opt}【{count}】",
            key=f"cb_{opt}",
            on_change=on_item_change
        )
        if is_chk:
            selected_statuses.append(opt)

    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    sort_options = ["コード順（E-01 → E-72）", "最新サインオフ日順", "施行時期順", "品目名順"]
    selected_sort = st.sidebar.selectbox("並び替え", sort_options)

    view_mode = st.sidebar.radio(
        "表示スタイル", ["📊 一覧表", "🗂️ カード"], horizontal=True, key="app_view_toggle"
    )

    st.sidebar.divider()
    with st.sidebar.expander("ℹ️ 参照版に関する注記", expanded=True):
        st.markdown(
            """
* 🇯🇵 **JP**: JP18 / JP19追補
* 🇺🇸 **USP**: USP-NF 2026
* 🇪🇺 **EP**: 11th Ed.
* 🇮🇳 **IP**: IP 2022

<div style="font-size: 0.72rem; color: #64748b; margin-top: 6px; text-align: left;">
    ※合意書にIP欄なしは「調和対象外」扱い
</div>
            """,
            unsafe_allow_html=True,
        )

    filtered_df = df.copy()
    if search_query:
        q = search_query.strip().lower()
        mask = (
            filtered_df["コード"].astype(str).str.lower().str.contains(q, na=False)
            | filtered_df["品目名(日本語)"].astype(str).str.lower().str.contains(q, na=False)
            | filtered_df["PDG 品目名"].astype(str).str.lower().str.contains(q, na=False)
        )
        filtered_df = filtered_df[mask]

    if selected_statuses:
        filtered_df = filtered_df[filtered_df["表示調和ステータス"].isin(selected_statuses)]
    else:
        filtered_df = filtered_df.iloc[0:0]

    if selected_sort == "コード順（E-01 → E-72）":
        def extract_num(val):
            m = re.search(r"\d+", str(val))
            return int(m.group()) if m else 999
        filtered_df["_s"] = filtered_df["コード"].apply(extract_num)
        filtered_df = filtered_df.sort_values(by="_s", ascending=True).drop(columns=["_s"])
    elif selected_sort == "最新サインオフ日順":
        filtered_df = filtered_df.sort_values(by="サインオフ日", ascending=False)
    elif selected_sort == "施行時期順":
        filtered_df = filtered_df.sort_values(by="施行日", ascending=False)
    elif selected_sort == "品目名順":
        filtered_df = filtered_df.sort_values(by="品目名(日本語)", ascending=True)

    col_info1, col_info2 = st.columns([1, 2])
    with col_info1:
        st.caption(f"表示中: **{len(filtered_df)} / {len(df)} 件**")
    with col_info2:
        if view_mode == "🗂️ カード":
            st.markdown(
                """
                <div class="icon-legend">
                    <span>🌐 4局調和</span>
                    <span>✅ 3局完全調和</span>
                    <span>⚠️ 調和（局間差異あり）</span>
                    <span>🟣 作業中</span>
                    <span>❌ 調和中止</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    display_columns = [
        ("コード", "コード"),
        ("品目名(日本語)", "品目名"),
        ("表示調和ステータス", "ステータス"),
        ("サインオフ日", "サインオフ"),
        ("施行日", "施行日"),
        ("非調和属性", "非調和属性"),
        ("🇯🇵 JP不採用項目", "JP 不採用"),
        ("🇯🇵 JP独自例外", "JP 例外"),
        ("🇺🇸 USP不採用項目", "US USP 不採用"),
        ("🇺🇸 USP独自例外", "US USP 例外"),
        ("🇪🇺 EP不採用項目", "EU EP 不採用"),
        ("🇪🇺 EP独自例外", "EU EP 例外"),
        ("🇮🇳 IP不採用項目", "IN IP 不採用"),
        ("🇮🇳 IP独自例外", "IN IP 例外"),
    ]

    def format_split_text(val):
        val = str(val)
        if val in ["なし", "ー", "", "nan", "None"]:
            return val
            
        third_line = ""
        target_str = "(gelling grade and non-gelling grade)"
        if target_str in val:
            val = val.replace(f" {target_str}", "").replace(target_str, "").replace("))", ")")
            third_line = f"<span class='sub-text'>{target_str}</span>"
            
        if "（" in val:
            parts = val.split("（", 1)
            val = f"{parts[0].strip()}<span class='sub-text'>（{parts[1].strip()}</span>"
        elif "(" in val:
            parts = val.split("(", 1)
            val = f"{parts[0].strip()}<span class='sub-text'>({parts[1].strip()}</span>"
            
        return val + third_line

    if view_mode == "📊 一覧表":
        th_html = "".join([f"<th>{label}</th>" for _, label in display_columns])

        html_rows = []
        for _, row in filtered_df.iterrows():
            cells = []
            row_status = row.get("表示調和ステータス", "")
            is_in_progress_row = (row_status == "調和作業中")

            for col_key, _ in display_columns:
                val = str(row.get(col_key, "ー")).strip()
                if not val or val == "nan":
                    val = "ー"

                tooltip_val = html.escape(val, quote=True).replace("&#10;", "<br>").replace("\n", "<br>")
                text_val = val.replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", " ")

                if col_key == "コード":
                    cells.append(f'<td class="sticky-col1">{text_val}</td>')
                elif col_key == "品目名(日本語)":
                    cells.append(f'<td class="sticky-col2">{text_val}</td>')
                elif col_key == "表示調和ステータス":
                    if is_in_progress_row or "作業中" in val:
                        cells.append('<td class="col-status"><span class="badge-in-progress">調和作業中</span></td>')
                    else:
                        formatted_status = format_split_text(text_val)
                        if "4局調和" in val: b_class = "status-badge-4p"
                        elif "3局完全調和" in val: b_class = "status-badge-3p"
                        elif "中止" in val: b_class = "status-badge-discontinued"
                        else: b_class = "status-badge-diff"
                        cells.append(f'<td class="col-status"><span class="{b_class}">{formatted_status}</span></td>')
                elif col_key in ["サインオフ日", "施行日"]:
                    if is_in_progress_row or "作業中" in val:
                        cells.append('<td class="col-date"><span class="badge-in-progress">調和作業中</span></td>')
                    else:
                        cells.append(f'<td class="col-date">{format_split_text(text_val)}</td>')
                else:
                    if is_in_progress_row or "作業中" in val:
                        cells.append(f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="badge-in-progress">調和作業中</span><span class="popup-content"><b>【詳細】</b><br>{tooltip_val if tooltip_val not in ["なし", "ー"] else "調和作業中（合意文書未策定）"}</span></div></td>')
                    elif val in ["なし", "ー", ""] or "完全調和" in val:
                        cells.append('<td class="text-none">なし</td>')
                    elif "作業中止" in val or "計画削除" in val:
                        cells.append(f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="text-gray-active">計画削除</span><span class="popup-content"><b>【詳細】</b><br>{tooltip_val}</span></div></td>')
                    elif "調和対象外" in val:
                        cells.append(f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="text-gray-active">対象外</span><span class="popup-content"><b>【詳細】</b><br>{tooltip_val}</span></div></td>')
                    elif val.startswith("非調和（") or "合意文書にIP記載なし" in val:
                        cells.append(f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="text-gray-active">非調和</span><span class="popup-content"><b>【詳細】</b><br>{tooltip_val}</span></div></td>')
                    else:
                        cells.append(f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="text-red-active">あり</span><span class="popup-content"><b>【詳細】</b><br>{tooltip_val}</span></div></td>')

            html_rows.append(f"<tr>{''.join(cells)}</tr>")

        full_html = (
            f'<div class="custom-table-container">'
            f'<table class="custom-table">'
            f'<thead><tr>{th_html}</tr></thead>'
            f'<tbody>{"".join(html_rows)}</tbody>'
            f'</table>'
            f'</div>'
        )
        st.markdown(full_html, unsafe_allow_html=True)

    elif view_mode == "🗂️ カード":
        if "all_cards_expanded" not in st.session_state:
            st.session_state["all_cards_expanded"] = False

        btn_c1, btn_c2, _ = st.columns([1.2, 1.2, 6])
        with btn_c1:
            if st.button("🔼 すべて閉じる", use_container_width=True):
                st.session_state["all_cards_expanded"] = False
                st.rerun()
        with btn_c2:
            if st.button("🔽 すべて開く", use_container_width=True):
                st.session_state["all_cards_expanded"] = True
                st.rerun()

        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        for _, row in filtered_df.iterrows():
            status_val = row.get("表示調和ステータス", "")
            if "4局調和" in status_val: icon = "🌐"
            elif "3局完全調和" in status_val: icon = "✅"
            elif "作業中" in status_val: icon = "🟣"
            elif "中止" in status_val: icon = "❌"
            else: icon = "⚠️"

            with st.expander(
                f"{row['コード']} : {row['品目名(日本語)']} （{status_val}） {icon}",
                expanded=st.session_state["all_cards_expanded"]
            ):
                c_left, c_right = st.columns([3, 1])

                with c_left:
                    m1, m2, m3 = st.columns(3)
                    
                    sign_val = row.get('サインオフ日', 'ー')
                    eff_val = row.get('施行日', 'ー')
                    
                    if status_val == "調和作業中" or "作業中" in str(sign_val):
                        sign_disp = "<span class='badge-in-progress'>調和作業中</span>"
                    else:
                        sign_disp = f"<code style='font-size: 0.92rem;'>{sign_val}</code>"

                    if status_val == "調和作業中" or "作業中" in str(eff_val):
                        eff_disp = "<span class='badge-in-progress'>調和作業中</span>"
                    else:
                        eff_disp = f"<code style='font-size: 0.92rem;'>{eff_val}</code>"

                    m1.markdown(
                        f"<div style='font-size: 0.95rem; margin-bottom: 6px;'>"
                        f"英語名: <code style='font-size: 0.95rem;'>{row.get('PDG 品目名', 'ー')}</code></div>",
                        unsafe_allow_html=True
                    )
                    m2.markdown(
                        f"<div style='font-size: 0.95rem; margin-bottom: 6px;'>"
                        f"サインオフ: {sign_disp}</div>",
                        unsafe_allow_html=True
                    )
                    m3.markdown(
                        f"<div style='font-size: 0.95rem; margin-bottom: 6px;'>"
                        f"日局施行: {eff_disp}</div>",
                        unsafe_allow_html=True
                    )

                    non_harm = str(row.get("非調和属性", "なし"))
                    if status_val == "調和作業中" or "作業中" in non_harm:
                        st.info("**【全局共通 非調和属性 (Non-harmonised)】**\n\n調和作業中")
                    elif non_harm not in ["なし", "ー", ""]:
                        st.warning(f"**【全局共通 非調和属性 (Non-harmonised)】**\n\n{non_harm}")
                    else:
                        st.success("**【全局共通 非調和属性 (Non-harmonised)】**: なし（調和属性は完全合意）")

                with c_right:
                    pmda_url = str(row.get("PMDA_PDF_URL", "")).strip()
                    pdf_filename = str(row.get("元ファイル名", "")).strip()
                    if pmda_url and pmda_url.startswith("http"):
                        st.markdown(f"📄 **[PMDA公式 合意PDFを開く ↗]({pmda_url})**")
                    elif pdf_filename and pdf_filename not in ["なし", "nan", "ー", ""]:
                        st.caption(f"ローカル保存ファイル: `{pdf_filename}`")
                    else:
                        st.caption("合意文書なし（計画削除／作業中）")

                st.markdown("<hr style='margin: 12px 0 16px 0;'>", unsafe_allow_html=True)
                
                lbl_not = "<div style='font-size: 0.88rem; font-weight: 700; color: #9a3412; background: #ffedd5; padding: 2px 8px; border-radius: 4px; display: inline-block; margin-bottom: 6px;'>【不採用項目】</div>"
                lbl_exc = "<div style='font-size: 0.88rem; font-weight: 700; color: #1e40af; background: #dbeafe; padding: 2px 8px; border-radius: 4px; display: inline-block; margin-bottom: 6px;'>【独自例外（非調和部）】</div>"
                lbl_ep_exc = "<div style='font-size: 0.88rem; font-weight: 700; color: #1e40af; background: #dbeafe; padding: 2px 8px; border-radius: 4px; display: inline-block; margin-bottom: 6px;'>【独自例外 / FRCs】</div>"

                h_jp, h_usp, h_ep, h_ip = st.columns(4)
                h_jp.markdown("##### 🇯🇵 JP (JP18/19)")
                h_usp.markdown("##### 🇺🇸 USP (USP-NF)")
                h_ep.markdown("##### 🇪🇺 EP (11th Ed.)")
                h_ip.markdown("##### 🇮🇳 IP (IP 2022)")

                r1_jp, r1_usp, r1_ep, r1_ip = st.columns(4)
                
                def render_card_item(val, default_type="info"):
                    if status_val == "調和作業中" or "作業中" in str(val):
                        st.info("調和作業中")
                    elif str(val) not in ["なし", "ー", "", "nan"]:
                        if default_type == "warning":
                            st.warning(str(val))
                        else:
                            st.info(str(val))
                    else:
                        st.write("なし")

                with r1_jp:
                    st.markdown(lbl_not, unsafe_allow_html=True)
                    render_card_item(row.get("🇯🇵 JP不採用項目", "なし"), "warning")

                with r1_usp:
                    st.markdown(lbl_not, unsafe_allow_html=True)
                    render_card_item(row.get("🇺🇸 USP不採用項目", "なし"), "warning")

                with r1_ep:
                    st.markdown(lbl_not, unsafe_allow_html=True)
                    render_card_item(row.get("🇪🇺 EP不採用項目", "なし"), "warning")

                with r1_ip:
                    st.markdown(lbl_not, unsafe_allow_html=True)
                    render_card_item(row.get("🇮🇳 IP不採用項目", "なし"), "warning")

                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

                r2_jp, r2_usp, r2_ep, r2_ip = st.columns(4)
                
                with r2_jp:
                    st.markdown(lbl_exc, unsafe_allow_html=True)
                    render_card_item(row.get("🇯🇵 JP独自例外", "なし"), "info")

                with r2_usp:
                    st.markdown(lbl_exc, unsafe_allow_html=True)
                    render_card_item(row.get("🇺🇸 USP独自例外", "なし"), "info")

                with r2_ep:
                    st.markdown(lbl_ep_exc, unsafe_allow_html=True)
                    render_card_item(row.get("🇪🇺 EP独自例外", "なし"), "info")

                with r2_ip:
                    st.markdown(lbl_exc, unsafe_allow_html=True)
                    render_card_item(row.get("🇮🇳 IP独自例外", "なし"), "info")

if __name__ == "__main__":
    main()