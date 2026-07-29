import streamlit as st
import pandas as pd
import plotly.express as px
from logic import (
    sign_up,
    sign_in,
    sign_out,
    load_foods_data,
    add_food_data,
    update_food_data,
    delete_food_data
)

st.set_page_config(page_title="アンチ二郎 PWA", layout="wide")

# 1. セッション状態（ログイン情報）の初期化
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
                        st.session_state.user = res.user
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
    
    # サイドバーにユーザー情報とログアウトボタンを設置
    st.sidebar.write(f"👤 **{user.email}** でログイン中")
    if st.sidebar.button("ログアウト"):
        sign_out()
        st.session_state.user = None
        st.rerun()

    st.title("🍜 アンチ二郎 PWA")
    
    # ログイン中のユーザーIDを使ってデータを取得
    foods_list = load_foods_data(user.id)

    # 画面上部にサマリーを表示
    total_items = len(foods_list)
    avg_p = sum(f['p'] for f in foods_list) / total_items if total_items > 0 else 0
    avg_f = sum(f['f'] for f in foods_list) / total_items if total_items > 0 else 0
    avg_c = sum(f['c'] for f in foods_list) / total_items if total_items > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("登録食品数", f"{total_items} 件")
    col2.metric("平均タンパク質(P)", f"{avg_p:.1f} g")
    col3.metric("平均脂質(F)", f"{avg_f:.1f} g")
    col4.metric("平均炭水化物(C)", f"{avg_c:.1f} g")

    st.divider()

    # タブで機能を切り替え
    tab_view, tab_add, tab_edit = st.tabs(["📊 食品一覧・グラフ", "➕ 新規登録", "✏️ 編集・削除"])

    # --- タブ1: 一覧とグラフ ---
    with tab_view:
        st.subheader("登録済み食品データ")
        
        if foods_list:
            df = pd.DataFrame(foods_list)
            
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
            st.info("登録されている食品データがまだないわ！下の「新規登録」タブから追加してみてね！")

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
                    # ユーザーIDも渡して保存！
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
