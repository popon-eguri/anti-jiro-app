# app.py - フロントエンド（食品データのCRUD完全対応版）
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from logic import (
    load_foods_data, 
    calculate_target_pfc, 
    calculate_consumed_kcal, 
    add_food_to_json,
    delete_food_from_json,
    update_food_in_json
)

# 画面の基本設定
st.set_page_config(page_title="アンチ二郎系・栄養デバッグ", page_icon="🍜", layout="wide")

st.title("🍜 アンチ二郎系・栄養デバッグシステム")
st.caption("二郎系でオーバーした脂質を、数学的・合理的に相殺（ロールバック）するアプリ")

st.markdown("---")

# ----------------------------------------------------
# セッション状態の初期化
# ----------------------------------------------------
if "today_log" not in st.session_state:
    st.session_state.today_log = []

# DB（JSON）から食品リストをロード
foods_list = load_foods_data()
st.write("🔍 デバッグ表示（Supabaseから取れたデータ）:", foods_list)

# ----------------------------------------------------
# サイドバー：ユーザー設定 ＆ 食品マスター管理 (CRUD)
# ----------------------------------------------------
st.sidebar.header("👤 ユーザー設定")
gender = st.sidebar.selectbox("性別", ["男性", "女性"])
age = st.sidebar.number_input("年齢", min_value=15, max_value=80, value=28)
height = st.sidebar.number_input("身長 (cm)", min_value=120.0, max_value=220.0, value=175.0)
weight = st.sidebar.number_input("体重 (kg)", min_value=30.0, max_value=150.0, value=70.0)

activity = st.sidebar.selectbox(
    "普段の活動量",
    ["デスクワーク中心 (低)", "日常的に動く・立ち仕事 (中)", "ハードな運動・筋トレ (高)"]
)

# 目標値の計算
user_targets = calculate_target_pfc(gender, age, height, weight, activity)
target_p = user_targets["target_p"]
target_f = user_targets["target_f"]
target_c = user_targets["target_c"]
target_kcal = user_targets["tdee"]

st.sidebar.markdown("---")

# ----------------------------------------------------
# 🛠️ 【CRUD機能】食品データの追加・編集・削除タブ
# ----------------------------------------------------
st.sidebar.header("⚙️ 食品データベース管理")
tab_add, tab_edit, tab_del = st.sidebar.tabs(["➕ 追加", "✏️ 編集", "🗑️ 削除"])

# --- 1. 新規追加タブ ---
with tab_add:
    with st.form("add_food_form", clear_on_submit=True):
        new_name = st.text_input("食品名", placeholder="例: サラダチキン")
        new_p = st.number_input("タンパク質 (P) g", min_value=0.0, step=0.1)
        new_f = st.number_input("脂質 (F) g", min_value=0.0, step=0.1)
        new_c = st.number_input("炭水化物 (C) g", min_value=0.0, step=0.1)
        
        submit_add = st.form_submit_button("💾 保存する")

    if submit_add:
        if new_name.strip() == "":
            st.sidebar.error("食品名を入力してね！")
        else:
            new_food_data = {
                "name": new_name,
                "p": float(new_p),
                "f": float(new_f),
                "c": float(new_c)
            }
            if add_food_to_json(new_food_data):
                st.sidebar.success(f"「{new_name}」を追加したわよ！")
                st.rerun()

# --- 2. 編集タブ ---
with tab_edit:
    if foods_list:
        edit_target_str = st.selectbox("編集する食品を選択", [f['name'] for f in foods_list], key="edit_select")
        target_food = next(f for f in foods_list if f['name'] == edit_target_str)
        
        with st.form("edit_food_form"):
            edit_name = st.text_input("食品名", value=target_food['name'])
            edit_p = st.number_input("タンパク質 (P) g", min_value=0.0, value=float(target_food['p']), step=0.1)
            edit_f = st.number_input("脂質 (F) g", min_value=0.0, value=float(target_food['f']), step=0.1)
            edit_c = st.number_input("炭水化物 (C) g", min_value=0.0, value=float(target_food['c']), step=0.1)
            
            submit_edit = st.form_submit_button("🔄 変更を更新")

        if submit_edit:
            updated_data = {
                "id": target_food.get("id"),
                "name": edit_name,
                "p": float(edit_p),
                "f": float(edit_f),
                "c": float(edit_c)
            }
            if update_food_in_json(updated_data):
                st.sidebar.success("更新完了よ！")
                st.rerun()
    else:
        st.write("データがありません")

# --- 3. 削除タブ ---
with tab_del:
    if foods_list:
        del_target_str = st.selectbox("削除する食品を選択", [f['name'] for f in foods_list], key="del_select")
        del_food = next(f for f in foods_list if f['name'] == del_target_str)
        
        if st.button("🚨 本当に削除する", type="primary"):
            if delete_food_from_json(del_food.get("id")):
                st.sidebar.success(f"「{del_food['name']}」を削除したわよ！")
                st.rerun()
    else:
        st.write("データがありません")

# ----------------------------------------------------
# メイン画面：1. 食品の選択 ＆ 今日のログへの追加
# ----------------------------------------------------
st.subheader("1. 今日食べたものを追加")

col_select, col_btn = st.columns([3, 1])

with col_select:
    food_names = [f"{item['name']} - [P:{item['p']}g / F:{item['f']}g / C:{item['c']}g]" for item in foods_list]
    if food_names:
        selected_food_str = st.selectbox("データベースから食品を選択", food_names)
        selected_index = food_names.index(selected_food_str)
        selected_food = foods_list[selected_index]
    else:
        st.warning("食品データがありません。サイドバーから登録してね！")
        selected_food = None

