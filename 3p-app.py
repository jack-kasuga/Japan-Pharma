import html
import os
import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="PDG 4局調和ステータス(試験法)",
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
    # 読み込み対象のCSVファイル（複数候補に対応）
    candidates = [
        "pdg_extracted_3regions_ja_3.csv",
        "pdg_extracted_3regions_ja_2.csv",
        "pdg_extracted_3regions_ja.csv",
        "pdg_extracted_3regions.csv"
    ]
    target_csv = None
    for cand in candidates:
        if os.path.exists(cand):
            target_csv = cand
            break

    if target_csv is None:
        return pd.DataFrame()

    try:
        # すべて文字列として読み込み（ゼロ落ち防止）
        df = pd.read_csv(target_csv, encoding="utf-8-sig", dtype=str)
        df = df.fillna("ー")

        if "試験法名(英語)" not in df.columns:
            if "PDG 試験法名" in df.columns:
                df["試験法名(英語)"] = df["PDG 試験法名"]
            else:
                df["試験法名(英語)"] = "ー"

        if "サインオフ日" not in df.columns:
            df["サインオフ日"] = "ー"
        if "施行日" not in df.columns:
            df["施行日"] = "ー"

        df = df.sort_values(by="コード", ascending=True)

        # ステータス判定ロジック（「調和（局間差異あり）」に統一）
        def determine_harmonization_status(row):
            raw_status = str(row.get("全体調和ステータス", "")).replace("極間", "局間")
            if "中止" in raw_status or "削除" in raw_status or "非調和" in raw_status:
                return "調和中止（非調和）"
            if "一部調和" in raw_status or "局間差異" in raw_status or "差異" in raw_status or "局間の差異" in raw_status:
                return "調和（局間差異あり）"

            ip_reject = str(row.get("🇮🇳 IP不採用項目", "")).strip()
            if ip_reject == "なし":
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
    }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
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
        white-space: nowrap;
        text-align: center;
        z-index: 2;
        user-select: none;
    }
    .custom-table th:hover { background-color: #eaeef2; }
    .custom-table td {
        padding: 5px 8px;
        border-bottom: 1px solid #eaeef2;
        color: #24292f;
        vertical-align: middle;
    }
    .custom-table tr:hover td { background-color: #f2f7fc; }
    
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
        min-width: 175px;
        max-width: 175px;
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
    
    .col-num { white-space: nowrap; text-align: center; font-weight: 500; color: #0969da; }
    .col-status { white-space: nowrap; text-align: center; }
    .col-date { white-space: nowrap; text-align: center; font-size: 12px; }
    .col-detail { white-space: nowrap; text-align: center; min-width: 75px; position: relative; }

    .popup-container {
        position: relative;
        display: inline-block;
        cursor: pointer;
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
    .popup-container:focus-within .popup-content {
        visibility: visible;
        opacity: 1;
    }
    .popup-container:hover .popup-content {
        visibility: visible;
        opacity: 1;
    }
    .text-none { color: #8c959f; }

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
    .ip-note {
        font-size: 0.7rem;
        color: #64748b;
        white-space: nowrap;
        margin-top: 4px;
        display: inline-block;
    }
    </style>
    """
    st.markdown(app_css, unsafe_allow_html=True)

    st.markdown(
        '<div class="custom-main-title">🌐 PDG 4局調和ステータス(試験法)</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="custom-main-caption">日本薬局方(JP)、米国薬局方(USP)、欧州薬局方(EP)、インド薬局方(IP)の4局における調和状況およびローカル要件一覧</div>',
        unsafe_allow_html=True,
    )

    df = load_data()
    if df.empty:
        st.warning("表示できるデータがありません。CSVファイルを確認してください。")
        return

    jp_no_col = find_col(df.columns, ["jp番号", "jp各条", "jp章"])
    usp_no_col = find_col(df.columns, ["usp番号", "usp各条", "usp章"])
    ep_no_col = find_col(df.columns, ["ep番号", "ep各条", "ep章"])
    ip_no_col = find_col(df.columns, ["ip番号", "ip各条", "ip章"])

    st.sidebar.header("⚙️ 検索・設定")

    search_query = st.sidebar.text_input(
        "🔍 検索",
        "",
        placeholder="コード、試験法名など",
    )

    status_options = [
        "すべての調和ステータス",
        "4局調和（IP反映済）",
        "3局完全調和（IP未反映）",
        "調和（局間差異あり）",
        "調和中止（非調和）",
    ]
    selected_status = st.sidebar.selectbox("調和状況", status_options)

    sort_options = [
        "コード順（B→G→Q）",
        "最新サインオフ日順",
        "施行時期順",
        "試験法名順",
    ]
    selected_sort = st.sidebar.selectbox("並び替え", sort_options)

    view_mode = st.sidebar.radio(
        "表示スタイル",
        ["📊 一覧表", "🗂️ カード"],
        horizontal=True,
    )

    st.sidebar.divider()

    with st.sidebar.expander("ℹ️ 参照版に関する注記", expanded=True):
        st.markdown("""
        * 🇯🇵 **JP**: JP19
        * 🇺🇸 **USP**: USP-NF 2026 (Issue 5)
        * 🇪🇺 **EP**: 11th Ed.
        * 🇮🇳 **IP**: IP 2022<br><span class="ip-note">&nbsp;&nbsp;&nbsp;&nbsp;*(※IP欄記載なしは「調和対象外」扱い)*</span>
        """, unsafe_allow_html=True)

    filtered_df = df.copy()
    if search_query:
        mask = (
            filtered_df["コード"].astype(str).str.contains(search_query, case=False, na=False)
            | filtered_df["試験法名(日本語)"].astype(str).str.contains(search_query, case=False, na=False)
            | filtered_df["試験法名(英語)"].astype(str).str.contains(search_query, case=False, na=False)
        )
        for c in [jp_no_col, usp_no_col, ep_no_col, ip_no_col]:
            if c:
                mask = mask | filtered_df[c].astype(str).str.contains(search_query, case=False, na=False)
        filtered_df = filtered_df[mask]

    if selected_status != "すべての調和ステータス":
        filtered_df = filtered_df[filtered_df["表示調和ステータス"] == selected_status]

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
                <span>⏹️ 調和中止</span>
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
    table_df = filtered_df[cols_to_show].copy()

    if view_mode == "📊 一覧表":
        html_rows = []
        for _, row in table_df.iterrows():
            cells = []
            for col in cols_to_show:
                val = str(row[col]) if pd.notna(row[col]) else "ー"
                tooltip_val = html.escape(val, quote=True).replace("&#10;", "<br>").replace("\n", "<br>")
                text_val = val.replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", " ")

                if col == "コード":
                    td_html = f'<td class="sticky-col1">{text_val}</td>'
                elif "試験法名" in col:
                    td_html = f'<td class="sticky-col2">{text_val}</td>'
                elif col == jp_no_col:
                    jp_val = text_val.replace("参考情報", "参考情報<br>")
                    td_html = f'<td class="col-num">{jp_val}</td>'
                elif col in [usp_no_col, ep_no_col, ip_no_col]:
                    td_html = f'<td class="col-num">{text_val}</td>'
                elif col == "表示調和ステータス":
                    if "4局調和" in val:
                        badge_class = "status-badge-4p"
                    elif "3局完全調和" in val:
                        badge_class = "status-badge-3p"
                    elif "中止" in val:
                        badge_class = "status-badge-discontinued"
                    else:
                        badge_class = "status-badge-diff"
                    status_text = text_val.replace("（", "<br>（").replace("(", "<br>(")
                    td_html = f'<td class="col-status"><span class="{badge_class}">{status_text}</span></td>'
                elif col in ["サインオフ日", "施行日"]:
                    date_val = text_val.replace("(", "<br>(").replace("（", "<br>（")
                    date_val = re.sub(r'^[ー－-]\s*<br>\s*([\(（])', r'\1', date_val)
                    td_html = f'<td class="col-date">{date_val}</td>'
                else:
                    is_empty = val.strip() in ["なし", "ー", "", "None", "nan"]
                    if "完全調和" in val:
                        is_empty = True

                    if not is_empty:
                        if "作業中止" in val:
                            td_html = f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="text-gray-active">（作業中止）</span><span class="popup-content">{tooltip_val}</span></div></td>'
                        elif "計画削除" in val:
                            td_html = f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="text-gray-active">（計画削除）</span><span class="popup-content">{tooltip_val}</span></div></td>'
                        elif "調和対象外" in val:
                            td_html = f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="text-gray-active">調和対象外</span><span class="popup-content">{tooltip_val}</span></div></td>'
                        elif val.strip().startswith("非調和（") or "合意文書にIP記載なし" in val:
                            td_html = f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="text-gray-active">非調和</span><span class="popup-content">{tooltip_val}</span></div></td>'
                        else:
                            td_html = f'<td class="col-detail"><div class="popup-container" tabindex="0"><span class="text-red-active">あり</span><span class="popup-content">{tooltip_val}</span></div></td>'
                    else:
                        td_html = '<td class="col-detail text-none">なし</td>'
                cells.append(td_html)
            html_rows.append(f"<tr>{''.join(cells)}</tr>")

        th_cells = []
        for i, col in enumerate(cols_to_show):
            col_name = col
            if col == "表示調和ステータス": col_name = "ステータス"
            elif col == "試験法名(日本語)": col_name = "試験法名"
            elif col == "サインオフ日": col_name = "サインオフ"
            elif "不採用項目" in col: col_name = col.replace("不採用項目", " 不採用")
            elif "独自例外" in col: col_name = col.replace("独自例外", " 例外")

            if col == "コード":
                th_cells.append(f'<th class="sticky-col1" onclick="sortTable({i})">{col_name}</th>')
            elif "試験法名" in col:
                th_cells.append(f'<th class="sticky-col2" onclick="sortTable({i})">{col_name}</th>')
            else:
                th_cells.append(f'<th onclick="sortTable({i})">{col_name}</th>')
        
        th_html = "".join(th_cells)

        table_sort_js = """
        <script>
        function sortTable(n) {
          var table = document.getElementById("pdgTable");
          var rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
          switching = true;
          dir = "asc";
          while (switching) {
            switching = false;
            rows = table.rows;
            for (i = 1; i < (rows.length - 1); i++) {
              shouldSwitch = false;
              x = rows[i].getElementsByTagName("TD")[n];
              y = rows[i + 1].getElementsByTagName("TD")[n];
              var xText = x.innerText.toLowerCase();
              var yText = y.innerText.toLowerCase();
              if (dir == "asc") {
                if (xText > yText) { shouldSwitch = true; break; }
              } else if (dir == "desc") {
                if (xText < yText) { shouldSwitch = true; break; }
              }
            }
            if (shouldSwitch) {
              rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
              switching = true;
              switchcount ++;
            } else {
              if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
              }
            }
          }
        }
        </script>
        """

        full_html = (
            '<div class="custom-table-container">'
            '<table class="custom-table" id="pdgTable">'
            f"<thead><tr>{th_html}</tr></thead>"
            f"<tbody>{''.join(html_rows)}</tbody>"
            "</table>"
            "</div>"
            + table_sort_js
        )
        st.markdown(full_html, unsafe_allow_html=True)

    elif view_mode == "🗂️ カード":
        for _, row in filtered_df.iterrows():
            status_val = row.get("表示調和ステータス", "")
            if "4局調和" in status_val: status_icon = "🌐"
            elif "3局完全調和" in status_val: status_icon = "✅"
            elif "中止" in status_val: status_icon = "⏹️"
            else: status_icon = "⚠️"

            with st.expander(f"{row['コード']} : {row['試験法名(日本語)']} （{status_val}） {status_icon}"):
                m_c1, m_c2, m_c3 = st.columns(3)
                m_c1.caption(f"英語名: **{row.get('試験法名(英語)', 'ー')}**")
                m_c2.caption(f"最新サインオフ: **`{row.get('サインオフ日', 'ー')}`**")
                m_c3.caption(f"施行時期: **`{row.get('施行日', 'ー')}`**")

                tab_jp, tab_usp, tab_ep, tab_ip = st.tabs(["🇯🇵 JP19", "🇺🇸 USP-NF", "🇪🇺 EP 11th", "🇮🇳 IP 2022"])

                with tab_jp:
                    if jp_no_col and jp_no_col in row: st.markdown(f"**【局方番号】** `{row[jp_no_col]}`")
                    st.markdown("**【不採用項目】**"); st.write(row.get("🇯🇵 JP不採用項目", "なし"))
                    st.markdown("**【独自例外（非調和部）】**"); st.info(row.get("🇯🇵 JP独自例外", "なし"))

                with tab_usp:
                    if usp_no_col and usp_no_col in row: st.markdown(f"**【局方番号】** `{row[usp_no_col]}`")
                    st.markdown("**【不採用項目】**"); st.write(row.get("🇺🇸 USP不採用項目", "なし"))
                    st.markdown("**【独自例外（非調和部）】**"); st.info(row.get("🇺🇸 USP独自例外", "なし"))

                with tab_ep:
                    if ep_no_col and ep_no_col in row: st.markdown(f"**【局方番号】** `{row[ep_no_col]}`")
                    st.markdown("**【不採用項目】**"); st.write(row.get("🇪🇺 EP不採用項目", "なし"))
                    st.markdown("**【独自例外（非調和部）】**"); st.info(row.get("🇪🇺 EP独自例外", "なし"))

                with tab_ip:
                    if ip_no_col and ip_no_col in row: st.markdown(f"**【局方番号】** `{row[ip_no_col]}`")
                    st.markdown("**【不採用項目】**"); st.write(row.get("🇮🇳 IP不採用項目", "なし"))
                    st.markdown("**【独自例外（非調和部）】**"); st.info(row.get("🇮🇳 IP独自例外", "なし"))

if __name__ == "__main__":
    main()