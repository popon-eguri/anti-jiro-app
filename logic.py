# logic.py - バックエンド（演算・データ処理モジュール）
import json

def load_foods_data(filepath="foods.json"):
    """JSONファイルから食品データを読み込む"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

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
    """PFCから総カロリーを計算する (P:4kcal, F:9kcal, C:4kcal)"""
    return round(p * 4.0 + f * 9.0 + c * 4.0)

def add_food_to_json(new_food, filepath="foods.json"):
    """新しい食品データをfoods.jsonに追記保存する"""
    foods = load_foods_data(filepath)
    
    # 重複防止用IDの生成（簡易的）
    new_food["id"] = f"custom_{len(foods) + 1}"
    foods.append(new_food)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(foods, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving food: {e}")
        return False

    # logic.py の末尾に追記

def delete_food_from_json(food_id, filepath="foods.json"):
    """指定されたIDの食品をfoods.jsonから削除する"""
    foods = load_foods_data(filepath)
    # 対象のID以外の食品だけで新しいリストを作成（フィルタリング）
    updated_foods = [f for f in foods if f.get("id") != food_id]
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(updated_foods, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error deleting food: {e}")
        return False

def update_food_in_json(updated_food, filepath="foods.json"):
    """指定されたIDの食品データを更新してfoods.jsonに上書き保存する"""
    foods = load_foods_data(filepath)
    
    for i, f in enumerate(foods):
        if f.get("id") == updated_food["id"]:
            foods[i] = updated_food
            break

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(foods, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error updating food: {e}")
        return False