import streamlit as st
import pandas as pd
import os
import json

st.title("米粉マフィン Gallery")
st.markdown("究極の米粉マフィンを求めて。試作品の紹介です🔎")
st.divider()

CSV_PATH = "data/recipes.csv"

if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
    
    # スコア5以上の成功レシピを抽出
    df_success = df[df["粘度スコア"] >= 5]
    
    if not df_success.empty:
        # 最新のものが上に来るように並び替え
        df_success = df_success.sort_values("作成日", ascending=False)
       
        # ギャラリーを3列のグリッドで表示
        cols = st.columns(3)
        
        for index, row in df_success.reset_index().iterrows():
            # 順番にカラムに割り当てる (0列目, 1列目, 2列目...と順番に入れていく)
            col = cols[index % 3]
            
            with col:
                # 💡 ここが魔法！カード風の枠を作る
                with st.container(border=True):
                    
                    # 1. 画像の表示（1枚目だけを表示する）
                    img_path_str = str(row.get("画像パス", ""))
                    has_image = False
                    if pd.notna(img_path_str) and img_path_str != "":
                        paths = img_path_str.split(',')
                        if len(paths) > 0 and os.path.exists(paths[0]):
                            st.image(paths[0], use_container_width=True)
                            has_image = True
                            
                    if not has_image:
                        # 画像がない場合の代わりのグレー背景ボックス
                        st.markdown("""
                        <div style='background-color: #f0f2f6; height: 150px; display: flex; align-items: center; justify-content: center; border-radius: 5px;'>
                            <span style='font-size: 50px;'>🐈</span>
                        </div>
                        <br>
                        """, unsafe_allow_html=True)

                    # 2. レシピ名と基本情報
                    st.subheader(f"{row['レシピ名']}")
                    st.caption(f"📅 {row['作成日']} | 🌾 {row['米粉ブランド']}")
                    
                    # 3. 栄養成分（1個あたりを計算）
                    s = int(row['焼き上がり個数'])
                    cal_per = int(row['総熱量'] / s)
                    st.markdown(f"**🔥 1個あたり: {cal_per} kcal**")
                                        
                    # 5. 詳細を見るボタン（折りたたみ）
                    with st.expander("📖 レシピ詳細を見る"):
                        st.write(f"**水分比率:** {row['有効水分比率']}%")
                        st.write("**材料:**")
                        try:
                            # JSONを解読して表で綺麗に出す
                            details = json.loads(row['材料詳細'])

                            komeko_info = {
                                "材料名": f"米粉（{row['米粉ブランド']}）",
                                "分量": row['米粉重量']
                            }
                            details.insert(0, komeko_info)

                            st.dataframe(pd.DataFrame(details)[["材料名", "分量"]], hide_index=True, use_container_width=True)
                        except:
                            st.write("詳細データなし")

    else:
        st.info("まだ展示できる大成功レシピがありません。秘密の研究室で「粘度スコア5」のレシピを生み出してください！")
else:
    st.info("データがありません。")