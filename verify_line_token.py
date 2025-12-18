# -*- coding: utf-8 -*-
import requests
import sys

# 【已修正】直接填入您的 Token 與 User ID，這樣就不怕讀取不到設定檔
# 來源：pi4/core/config.py
LINE_CHANNEL_ACCESS_TOKEN = "qk8lVIzCOe0lJ0eJ9362H7X9jcWsjOhjbULPzLhiNHN9C+HlF4sKF/UVQTrRAFwTiyGAtvbFbvJbY4XMS4SzkjB4hk6KX1ha9Ljmm3AqOFDSpQnyuBzfrSiFuTT5Gm64BEgS9sFF71i8Wu5RP/jwZgdB04t89/1O/w1cDnyilFU="
LINE_TARGET_USER_ID = "U58f2e37ee1ccebb07d8f437c4fa5f976"

def check_token():
    print("=== LINE Token 診斷工具 (獨立版) ===")
    print(f"Token (前10碼): {LINE_CHANNEL_ACCESS_TOKEN[:10]}...")
    print(f"Target User ID: {LINE_TARGET_USER_ID}")
    
    # 1. 測試 Token 有效性 (Get Bot Info)
    print("\n[測試 1] 檢查 Token 有效性...")
    url = "https://api.line.me/v2/bot/info"
    headers = {"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            print("✅ Token 有效！")
            json_data = resp.json()
            print(f"Bot Name: {json_data.get('displayName', 'Unknown')}")
        elif resp.status_code == 401:
            print("❌ Token 無效 (401 Unauthorized)。")
            return
        elif resp.status_code == 429:
            print("⚠️ API 請求次數過多 (429 Too Many Requests)。")
        else:
            print(f"❌ 未知錯誤: {resp.text}")
    except Exception as e:
        print(f"❌ 連線失敗 (可能 Pi 無法上網): {e}")
        return

    # 2. 測試發送訊息 (Push Message)
    print("\n[測試 2] 嘗試發送測試訊息...")
    push_url = "https://api.line.me/v2/bot/message/push"
    payload = {
        "to": LINE_TARGET_USER_ID,
        "messages": [{"type": "text", "text": "【系統測試】這是一條 Token 驗證訊息。"}]
    }
    
    try:
        resp = requests.post(push_url, headers=headers, json=payload, timeout=5)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            print("✅ 訊息發送成功！請檢查手機。")
        elif resp.status_code == 429:
            print("❌ 發送失敗：請求過多 (429)。(可能額度已滿)")
        else:
            print(f"❌ 發送失敗: {resp.text}")
    except Exception as e:
        print(f"❌ 發送連線失敗: {e}")

if __name__ == "__main__":
    check_token()
