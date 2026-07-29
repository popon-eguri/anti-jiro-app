import os
import streamlit as st
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Streamlit Secretsまたは環境変数からURLとKEYを取得してSupabaseクライアントを作成する"""
    url = ""
    key = ""
    
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        
    if not url or not key:
        raise ValueError("SUPABASE_URL または SUPABASE_KEY が設定されていないわ！")
        
    return create_client(url, key)

# --- 🔐 認証用関数 ---

def sign_up(email: str, password: str):
    """新規ユーザー登録"""
    supabase = get_supabase_client()
    response = supabase.auth.sign_up({"email": email, "password": password})
    return response

def sign_in(email: str, password: str):
    """ログイン"""
    supabase = get_supabase_client()
    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    return response

def sign_out():
    """ログアウト"""
    supabase = get_supabase_client()
    supabase.auth.sign_out()

def load_preset_foods():
    supabase = get_supabase_client()
    response = supabase.table("food_presets").select("*").execute()

    if isinstance(response.data, list):
        preset_foods = []
        for item in response.data:
            if isinstance(item, dict) and "name" in item:
                item["p"] = float(item.get("p", 0))
                item["f"] = float(item.get("f", 0))
                item["c"] = float(item.get("c", 0))
                preset_foods.append(item)
        return preset_foods

    return []

def recommend_foods(all_foods, target_p, target_f, target_c):
    """
    不足しているPFCを補うおすすめ食品をスコア順に返す
    """

    # 不足量（マイナスなら0扱い）
    deficit_p = max(target_p, 0)
    deficit_f = max(target_f, 0)
    deficit_c = max(target_c, 0)

    recommendations = []

    for food in all_foods:
        p = food.get("p", 0)
        f = food.get("f", 0)
        c = food.get("c", 0)

        # 不足をどれだけ補えるか（比率）
        score_p = p / deficit_p if deficit_p > 0 else 0
        score_f = f / deficit_f if deficit_f > 0 else 0
        score_c = c / deficit_c if deficit_c > 0 else 0

        # 総合スコア（重み付け）
        score = score_p * 0.4 + score_f * 0.3 + score_c * 0.3

        recommendations.append({
            "name": food["name"],
            "p": p,
            "f": f,
            "c": c,
            "score": score
        })

    # スコア順に並べる
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    return recommendations

    def add_intake_log(user_id, food_id):
        supabase = get_supabase_client()
        response = supabase.table("intake_logs").insert({
            "user_id": user_id,
            "food_id": food_id
        }).execute()
        return response.data

    def load_today_intake(user_id):
        supabase = get_supabase_client()
        response = supabase.table("intake_logs") \
            .select("food_id") \
            .eq("user_id", user_id) \
            .eq("taken_at", date.today().isoformat()) \
            .execute()
        return response.data or []


# --- 🗄️ データ操作関数（ユーザーID連携版） ---

def load_foods_data(user_id: str):
    """ログイン中ユーザーの食品データのみを取得する"""
    try:
        supabase = get_supabase_client()
        # eq("user_id", user_id) で自分のデータだけに絞り込み！
        response = supabase.table("foods").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
        
        if isinstance(response.data, list):
            valid_foods = []
            for item in response.data:
                if isinstance(item, dict) and "name" in item:
                    item["p"] = float(item.get("p", 0))
                    item["f"] = float(item.get("f", 0))
                    item["c"] = float(item.get("c", 0))
                    valid_foods.append(item)
            return valid_foods
        return []
    except Exception as e:
        st.error(f"🚨 データ取得エラー: {e}")
        return []

def add_food_data(name: str, p: float, f: float, c: float, user_id: str):
    """新規食品データを追加（user_idを紐付け）"""
    try:
        supabase = get_supabase_client()
        new_data = {
            "name": name,
            "p": p,
            "f": f,
            "c": c,
            "user_id": user_id  # 🔑 誰が追加したか記録！
        }
        response = supabase.table("foods").insert(new_data).execute()
        return response
    except Exception as e:
        st.error(f"🚨 データ追加エラー: {e}")
        return None

def update_food_data(food_id: str, name: str, p: float, f: float, c: float):
    """既存食品データを更新"""
    try:
        supabase = get_supabase_client()
        update_data = {
            "name": name,
            "p": p,
            "f": f,
            "c": c
        }
        response = supabase.table("foods").update(update_data).eq("id", food_id).execute()
        return response
    except Exception as e:
        st.error(f"🚨 データ更新エラー: {e}")
        return None

def delete_food_data(food_id: str):
    """食品データを削除"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("foods").delete().eq("id", food_id).execute()
        return response
    except Exception as e:
        st.error(f"🚨 データ削除エラー: {e}")
        return None

