# logic.py - Supabase（クラウドデータベース）連携版
import os
from supabase import create_client, Client

# 環境変数はStreamlit Secretsまたはローカル環境から取得
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

import os
import streamlit as st
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Streamlit Secretsまたは環境変数からURLとKEYを取得してSupabaseクライアントを作成する"""
    url = ""
    key = ""
    
    # 1. Streamlit Secretsから取得を試みる
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        # 2. 環境変数から取得を試みる
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        
    if not url or not key:
        raise ValueError("SUPABASE_URL または SUPABASE_KEY が設定されていないわ！Secretsを確認してね！")
        
    return create_client(url, key)

def load_foods_data():
    """Supabaseからの取得結果やエラーを包み隠さず画面に出す診断版"""
    try:
        supabase = get_supabase_client()
        response = supabase.table("foods").select("*").execute()
        
        # 取得できた生データをそのまま返す
        if response.data:
            return response.data
        else:
            st.warning("⚠️ Supabaseとの通信は成功したけど、データが0件で返ってきたわ！")
            return []
            
    except Exception as e:
        # エラーの内容を画面にでっかく赤字で表示する！
        st.error(f"💥 Supabaseエラー発生: {type(e).__name__} - {e}")
        return []

def add_food_to_json(new_food, filepath=None):
    """新しい食品データをSupabaseのfoodsテーブルに挿入する (関数名は互換性のため維持)"""
    try:
        supabase = get_supabase_client()
        data = {
            "name": new_food["name"],
            "p": float(new_food["p"]),
            "f": float(new_food["f"]),
            "c": float(new_food["c"])
        }
        supabase.table("foods").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error adding food to Supabase: {e}")
        return False

def update_food_in_json(updated_food, filepath=None):
    """指定されたIDの食品データをSupabaseで更新する"""
    try:
        supabase = get_supabase_client()
        data = {
            "name": updated_food["name"],
            "p": float(updated_food["p"]),
            "f": float(updated_food["f"]),
            "c": float(updated_food["c"])
        }
        supabase.table("foods").update(data).eq("id", updated_food["id"]).execute()
        return True
    except Exception as e:
        print(f"Error updating food in Supabase: {e}")
        return False

def delete_food_from_json(food_id, filepath=None):
    """指定されたIDの食品をSupabaseから削除する"""
    try:
        supabase = get_supabase_client()
        supabase.table("foods").delete().eq("id", food_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting food from Supabase: {e}")
        return False

def calculate_target_pfc(gender, age, height_cm, weight_kg, activity_level):
    """ユーザーのスペックから基礎代謝(BMR)・TDEE・目標PFCを計算する"""
    if gender == "男性":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    act_mult = 1.2 if "低" in activity_level else (1.55 if "高" in activity_level else 1.375)
    tdee = bmr * act_mult

    target_p = round(weight_kg * 2.0, 1)
    target_f = round((tdee * 0.20) / 9.0, 1)
    target_c = round((tdee - (target_p * 4.0 + target_f * 9.0)) / 4.0, 1)

    return {
        "tdee": round(tdee),
        "target_p": target_p,
        "target_f": target_f,
        "target_c": target_c
    }

def calculate_consumed_kcal(p, f, c):
    """PFCから総カロリーを計算する"""
    return round(p * 4.0 + f * 9.0 + c * 4.0)
