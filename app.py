import streamlit as st
import pandas as pd
import plotly.express as px
from logic import (
    sign_up,
    sign_in,
    sign_out,
    load_foods_data,
    load_preset_foods,
    recommend_foods,
    add_intake_log,
    load_today_intake,
    add_food_data,
    update_food_data,
    delete_food_data
)

st.set_page_config(page_title="アンチ二郎 PWA", layout="wide")

# セッション状態（ログイン情報）の初期化
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------------------------------------------------
# 🔑 未ログイン時の処理（ログイン / 新規登録画面）
# ---------------------------------------------------------
if st.session_state.user is None:
    st.title("🍜 アンチ二郎 PWA")
    st.caption("ログインまたはアカウント作成をしてスタートしてね！")
    
    tab_login, tab_signup = st.tabs(["🔑 ログイン", "📝 新規登録"])
    
    # --- ログインタブ ---
    with tab_login:
        st.subheader("ログイン")
        login_email = st.text_input("メールアドレス", key="login_email")
        login_password = st.text_input("パスワード", type="password", key="login_pw")
        
        if st.button("ログインする", type="primary"):
            if login_email and login_password:
                try:
                    res = sign_in(login_email, login_password)
                    if res.user:
                        st.session_state.user = {
                            "id": res.user.id,
                            "email": res.user.email
                        }
                        st.success("ログインに成功したわ！")
                        st.rerun()
                    else:
                        st.error("ログインに失敗しちゃった。メアドかパスワードを確認してね。")
                except Exception as e:
                    st.error(f"エラーが発生したわ: {e}")
            else:
                st.warning("メールアドレスとパスワードを入力してね！")

    # --- 新規登録タブ ---
    with tab_signup:
        st.subheader("新規アカウント作成")
        signup_email = st.text_input("メールアドレス", key="signup_email")
        signup_password = st.text_input("パスワード (6文字以上)", type="password", key="signup_pw")
        
        if st.button("登録する"):
            if signup_email and signup_password:
                try:
                    res = sign_up(signup_email, signup_password)
                    if res.user:
                        st.success("アカウント登録が完了したわ！ログインタブからログインしてみてね！")
                    else:
                        st.error("登録に失敗しちゃったわ。")
                except Exception as e:
                    st.error(f"エラーが発生したわ: {e}")
            else:
                st.warning("メールアドレスとパスワードを入力してね！")

