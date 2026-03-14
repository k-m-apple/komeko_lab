import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
import plotly.express as px

# --- 1. 合言葉（パスワード）の設定 ---
PASSWORD = "anzukkk"  # ここを好きな言葉に変えてください

def check_password():
    """合言葉が正しいかチェックする関数"""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        # ログイン画面
        st.title("🔐 米粉ラボ - 限定公開")
        st.write("Bossの研究室へようこそ。合言葉を入力して入室してください。")
        pwd = st.text_input("合言葉", type="password")
        if st.button("入室"):
            if pwd == PASSWORD:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("合言葉が違います")
        return False
    return True

# --- 2. メインコンテンツ（ここが今のコードの塊） ---
if check_password():
    # --- ここから下に、今までの st.title("米粉ラボ") 以降の全コードをインデントして入れる ---
    st.sidebar.success("入室を許可しました。研究を開始してください。")
    
    # ... 今までのタブ作成や計算ロジック ...
    # --- 設定 ---
    SAVE_DIR = "data"
    CSV_PATH = os.path.join(SAVE_DIR, "recipes.csv")
    IMAGE_DIR = os.path.join(SAVE_DIR, "images")
    MASTER_JSON = os.path.join(SAVE_DIR, "ingredients_master.json")
    os.makedirs(IMAGE_DIR, exist_ok=True)

    # --- 定数（100gあたりの成分：管理栄養士標準値） ---
    DEFAULT_MASTER = {
        "水": {"水分": 1.0, "P": 0, "F": 0, "C": 0},
        "卵": {"水分": 0.75, "P": 12.3, "F": 10.3, "C": 0.3},
        "牛乳": {"水分": 0.9, "P": 3.3, "F": 3.8, "C": 4.8},
        "無塩バター": {"水分": 0.16, "P": 0.6, "F": 81.0, "C": 0.2},
        "米粉": {"水分": 0.12, "P": 6.0, "F": 0.7, "C": 81.3},
        "砂糖": {"水分": 0.0, "P": 0, "F": 0, "C": 99.2}
    }
    VISCOSITY_TABLE = {
        1: "完全液体：水状。傾けると一瞬で流れる。",
        2: "さらさら：飲むヨーグルト状。波紋がすぐ消える。",
        3: "とろとろ：練乳状。線を描くように落ちる。",
        4: "とろみ：緩いカスタード。落とした跡が数秒で消える。",
        5: "ムース：【マフィン成功値】落とした跡が残り、ゆっくり広がる。",
        6: "ぽってり：ギリシャヨーグルト状。スプーンを振らないと落ちない。",
        7: "ねっとり：味噌状。形を保つが表面は湿っている。",
        8: "ソフトドー：つきたての餅状。手に付くがひと塊になる。",
        9: "ハードドー：耳たぶ程度の固さ。指圧跡が残る。",
        10: "ぼそぼそ：水分不足。まとまらずに割れる状態。"
    }

    def load_master():
        if not os.path.isfile(MASTER_JSON):
            with open(MASTER_JSON, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_MASTER, f, ensure_ascii=False, indent=4)
            return DEFAULT_MASTER
        with open(MASTER_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_to_master(name, data_list):
        master = load_master()
        master[name] = data_list
        with open(MASTER_JSON, 'w', encoding='utf-8') as f:
            json.dump(master, f, ensure_ascii=False, indent=4)

    # --- 既存の関数 ---
    def get_next_recipe_id():
        if not os.path.isfile(CSV_PATH): return "R-001"
        try:
            df = pd.read_csv(CSV_PATH)
            if df.empty: return "R-001"
            last_id = df["レシピID"].iloc[-1]
            last_num = int(last_id.replace("R-", ""))
            return f"R-{last_num + 1:03d}"
        except: return "R-001"

    def calculate_metrics(df, flour_w, flour_name, master):
        net_water = 0.0
        total_p, total_f, total_c = 0.0, 0.0, 0.0

        # 米粉本体の計算
        f_data = master.get(flour_name, {"水分": 0.12, "P": 6.0, "F": 0.7, "C": 81.3})
        total_p += flour_w * f_data["P"] / 100
        total_f += flour_w * f_data["F"] / 100
        total_c += flour_w * f_data["C"] / 100

        # 追加材料の計算
        for _, r in df.iterrows():
            try:
                name, w = str(r["材料名"]), float(r["分量"])
                role = r.get("区分", "生地")
                d = master.get(name, {"水分": 0, "P": 0, "F": 0, "C": 0})

                if role == "生地":
                    net_water += w * d["水分"]

                total_p += w * d["P"] / 100
                total_f += w * d["F"] / 100
                total_c += w * d["C"] / 100
            except: continue

        # 熱量計算 (4, 9, 4 kcal)
        p_kcal, f_kcal, c_kcal = total_p * 4, total_f * 9, total_c * 4
        total_kcal = p_kcal + f_kcal + c_kcal

        hr = (net_water / flour_w * 100) if flour_w > 0 else 0
        pfc = (p_kcal/total_kcal, f_kcal/total_kcal, c_kcal/total_kcal) if total_kcal > 0 else (0,0,0)

        return net_water, hr, total_kcal, pfc, total_p, total_f, total_c

    # --- アプリ構成 ---
    st.set_page_config(page_title="米粉ラボ Pro", layout="wide")
    master_data = load_master()

    # --- サイドバー：材料マスター管理 ---
    with st.sidebar:
        st.header("🔍 材料マスター登録")
        st.write("新しい材料の栄養成分（100gあたり）を登録します。")
        new_ing = st.text_input("材料名 (例: はちみつ)")

        n_water = st.number_input("水分含有率 (0.0〜1.0)", 0.0, 1.0, 0.2)
        n_p = st.number_input("タンパク質 (g/100g)", 0.0, 100.0, 0.0)
        n_f = st.number_input("脂質 (g/100g)", 0.0, 100.0, 0.0)
        n_c = st.number_input("炭水化物 (g/100g)", 0.0, 100.0, 0.0)

        if st.button("マスターに登録"):
            if new_ing:
                new_data_dict = {
                    "水分": n_water,
                    "P": n_p,
                    "F": n_f,
                    "C": n_c
                }
                save_to_master(new_ing, new_data_dict)
                st.success(f"「{new_ing}」を登録しました！")
                st.rerun() # 画面を更新して即反映
            else:
                st.error("材料名を入力してください")

        st.divider()
        st.subheader("🗑️ 登録データの整理")

        # 削除したい材料をリストから選ぶ
        target_ing = st.selectbox("削除する材料を選択", options=[""] + list(master_data.keys()))

        if st.button("選択した材料をマスターから削除"):
            if target_ing:
                # 1. 読み込んでいるデータから削除
                del master_data[target_ing]

                # 2. ファイル(JSON)に上書き保存
                with open(MASTER_JSON, 'w', encoding='utf-8') as f:
                    json.dump(master_data, f, ensure_ascii=False, indent=4)

                st.warning(f"「{target_ing}」を削除しました。")
                st.rerun() # 画面を更新
        with st.expander("現在の登録リスト"):
            st.json(master_data)

    # --- メイン画面 ---
    st.title("🔬 米粉流動性解析データベース")
    next_id = get_next_recipe_id()



    # --- タブの作成 ---
    tab1, tab2 = st.tabs(["🧪 レシピ入力", "📈データ分析ダッシュボード"])

    with tab1:
        col_meta, col_calc = st.columns([1, 1.2])

        with col_meta:
            st.subheader("🧪 レシピ情報")
            recipe_id = st.text_input("レシピID", value=next_id, disabled=True)
            recipe_name = st.text_input("レシピ名")
            flour_brand = st.text_input("使用米粉ブランド", value="西友 1番粉")
            flour_weight = st.number_input("米粉の重量 (g)", value=100.0)
            category = st.selectbox("カテゴリ", ["焼き菓子（マフィン）", "パン", "ケーキ", "一般料理"])
            servings = st.number_input("焼き上がり個数（個）", min_value=1, value=1, step=1)

        with col_calc:
            st.subheader("⚖️ 材料・成分計算")
            # 登録済み材料名をサジェストに出すための準備
            ingredients_list = list(master_data.keys())
            # --- 修正ポイント：セッションステートでデータを保持する ---
            if "recipe_data" not in st.session_state:
                # 最初だけ初期データを作る
                st.session_state.recipe_data = pd.DataFrame([
                    {"材料名": ingredients_list[0] if ingredients_list else "", "分量": 0.0, "区分": "生地"}
                ] * 3)
            edited_df = st.data_editor(
                st.session_state.recipe_data,
                column_config={
                    "材料名": st.column_config.SelectboxColumn(
                        "材料名",
                        help="マスターから材料を選択してください",
                        options=ingredients_list,
                        required=True,
                    ),
                    "分量": st.column_config.NumberColumn(
                        "分量（g）",
                        min_value=0.0,
                        default=0.0,
                        format="%.1f",
                        required=True,
                    ),
                    "区分": st.column_config.SelectboxColumn(
                        "区分",
                        options=[
                            "生地",
                            "トッピング"
                        ],
                        default="生地"
                    )
                } ,
                num_rows="dynamic",
                use_container_width=True,
                key="data_editor_widget"
            )

            net_w, h_ratio, total_kcal, pfc, total_p, total_f, total_c = calculate_metrics(edited_df, flour_weight, flour_brand, master_data)

        # 表示部分
        st.subheader("🔋 栄養分析 (PFC)")
        m1, m2, m3 = st.columns(3)
        m1.metric("総熱量", f"{int(total_kcal)} kcal")
        m2.metric("有効水分比率", f"{h_ratio:.2f}%")
        m3.metric("P:F:C 比率", f"{int(pfc[0]*100)} : {int(pfc[1]*100)} : {int(pfc[2]*100)}")
        # --- PFC円グラフの作成 ---
        # 1. データの準備（名前と数値のペアを作る）
        st.divider() # 区切り線を入れると見やすいです
        st.subheader("🔋 PFCバランス（エネルギー比率）")

        pfc_data = pd.DataFrame({
            "成分": ["タンパク質 (P)", "脂質 (F)", "炭水化物 (C)"],
            "比率": [pfc[0], pfc[1], pfc[2]]
        })

        # 2. グラフの形を作る
        # hole=0.4 にすると、真ん中が空いたオシャレな「ドーナツチャート」になります
        fig_pfc = px.pie(
            pfc_data, 
            values="比率", 
            names="成分", 
            hole=0.4,
            color="成分",
            # 管理栄養士っぽく色を固定（P:黄色, F:赤, C:緑など）
            color_discrete_map={"タンパク質 (P)": "#FFD700", "脂質 (F)": "#FF4B4B", "炭水化物 (C)": "#28A745"}
        )

        # グラフの余白や文字サイズを調整（スッキリ見せるコツ）
        fig_pfc.update_layout(
            showlegend=True,
            margin=dict(t=20, b=20, l=20, r=20),
            height=300
        )

        # 3. 画面に表示
        st.plotly_chart(fig_pfc, use_container_width=True)
        st.divider()

        # 4. 1個当たりの成分計算
        st.subheader(f"🧁 1個あたりの推定値（全{servings}個中）")

        # 全体重量の概算（材料の合計）
        total_weight = edited_df["分量"].sum() + flour_weight

        # カラムを分けて1個あたりの数値を表示
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("エネルギー", f"{int(total_kcal / servings)} kcal")
        c2.metric("タンパク質", f"{(total_p / servings):.1f} g")
        c3.metric("脂質", f"{(total_f / servings):.1f} g")
        c4.metric("炭水化物", f"{(total_c / servings):.1f} g")

        with st.expander("詳細な1個あたりのデータ"):
            st.write(f"・1個あたりの重量（目安）: {int(total_weight / servings)} g")
            st.write(f"・1個あたりの水分量: {(net_w / servings):.1f} g")

        # --- 評価・保存エリア ---
        with st.form("research_summary"):
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("💧 生地の粘度")
                v_score = st.select_slider(
                    "粘度10段階スコア",
                    options=list(VISCOSITY_TABLE.keys()),
                    value=5,
                    format_func=lambda x: f"Score {x}"
                )
                st.info(f"現在の定義: {VISCOSITY_TABLE[v_score]}")

            with c2:
                st.subheader("📝 出来上がり評価")
                eval_text = st.text_area("食感、焼き色、改善メモ")
                img_files = st.file_uploader("画像（断面・全体）", accept_multiple_files=True)

            submitted = st.form_submit_button("🧪 研究データをCSVに記録する")

        # --- 保存処理 ---
        if submitted:
            st.session_state.recipe_data = edited_df
            # 1. 画像保存
            img_paths = []
            for i, file in enumerate(img_files):
                path = os.path.join(IMAGE_DIR, f"{recipe_id}_{i}.jpg")
                with open(path, "wb") as f:
                    f.write(file.getbuffer())
                img_paths.append(path)

            # 2. 保存用データ構築
            new_record = {
                "作成日": datetime.now().strftime("%Y-%m-%d"),
                "レシピID": recipe_id,
                "レシピ名": recipe_name,
                "米粉ブランド": flour_brand,
                "米粉重量": flour_weight,
                "焼き上がり個数": servings,
                "総熱量": total_kcal,        # ← これも追加しておくと楽
                "タンパク質総量": total_p,
                "脂質総量": total_f,
                "炭水化物総量": total_c,
                "有効水分比率": round(h_ratio, 2),
                "粘度スコア": v_score,
                "評価メモ": eval_text,
                "材料詳細": edited_df.to_json(orient='records', force_ascii=False),
                "画像パス": ",".join(img_paths)
            }

            # 3. CSV保存
            df_to_save = pd.DataFrame([new_record])
            if not os.path.isfile(CSV_PATH):
                df_to_save.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
            else:
                df_to_save.to_csv(CSV_PATH, mode='a', header=False, index=False, encoding="utf-8-sig")

            st.success(f"研究記録 {recipe_id} を保存しました！")
            st.balloons()

            pass
    with tab2:
        st.header("📊 研究データの相関分析")

        if os.path.isfile(CSV_PATH):
            df_all = pd.read_csv(CSV_PATH)

            if not df_all.empty:
                # 1. 散布図：有効水分比率 vs 粘度スコア
                st.subheader("💧 水分比率と粘度の相関")
                st.scatter_chart(
                    data=df_all,
                    x="有効水分比率",
                    y="粘度スコア",
                    color="米粉ブランド",  # ブランドごとに色分けされる！
                    size=100
                )

                # 2. 米粉ごとの傾向（表や平均値など）
                st.subheader("🌾 ブランド別 平均データ")
                summary = df_all.groupby("米粉ブランド")[["有効水分比率", "粘度スコア"]].mean()
                st.dataframe(summary)

                # 3. 履歴一覧
                st.subheader("📋 過去の試作履歴")
                # --- tab2 の履歴表示部分 ---
                for index, row in df_all.sort_values("作成日", ascending=False).iterrows():
                    with st.expander(f"{row['作成日']} | {row['レシピ名']} (1個あたり {int(row['総熱量']/row['焼き上がり個数'])} kcal)"):
                        # 1個あたりの計算
                        s = row['焼き上がり個数']
                        cal_per = int(row['総熱量'] / s)
                        p_per = row['タンパク質総量'] / s
                        f_per = row['脂質総量'] / s
                        c_per = row['炭水化物総量'] / s

                        # カラムで見やすく表示
                        st.write(f"### 🧁 1個あたりの栄養成分 (全{s}個)")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("エネルギー", f"{cal_per} kcal")
                        c2.metric("タンパク質", f"{p_per:.1f} g")
                        c3.metric("脂質", f"{f_per:.1f} g")
                        c4.metric("炭水化物", f"{c_per:.1f} g")
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.write(f"**米粉ブランド:** {row['米粉ブランド']}")
                            st.write(f"**水分比率:** {row['有効水分比率']}%")
                            st.write(f"**粘度スコア:** {row['粘度スコア']}")
                        with col2:
                            # ここがポイント：JSON文字列を辞書に戻して表示
                            details = json.loads(row['材料詳細'])
                            st.write("**材料内訳:**")
                            st.table(pd.DataFrame(details)) # 表形式で綺麗に出す

                        # 1. 保存された画像パスの文字列を取得
                        img_path_str = row.get("画像パス", "")

                        # 2. パスが存在する場合のみ表示処理へ
                        if pd.notna(img_path_str) and img_path_str != "":
                            st.divider()
                            st.markdown("#### 📸 試作記録（外観・断面）")

                            # カンマで分割してリストに戻す
                            paths = img_path_str.split(',')

                            # 枚数に合わせてカラムを自動生成
                            cols = st.columns(len(paths))

                            for i, p in enumerate(paths):
                                # コンテナ内のパスが存在するか確認
                                if os.path.exists(p):
                                    cols[i].image(p, use_container_width=True, caption=f"画像 {i+1}")
                                else:
                                    cols[i].warning("画像が見つかりません")
            else:
                st.info("データがまだありません。最初のレシピを保存してください！")
        else:
            st.info("CSVファイルが見つかりません。")