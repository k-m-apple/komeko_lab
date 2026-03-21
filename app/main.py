import streamlit as st

# 1. 各ページを読み込み、メニュー用の「タイトル」と「アイコン」を自由につける
page_gallery = st.Page("app.py", title="米粉マフィンギャラリー", icon="🏠")
page_lab = st.Page("lab.py", title="米粉研究室", icon="🔬")

# 2. サイドバーのメニューを作成
pg = st.navigation([page_gallery, page_lab])

# 3. アプリ全体の設定（ブラウザのタブ名など）
st.set_page_config(page_title="米粉ラボ Pro", layout="wide")

# 4. 実行！
pg.run()