# ---------------------------------------------------------
# 🚀 ログイン済みの処理（メインアプリ画面）
# ---------------------------------------------------------
else:
    user = st.session_state.user

    st.write("DEBUG: user.id =", st.session_state.user["id"])
    st.write("DEBUG: user dict =", st.session_state.user)

    # 🔥 ここに統合ロジックを置くのが正解！
    foods_list = load_foods_data(user["id"])
    preset_list = load_preset_foods()
    all_foods = preset_list + foods_list
    
    # サイドバー（ユーザー情報＆プロフィール入力）
    st.sidebar.write(f"👤 **{user["email"]}** でログイン中")
    if st.sidebar.button("ログアウト"):
        sign_out()
        st.session_state.user = None
        st.rerun()

    st.sidebar.divider()
    st.sidebar.header("⚙️ 身体プロフィールの設定")
    
    # 身長・体重・性別・目的の入力フォーム
    gender = st.sidebar.selectbox("性別", ["男性", "女性"], key="prof_gender")
    height = st.sidebar.number_input("身長 (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.1, key="prof_height")
    weight = st.sidebar.number_input("体重 (kg)", min_value=30.0, max_value=200.0, value=65.0, step=0.1, key="prof_weight")
    age = st.sidebar.number_input("年齢", min_value=10, max_value=100, value=25, step=1, key="prof_age")
    purpose = st.sidebar.selectbox("目的", ["減量（アンチ二郎）", "現状維持", "増量"], key="prof_purpose")

    # --- 簡易基礎代謝（BMR）＆目標PFC計算 ---
    if gender == "男性":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # 活動量を仮に1.375（軽度の運動）として推定消費カロリー算出
    tdee = bmr * 1.375

    if purpose == "減量（アンチ二郎）":
        target_calories = tdee - 500
    elif purpose == "増量":
        target_calories = tdee + 300
    else:
        target_calories = tdee

    # 目標PFC (P:25%, F:25%, C:50% で簡易計算)
    target_p = (target_calories * 0.25) / 4
    target_f = (target_calories * 0.25) / 9
    target_c = (target_calories * 0.50) / 4

    recommended = recommend_foods(all_foods, target_p, target_f, target_c)

    # メイン表示エリア
    st.title("🍜 アンチ二郎 PWA")
    
    # ユーザーごとの食品データ読み込み
    foods_list = load_foods_data(user["id"])

    # 上部サマリーエリア（目標カロリー・PFCと登録食品数）
    st.subheader("🎯 あなたの1日目標設定")
    scol1, scol2, scol3, scol4 = st.columns(4)
    scol1.metric("目標カロリー", f"{target_calories:.0f} kcal")
    scol2.metric("目標 P (タンパク質)", f"{target_p:.1f} g")
    scol3.metric("目標 F (脂質)", f"{target_f:.1f} g")
    scol4.metric("目標 C (炭水化物)", f"{target_c:.1f} g")

    st.divider()

    total_items = len(foods_list)
    avg_p = sum(f['p'] for f in foods_list) / total_items if total_items > 0 else 0
    avg_f = sum(f['f'] for f in foods_list) / total_items if total_items > 0 else 0
    avg_c = sum(f['c'] for f in foods_list) / total_items if total_items > 0 else 0

    st.subheader("📊 登録食品の平均データ")
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    fcol1.metric("登録食品数", f"{total_items} 件")
    fcol2.metric("平均 P", f"{avg_p:.1f} g")
    fcol3.metric("平均 F", f"{avg_f:.1f} g")
    fcol4.metric("平均 C", f"{avg_c:.1f} g")

    st.divider()

    # タブ切り替えエリア
    tab_view, tab_add, tab_edit, tab_recommend = st.tabs(["📊 食品一覧・グラフ", "➕ 新規登録", "✏️ 編集・削除","🔥 おすすめ食品"])

    # --- タブ1: 一覧とグラフ ---
    with tab_view:
        st.subheader("登録済み食品データ（プリセット＋ユーザー食品）")
    
        if all_foods:
            df = pd.DataFrame(all_foods)
        
            st.dataframe(
                df[['name', 'p', 'f', 'c']],
                column_config={
                    "name": "食品名",
                    "p": "タンパク質 (g)",
                    "f": "脂質 (g)",
                    "c": "炭水化物 (g)"
                },
                use_container_width=True
            )
            
            st.subheader("🍽 今日食べた食品を登録")

            for food in all_foods:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{food['name']}**（P:{food['p']} / F:{food['f']} / C:{food['c']}）")
                with col2:
                    if st.button(f"今日食べた！", key=f"eat_{food['id']}"):
                        add_intake_log(st.session_state.user["id"], food["id"])
                        st.success(f"{food['name']} を今日の摂取に追加したわ！")
                        st.rerun()
        
            st.subheader("PFCバランスの比較")
            fig = px.bar(
               df, 
                x="name", 
                y=["p", "f", "c"], 
                title="食品ごとのPFC量 (g)",
                labels={"value": "グラム (g)", "variable": "栄養素", "name": "食品名"},
                barmode="group"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("食品データがまだないわ！プリセットか新規登録を使って追加してみてね！")

    # --- タブ2: 新規登録 ---
    with tab_add:
        st.subheader("新しい食品を追加")
        
        with st.form("add_food_form", clear_on_submit=True):
            new_name = st.text_input("食品名", placeholder="例: サラダチキン")
            new_p = st.number_input("タンパク質 (P) [g]", min_value=0.0, step=0.1)
            new_f = st.number_input("脂質 (F) [g]", min_value=0.0, step=0.1)
            new_c = st.number_input("炭水化物 (C) [g]", min_value=0.0, step=0.1)
            
            submitted = st.form_submit_button("追加する")
            if submitted:
                if new_name.strip() == "":
                    st.error("食品名を入力してちょうだい！")
                else:
                    res = add_food_data(new_name, new_p, new_f, new_c, user.id)
                    if res:
                        st.success(f"「{new_name}」を追加したわ！")
                        st.rerun()

    # --- タブ3: 編集・削除 ---
    with tab_edit:
        st.subheader("食品データの編集・削除")
        
        if foods_list:
            edit_target_name = st.selectbox(
                "編集する食品を選択", 
                [f['name'] for f in foods_list], 
                key="edit_select"
            )
            
            selected_food = next((f for f in foods_list if f['name'] == edit_target_name), None)
            
            if selected_food:
                st.write(f"ID: `{selected_food['id']}`")
                
                with st.form("edit_food_form"):
                    updated_name = st.text_input("食品名", value=selected_food['name'])
                    updated_p = st.number_input("タンパク質 (P) [g]", value=float(selected_food['p']), min_value=0.0, step=0.1)
                    updated_f = st.number_input("脂質 (F) [g]", value=float(selected_food['f']), min_value=0.0, step=0.1)
                    updated_c = st.number_input("炭水化物 (C) [g]", value=float(selected_food['c']), min_value=0.0, step=0.1)
                    
                    col_save, col_del = st.columns([1, 1])
                    
                    with col_save:
                        save_submitted = st.form_submit_button("更新を保存", type="primary")
                    with col_del:
                        delete_submitted = st.form_submit_button("この食品を削除", type="secondary")
                    
                    if save_submitted:
                        res = update_food_data(selected_food['id'], updated_name, updated_p, updated_f, updated_c)
                        if res:
                            st.success(f"「{updated_name}」のデータを更新したわ！")
                            st.rerun()
                            
                    if delete_submitted:
                        res = delete_food_data(selected_food['id'])
                        if res:
                            st.warning(f"「{selected_food['name']}」を削除したわ！")
                            st.rerun()
        else:
            st.info("編集・削除できる食品データがないわ！")

    today_logs = load_today_intake(user["id"])

    today_p = sum(next(f['p'] for f in all_foods if f['id'] == log['food_id']) for log in today_logs)
    today_f = sum(next(f['f'] for f in all_foods if f['id'] == log['food_id']) for log in today_logs)
    today_c = sum(next(f['c'] for f in all_foods if f['id'] == log['food_id']) for log in today_logs)

    with tab_recommend:
        st.subheader("🔥 今日のおすすめ食品")

        if recommended:
            for item in recommended[:5]:  # 上位5件だけ表示
                st.write(f"**{item['name']}**（スコア: {item['score']:.2f}）")
        else:
            st.info("おすすめ食品が見つからなかったわ！")

    st.subheader("📅 今日の摂取状況")

    col1, col2, col3 = st.columns(3)
    col1.metric("摂取P", f"{today_p:.1f} g", f"{today_p - target_p:.1f} g")
    col2.metric("摂取F", f"{today_f:.1f} g", f"{today_f - target_f:.1f} g")
    col3.metric("摂取C", f"{today_c:.1f} g", f"{today_c - target_c:.1f} g")


