# LINE 額度用盡 (429 Error) 解決方案

測試結果顯示您的 Token 有效，但**當月免費額度 (200則) 已用完**。
這是因為舊版程式沒有冷卻機制，短時間內發送過多訊息所致。

## 解決步驟

### 1. 取得新額度
目前無法直接購買額度或重置，最快的方法是 **建立一個全新的 LINE Channel**。
1. 前往 [LINE Developers Console](https://developers.line.biz/console/)。
2. 建立一個新的 Provider (或用現有的)。
3. 建立一個新的 **Messaging API** Channel。
4. 取得新的 **Channel Access Token (Long-lived)**。
5. 掃描 QR Code 加入這個新機器人好友，取得新的 **User ID** (或透過 webhook 取得)。

### 2. 更新 Pi 設定
拿到新資料後，請用 WinSCP 修改 Pi 上的 `pi4/core/config.py`：

```python
# 找到這兩行並填入新資料
LINE_CHANNEL_ACCESS_TOKEN = "貼上新的長 Token"
LINE_TARGET_USER_ID = "貼上新的 U 開頭 ID"
```

### 3. 防止再次發生 (重要!)
請務必確認您的 `pi4/core/orchestrator.py` 是最新的 **V3 (非同步+冷卻版)**。
*   V3 版有 **3秒冷卻時間**。
*   V3 版使用 **背景發送**，不會卡住語音。

若不更新程式，新申請的額度可能在幾分鐘內又會被燒光！
