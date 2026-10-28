# -*- coding: utf-8 -*-
"""
PDG 試験法 4局調和ステータス ダッシュボード
- 添加物版 (app_excipients.py) と完全同等のUI仕様に統一
- カード表示の一括開閉（🔼 すべて閉じる / 🔽 すべて開く）
- 4局横並びカードレイアウト（タブ廃止）
- 調和状況チェックボックスの双方向連動＆件数【〇】表示
- PDFファイル/サイトへのリンク表示機能
- 【最適化】単一マスターCSV(pdg_extracted_3regions_ja.csv)の直接読み込み
"""

import os
import re
import html
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="PDG 4局調和ステータス(試験法)",
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
    target_csv = "pdg_extracted_3regions_ja.csv"

    if not os.path.exists(target_csv):
        return pd.DataFrame()

    try:
        df = pd.read_csv(target_csv, encoding="utf-8-sig", dtype=str)
        df.columns = [c.replace("\ufeff", "").strip() for c in df.columns]
        df = df.fillna("ー")

        if "試験法名(英語)" not in df.columns:
            if "PDG 試験法名" in df.columns:
                df["試験法名(英語)"] = df["PDG 試験法名"]
            else:
                df["試験法名(英語)"] = "ー"

        if "サインオフ日" not in df.columns: df["サインオフ日"] = "ー"
        if "施行日" not in df.columns: df["施行日"] = "ー"
        if "PMDA_PDF_URL" not in df.columns: df["PMDA_PDF_URL"] = "ー"

        def extract_code_order(code):
            code_str = str(code).upper()
            prefix = 9
            if code_str.startswith("B"): prefix = 1
            elif code_str.startswith("G"): prefix = 2
            elif code_str.startswith("Q"): prefix = 3
            
            m = re.search(r"\d+", code_str)
            num = int(m.group()) if m else 999
            return (prefix, num)

        df["_sort_key"] = df["コード"].apply(extract_code_order)
        df = df.sort_values(by="_sort_key", ascending=True).drop(columns=["_sort_key"])

        def determine_harmonization_status(row):
            raw_status = str(row.get("全体調和ステータス", "")).replace("極間", "局間")
            
            if "中止" in raw_status or "削除" in raw_status or "非調和" in raw_status or "作業中止" in str(row.get("サインオフ日", "")):
                return "調和中止（非調和）"
            
            if "一部調和" in raw_status or "局間差異" in raw_status or "差異" in raw_status:
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
    .block-container { padding-top: 0.2rem !important; padding-bottom: 1.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
    header[data-testid="stHeader"] { background-color: transparent !important; height: 2.2rem !important; }
    .custom-main-title { font-size: 1.75rem !important; font-weight: 800 !important; color: #1a202c !important; text-align: center !important; margin-top: 0px !important; margin-bottom: 2px !important; line-height: 1.3 !important; }
    .custom-main-caption { font-size: 0.85rem !important; color: #64748b !important; text-align: center !important; margin-top: 0px !important; margin-bottom: 8px !important; }
    
    .custom-table-container { max-height: calc(100vh - 160px); overflow-y: auto; overflow-x: auto; border: 1px solid #d0d7de; border-radius: 8px; margin-bottom: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); background-color: #ffffff; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 12.5px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .custom-table th { position: sticky; top: 0; background-color: #f6f8fa; color: #24292f; font-weight: 600; padding: 7px 8px; border-bottom: 2px solid #d0d7de; border-right: 1px solid #eaeef2; white-space: nowrap; text-align: center; z-index: 2; user-select: none; }
    .custom-table th:hover { background-color: #eaeef2; }
    .custom-table td { padding: 6px 8px; border-bottom: 1px solid #eaeef2; border-right: 1px solid #f0f3f6; color: #24292f; vertical-align: middle; text-align: center; }
    .custom-table tr:hover td { background-color: #f8fafc; }
    
    .sticky-col1 { position: sticky !important; left: 0; min-width: 65px; max-width: 65px; white-space: nowrap; font-weight: 600; text-align: center; box-sizing: border-box; }
    .sticky-col2 { position: sticky !important; left: 65px; min-width: 200px; max-width: 200px; box-shadow: 3px 0 5px -2px rgba(0,0,0,0.1); box-sizing: border-box; }
    .custom-table td.sticky-col1, .custom-table td.sticky-col2 { background-color: #fff; z-index: 1; }
    .custom-table th.sticky-col1, .custom-table th.sticky-col2 { background-color: #f6f8fa !important; z-index: 4 !important; }
    .custom-table tr:hover td.sticky-col1, .custom-table tr:hover td.sticky-col2 { background-color: #f2f7fc; }
    
    .col-num { white-space: nowrap; text-align: center; font-weight: 500; color: #0969da; }
    .col-status { white-space: normal; text-align: center; line-height: 1.35; min-width: 145px; } 
    .col-date { white-space: normal; text-align: center; font-size: 12px; line-height: 1.35; min-width: 110px; } 
    .col-detail { white-space: nowrap; text-align: center; min-width: 75px; position: relative; }
    
    .popup-container { position: relative; display: inline-block; cursor: pointer; outline: none; }
    .text-red-active { color: #ff0000 !important; font-weight: 700; font-size: 13px; text-decoration: none !important; padding: 2px 6px; }
    .text-gray-active { color: #64748b !important; font-weight: 600; font-size: 12px; text-decoration: none !important; padding: 2px 4px; }

    .popup-content { visibility: hidden; width: 450px; background-color: #fff; color: #333; text-align: left; border-radius: 6px; padding: 12px; position: absolute; z-index: 100; top: 125%; left: 50%; margin-left: -225px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border: 1px solid #ccc; opacity: 0; transition: opacity 0.2s; white-space: normal; font-weight: normal; line-height: 1.4; }
    .popup-content::after { content: ""; position: absolute; bottom: 100%; left: 50%; margin-left: -5px; border-width: 5px; border-style: solid; border-color: transparent transparent #ccc transparent; }
    .popup-container:focus .popup-content, .popup-container:focus-within .popup-content, .popup-container:active .popup-content, .popup-container:hover .popup-content { visibility: visible; opacity: 1; }

    .status-badge-4p { background-color: #ddf4ff; color: #0969da; border: 1px solid #54aeff; padding: 4px 8px; border-radius: 8px; font-size: 12px; font-weight: 600; display: inline-block; line-height: 1.3; }
    .status-badge-3p { background-color: #dafbe1; color: #1a7f37; padding: 4px 8px; border-radius: 8px; font-size: 12px; font-weight: 500; display: inline-block; line-height: 1.3; }
    .status-badge-diff { background-color: #fff8c5; color: #9a6700; padding: 4px 8px; border-radius: 8px; font-size: 12px; font-weight: 500; display: inline-block; line-height: 1.3; }
    .status-badge-discontinued { background-color: #f1f3f5; color: #495057; border: 1px solid #ced4da; padding: 4px 8px; border-radius: 8px; font-size: 12px; font-weight: 600; display: inline-block; line-height: 1.3; }

    .icon-legend { font-size: 0.85rem; color: #4a5568; display: flex; gap: 15px; align-items: center; justify-content: flex-end; }
    .stCheckbox { margin-bottom: -10px; }
    [data-testid="stExpander"] summary p { font-size: 1.05rem !important; font-weight: 700 !important; color: #1e293b !important; }
    .ip-note { font-size: 0.7rem; color: #64748b; white-space: nowrap; margin-top: 4px; display: inline-block; }
    </style>
    """
    st.markdown(app_css, unsafe_allow_html=True)

    st.markdown('<div class="custom-main-title">🌐 PDG 4局調和ステータス(試験法)</div>', unsafe_allow_html=True)
    st.markdown('<div class="custom-main-caption">日本薬局方(JP)、米国薬局方(USP)、欧州薬局方(EP)、インド薬局方(IP)の4局における調和状況およびローカル要件一覧</div>', unsafe_allow_html=True)

    df = load_data()
    if df.empty:
        st.warning("表示できるデータがありません。マスターデータ(pdg_extracted_3regions_ja.csv)を確認してください。")
        return

    jp_no_col = find_col(df.columns, ["jp番号", "jp各条", "jp章"])
    usp_no_col = find_col(df.columns, ["usp番号", "usp各条", "usp章"])
    ep_no_col = find_col(df.columns, ["ep番号", "ep各条", "ep章"])
    ip_no_col = find_col(df.columns, ["ip番号", "ip各条", "ip章"])

    st.sidebar.header("⚙️ 検索・設定")
    search_query = st.sidebar.text_input("🔍 検索", "", placeholder="コード、試験法名など")

    st.sidebar.markdown("**調和状況**")
    status_options = [
        "4局調和（IP反映済）",
        "3局完全調和（IP未反映）",
        "調和（局間差異あり）",
        "調和中止（非調和）",
    ]
    status_counts = df["表示調和ステータス"].value_counts().to_dict()
    total_count = len(df)

    if "cb_all_test" not in st.session_state:
        st.session_state["cb_all_test"] = True
    for opt in status_options:
        key = f"cb_test_{opt}"
        if key not in st.session_state:
            st.session_state[key] = True

    def on_all_change():
        val = st.session_state["cb_all_test"]
        for opt in status_options:
            st.session_state[f"cb_test_{opt}"] = val

    def on_item_change():
        all_checked = all(st.session_state.get(f"cb_test_{opt}", False) for opt in status_options)
        st.session_state["cb_all_test"] = all_checked

    st.sidebar.checkbox(f"すべて【{total_count}】", key="cb_all_test", on_change=on_all_change)

    selected_statuses = []
    for opt in status_options:
        count = status_counts.get(opt, 0)
        is_chk = st.sidebar.checkbox(f"{opt}【{count}】", key=f"cb_test_{opt}", on_change=on_item_change)
        if is_chk:
            selected_statuses.append(opt)

    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    sort_options = ["コード順（B→G→Q）", "最新サインオフ日順", "施行時期順", "試験法名順"]
    selected_sort = st.sidebar.selectbox("並び替え", sort_options)

    view_mode = st.sidebar.radio("表示スタイル", ["📊 一覧表", "🗂️ カード"], horizontal=True)

    st.sidebar.divider()
    with st.sidebar.expander("ℹ️ 参照版に関する注記", expanded=True):
        st.markdown("""
        * 🇯🇵 **JP**: JP19 / JP19追補
        * 🇺🇸 **USP**: USP-NF 2026 (Issue 5)
        * 🇪🇺 **EP**: 11th Ed.
        * 🇮🇳 **IP**: IP 2022<br><span class="ip-note">&nbsp;&nbsp;&nbsp;&nbsp;*(※合意書にIP欄記載なしは「調和対象外」扱い)*</span>
        """, unsafe_allow_html=True)

    filtered_df = df.copy()
    if search_query:
        mask = (
            filtered_df["コード"].astype(str).str.contains(search_query, case=False, na=False)
            | filtered_df["試験法名(日本語)"].astype(str).str.contains(search_query, case=False, na=False)
            | filtered_df["試験法名(英語)"].astype(str).str.contains(search_query, case=False, na=False)
        )
        for c in [jp_no_col, usp_no_col, ep_no_col, ip_no_col]:
            if c: mask = mask | filtered_df[c].astype(str).str.contains(search_query, case=False, na=False)
        filtered_df = filtered_df[mask]

    if selected_statuses:
        filtered_df = filtered_df[filtered_df["表示調和ステータス"].isin(selected_statuses)]
    else:
        filtered_df = filtered_df.iloc[0:0]

    if selected_sort == "コード順（B→G→Q）":
        filtered_df = filtered_df.sort_values(by="コード", ascending=True)
    elif selected_sort == "最新サインオフ日順":
        filtered_df = filtered_df.sort_values(by="サインオフ日", ascending=False)
    elif selected_sort == "施行時期順":
        filtered_df = filtered_df.sort_values(by="施行日", ascending=False)
    elif selected_sort == "試験法名順":
        filtered_df = filtered_df.sort_values(by="試験法名(日本語)", ascending=True)

    col_info1, col_info2 = st.columns([1, 2])
    with col_info1:
        st.caption(f"表示中: **{len(filtered_df)} / {len(df)} 件**")
    with col_info2:
        if view_mode == "🗂️ カード":
            st.markdown("""
            <div class="icon-legend">
                <span>🌐 4局調和</span>
                <span>✅ 3局完全調和</span>
                <span>⚠️ 調和（局間差異あり）</span>
                <span>❌ 調和中止</span>
            </div>
            """, unsafe_allow_html=True)

    display_cols = ["コード", "試験法名(日本語)"]
    if jp_no_col: display_cols.append(jp_no_col)
    if usp_no_col: display_cols.append(usp_no_col)
    if ep_no_col: display_cols.append(ep_no_col)
    if ip_no_col: display_cols.append(ip_no_col)
    
    display_cols += [
        "表示調和ステータス", "サインオフ日", "施行日",
        "🇯🇵 JP不採用項目", "🇯🇵 JP独自例外",
        "🇺🇸 USP不採用項目", "🇺🇸 USP独自例外",
        "🇪🇺 EP不採用項目", "🇪🇺 EP独自例外",
        "🇮🇳 IP不採用項目", "🇮🇳 IP独自例外",
    ]
    cols_to_show = [c for c in display_cols if c in filtered_df.columns]

    if view_mode == "📊 一覧表":
        html_rows = []
        for _, row in filtered_df.iterrows():
            cells = []
            for col in cols_to_show:
                val = str(row.get(col, "ー")).strip()
                if not val or val == "nan": val = "ー"
                tooltip_val = html.escape(val, quote=True).replace("&#10;", "<br>").replace("\n", "<br>")
                text_val = val.replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", " ")

                if col == "コード": cells.append(f'<td class="sticky-col1">{text_val}</td>')
                elif "試験法名" in col: cells.append(f'<td class="sticky-col2">{text_val}</td>')
                elif col == jp_no_col: cells.append(f'<td class="col-num">{text_val.replace("参考情報", "参考情報<br>")}</td>')
                elif col in [usp_no_col, ep_no_col, ip_no_col]: cells.append(f'<td class="col-num">{text_val}</td>')
                elif col == "表示調和ステータス":
                    if "4局調和" in val: badge_class = "status-badge-4p"
                    elif "3局完全調和" in val: badge_class = "status-badge-3p"
                    elif "中止" in val: badge_class = "status-badge-discontinued"
                    else: badge_class = "status-badge-diff"
                    status_text = text_val.replace("（", "<br>（").replace("(", "<br>(")
                    cells.append(f'<td class="col-status"><span class="{badge_class}">{status_text}</span></td>')
                elif col in ["サインオフ日", "施行日"]:
                    date_val = text_val.replace("(", "<br>(").replace("（", "<br>（")
                    date_val = re.sub(r'^[ー－-]\s*<br>\s*([\(（])', r'\1', date_val)
                    cells.append(f'<td class="col-date">{date_val}</td>')
                else:
                    is_empty = val in ["なし", "ー", "", "None", "nan"] or "完全調和" in val
                    if not is_empty:
                        if "作業中止" in val or "計画削除" in val:
                            cells.append(f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="text-gray-active">計画削除</span><span class="popup-content"><b>【詳細】</b><br>{tooltip_val}</span></div></td>')
                        elif "調和対象外" in val:
                            cells.append(f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="text-gray-active">対象外</span><span class="popup-content"><b>【詳細】</b><br>{tooltip_val}</span></div></td>')
                        elif val.startswith("非調和") or "記載なし" in val:
                            cells.append(f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="text-gray-active">非調和</span><span class="popup-content"><b>【詳細】</b><br>{tooltip_val}</span></div></td>')
                        else:
                            cells.append(f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="text-red-active">あり</span><span class="popup-content"><b>【詳細】</b><br>{tooltip_val}</span></div></td>')
                    else:
                        cells.append('<td class="col-detail text-none">なし</td>')
            html_rows.append(f"<tr>{''.join(cells)}</tr>")

        th_cells = []
        for i, col in enumerate(cols_to_show):
            col_name = col
            if col == "表示調和ステータス": col_name = "ステータス"
            elif col == "試験法名(日本語)": col_name = "試験法名"
            elif col == "サインオフ日": col_name = "サインオフ"
            elif "不採用項目" in col: col_name = col.replace("不採用項目", " 不採用")
            elif "独自例外" in col: col_name = col.replace("独自例外", " 例外")

            if col == "コード": th_cells.append(f'<th class="sticky-col1" onclick="sortTable({i})">{col_name}</th>')
            elif "試験法名" in col: th_cells.append(f'<th class="sticky-col2" onclick="sortTable({i})">{col_name}</th>')
            else: th_cells.append(f'<th onclick="sortTable({i})">{col_name}</th>')

        table_sort_js = """
        <script>
        function sortTable(n) {
          var table = document.getElementById("pdgTable");
          var rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
          switching = true; dir = "asc";
          while (switching) {
            switching = false; rows = table.rows;
            for (i = 1; i < (rows.length - 1); i++) {
              shouldSwitch = false;
              x = rows[i].getElementsByTagName("TD")[n];
              y = rows[i + 1].getElementsByTagName("TD")[n];
              if (dir == "asc") { if (x.innerText.toLowerCase() > y.innerText.toLowerCase()) { shouldSwitch = true; break; } }
              else if (dir == "desc") { if (x.innerText.toLowerCase() < y.innerText.toLowerCase()) { shouldSwitch = true; break; } }
            }
            if (shouldSwitch) { rows[i].parentNode.insertBefore(rows[i + 1], rows[i]); switching = true; switchcount++; }
            else { if (switchcount == 0 && dir == "asc") { dir = "desc"; switching = true; } }
          }
        }
        </script>
        """
        full_html = f'<div class="custom-table-container"><table class="custom-table" id="pdgTable"><thead><tr>{"".join(th_cells)}</tr></thead><tbody>{"".join(html_rows)}</tbody></table></div>{table_sort_js}'
        st.markdown(full_html, unsafe_allow_html=True)

    elif view_mode == "🗂️ カード":
        if "all_cards_test_exp" not in st.session_state:
            st.session_state["all_cards_test_exp"] = False

        btn_c1, btn_c2, _ = st.columns([1.2, 1.2, 6])
        with btn_c1:
            if st.button("🔼 すべて閉じる", use_container_width=True):
                st.session_state["all_cards_test_exp"] = False
                st.rerun()
        with btn_c2:
            if st.button("🔽 すべて開く", use_container_width=True):
                st.session_state["all_cards_test_exp"] = True
                st.rerun()

        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        for _, row in filtered_df.iterrows():
            status_val = row.get("表示調和ステータス", "")
            if "4局調和" in status_val: status_icon = "🌐"
            elif "3局完全調和" in status_val: status_icon = "✅"
            elif "中止" in status_val: status_icon = "❌"
            else: status_icon = "⚠️"

            with st.expander(f"{row['コード']} : {row['試験法名(日本語)']} （{status_val}） {status_icon}", expanded=st.session_state["all_cards_test_exp"]):
                c_left, c_right = st.columns([3, 1])

                with c_left:
                    m1, m2, m3 = st.columns(3)
                    m1.markdown(f"<div style='font-size: 0.95rem; margin-bottom: 6px;'>英語名: <code style='font-size: 0.95rem;'>{row.get('試験法名(英語)', 'ー')}</code></div>", unsafe_allow_html=True)
                    m2.markdown(f"<div style='font-size: 0.95rem; margin-bottom: 6px;'>サインオフ: <code style='font-size: 0.92rem;'>{row.get('サインオフ日', 'ー')}</code></div>", unsafe_allow_html=True)
                    m3.markdown(f"<div style='font-size: 0.95rem; margin-bottom: 6px;'>日局施行: <code style='font-size: 0.92rem;'>{row.get('施行日', 'ー')}</code></div>", unsafe_allow_html=True)
                    
                    num_parts = []
                    if jp_no_col and str(row.get(jp_no_col, "")) not in ["", "nan"]: num_parts.append(f"🇯🇵 JP: `{row[jp_no_col]}`")
                    if usp_no_col and str(row.get(usp_no_col, "")) not in ["", "nan"]: num_parts.append(f"🇺🇸 USP: `{row[usp_no_col]}`")
                    if ep_no_col and str(row.get(ep_no_col, "")) not in ["", "nan"]: num_parts.append(f"🇪🇺 EP: `{row[ep_no_col]}`")
                    if ip_no_col and str(row.get(ip_no_col, "")) not in ["", "nan"]: num_parts.append(f"🇮🇳 IP: `{row[ip_no_col]}`")
                    if num_parts:
                        st.markdown(f"<div style='font-size: 0.85rem; color: #475569;'>局方番号 | {' ｜ '.join(num_parts)}</div>", unsafe_allow_html=True)

                with c_right:
                    pmda_url = str(row.get("PMDA_PDF_URL", "")).strip()
                    pdf_filename = str(row.get("元ファイル名", "")).strip()
                    if pmda_url and pmda_url.startswith("http"):
                        st.markdown(f"📄 **[PMDA公式 合意PDFを開く ↗]({pmda_url})**")
                    elif pdf_filename and pdf_filename not in ["なし", "nan", "ー", ""]:
                        st.caption(f"ローカル保存ファイル: `{pdf_filename}`")
                    else:
                        st.caption("合意文書なし（作業中止等）")

                st.markdown("<hr style='margin: 12px 0 16px 0;'>", unsafe_allow_html=True)
                
                lbl_not = "<div style='font-size: 0.88rem; font-weight: 700; color: #9a3412; background: #ffedd5; padding: 2px 8px; border-radius: 4px; display: inline-block; margin-bottom: 6px;'>【不採用項目】</div>"
                lbl_exc = "<div style='font-size: 0.88rem; font-weight: 700; color: #1e40af; background: #dbeafe; padding: 2px 8px; border-radius: 4px; display: inline-block; margin-bottom: 6px;'>【独自例外（非調和部）】</div>"

                h_jp, h_usp, h_ep, h_ip = st.columns(4)
                h_jp.markdown("##### 🇯🇵 JP (JP19)")
                h_usp.markdown("##### 🇺🇸 USP (USP-NF)")
                h_ep.markdown("##### 🇪🇺 EP (11th Ed.)")
                h_ip.markdown("##### 🇮🇳 IP (IP 2022)")

                def render_card_item(val, default_type="info"):
                    v_str = str(val).strip()
                    if v_str not in ["なし", "ー", "", "nan"]:
                        if default_type == "warning": st.warning(v_str)
                        else: st.info(v_str)
                    else:
                        st.write("なし")

                r1_jp, r1_usp, r1_ep, r1_ip = st.columns(4)
                with r1_jp:
                    st.markdown(lbl_not, unsafe_allow_html=True); render_card_item(row.get("🇯🇵 JP不採用項目", "なし"), "warning")
                with r1_usp:
                    st.markdown(lbl_not, unsafe_allow_html=True); render_card_item(row.get("🇺🇸 USP不採用項目", "なし"), "warning")
                with r1_ep:
                    st.markdown(lbl_not, unsafe_allow_html=True); render_card_item(row.get("🇪🇺 EP不採用項目", "なし"), "warning")
                with r1_ip:
                    st.markdown(lbl_not, unsafe_allow_html=True); render_card_item(row.get("🇮🇳 IP不採用項目", "なし"), "warning")

                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                r2_jp, r2_usp, r2_ep, r2_ip = st.columns(4)
                with r2_jp:
                    st.markdown(lbl_exc, unsafe_allow_html=True); render_card_item(row.get("🇯🇵 JP独自例外", "なし"), "info")
                with r2_usp:
                    st.markdown(lbl_exc, unsafe_allow_html=True); render_card_item(row.get("🇺🇸 USP独自例外", "なし"), "info")
                with r2_ep:
                    st.markdown(lbl_exc, unsafe_allow_html=True); render_card_item(row.get("🇪🇺 EP独自例外", "なし"), "info")
                with r2_ip:
                    st.markdown(lbl_exc, unsafe_allow_html=True); render_card_item(row.get("🇮🇳 IP独自例外", "なし"), "info")

if __name__ == "__main__":
    main()