with col_btn:
    st.write("")
    st.write("") 
    if st.button("➕ 今日のログに追加", type="primary", disabled=(selected_food is None)):
        st.session_state.today_log.append(selected_food)
        st.success(f"「{selected_food['name']}」を追加したわよ！")

# ----------------------------------------------------
# 2. 今日の記録（ログ）一覧 ＆ リセット機能
# ----------------------------------------------------
if st.session_state.today_log:
    st.markdown("##### 📝 本日記録した食品リスト")
    log_cols = st.columns([4, 1])
    with log_cols[0]:
        for idx, item in enumerate(st.session_state.today_log):
            st.text(f"・ {item['name']} （P:{item['p']}g / F:{item['f']}g / C:{item['c']}g）")
    
    with log_cols[1]:
        if st.button("🗑️ ログを全リセット"):
            st.session_state.today_log = []
            st.rerun()

# ----------------------------------------------------
# 3. 今日の合計PFC & カロリーの集計
# ----------------------------------------------------
consumed_p = sum([item["p"] for item in st.session_state.today_log])
consumed_f = sum([item["f"] for item in st.session_state.today_log])
consumed_c = sum([item["c"] for item in st.session_state.today_log])

consumed_kcal = calculate_consumed_kcal(consumed_p, consumed_f, consumed_c)
rem_kcal = target_kcal - consumed_kcal

st.markdown("---")

# ----------------------------------------------------
# ⚡ カロリー収支表示
# ----------------------------------------------------
st.subheader("⚡ 本日の合計エネルギー（カロリー）収支")

cal_col1, cal_col2, cal_col3 = st.columns(3)
with cal_col1:
    st.metric(label="🔥 推定消費カロリー (TDEE)", value=f"{target_kcal:,} kcal")

with cal_col2:
    st.metric(label="🍽️ 本日の合計摂取カロリー", value=f"{consumed_kcal:,} kcal")

with cal_col3:
    if rem_kcal >= 0:
        st.metric(label="🎯 本日の残り許容カロリー", value=f"{rem_kcal:,} kcal")
    else:
        st.metric(label="🚨 許容カロリーオーバー", value=f"{abs(rem_kcal):,} kcal", delta=f"-{abs(rem_kcal):,} kcal", delta_color="inverse")

progress_rate = min(consumed_kcal / target_kcal, 1.0) if target_kcal > 0 else 0
st.progress(progress_rate, text=f"目標消費カロリーの 【{int(progress_rate * 100)}%】 を摂取済み")

st.markdown("---")

# ----------------------------------------------------
# 📊 PFCグラフ描画
# ----------------------------------------------------
st.subheader("📊 本日の合計PFC達成状況（目標ライン 基準）")

categories = ['タンパク質 (P)', '脂質 (F)', '炭水化物 (C)']
consumed_values = [consumed_p, consumed_f, consumed_c]
target_values = [target_p, target_f, target_c]

fig = go.Figure()
fig.add_trace(go.Bar(
    x=categories,
    y=consumed_values,
    name='本日の合計摂取 (g)',
    marker_color=['#1f77b4', '#ff7f0e' if consumed_f > target_f else '#1f77b4', '#1f77b4'],
    text=[f"{round(v, 1)}g" for v in consumed_values],
    textposition='auto',
))

fig.add_trace(go.Scatter(
    x=categories,
    y=target_values,
    name='1日の目標上限 (g)',
    mode='markers+text',
    marker=dict(color='red', size=16, symbol='line-ew-open', line=dict(width=4)),
    text=[f"目標:{v}g" for v in target_values],
    textposition="top center"
))

fig.update_layout(
    height=380,
    margin=dict(l=20, r=20, t=30, b=20),
    yaxis=dict(title="グラム (g)", gridcolor='LightGray'),
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ----------------------------------------------------
# 🛠️ デバッグ結果（相殺パッチ）
# ----------------------------------------------------
st.subheader("🛠️ デバッグ結果（相殺パッチ）")

rem_p = target_p - consumed_p
rem_f = target_f - consumed_f
rem_c = target_c - consumed_c

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="タンパク質(P) 残り", value=f"{rem_p:.1f} g")
    if rem_p > 0:
        st.info(f"あと {rem_p:.1f}g 必要！")
    else:
        st.success("目標達成！")

with col2:
    st.metric(label="脂質(F) 残り", value=f"{rem_f:.1f} g", delta=f"{rem_f:.1f} g", delta_color="inverse")
    if rem_f <= 0:
        st.error(f"🚨 {abs(rem_f):.1f}g オーバー！脂質0gを死守！")
    else:
        st.warning(f"残り {rem_f:.1f}g")

with col3:
    st.metric(label="炭水化物(C) 残り", value=f"{rem_c:.1f} g")
    if rem_c <= 0:
        st.error(f"🚨 {abs(rem_c):.1f}g オーバー！")
    else:
        st.info(f"残り {rem_c:.1f}g")

st.markdown("---")

# ----------------------------------------------------
# レコメンド
# ----------------------------------------------------
st.subheader("💡 今夜のおすすめ補償メニュー（脂質カット特化）")
if rem_f <= 0:
    st.write("脂質がカンストしているため、**『脂質ほぼ0g』**の以下の素材でタンパク質だけを回収しましょう！")
    st.success("🥚 **白身だけのレンチン固まり** (卵2〜3個分) ＋ **ノンオイルツナ缶** ＋ **皮なし鶏むね肉** ＋ **プロテイン**")
    st.caption("※塩分排出のために、カリウム（バナナ1本やほうれん草、トクホのお茶）を一緒に摂取するのがおすすめ！")
