# LINE 設定資訊備忘

幫您找到了！這兩組資料目前是直接寫在 **`pi4/core/config.py`** 的第 105 行與 107 行：

*   **Token**: `qk8lVIzCOe0lJ0eJ9362H7X9jcWsjOhjbULPzLhiNHN9C+HlF4sKF/UVQTrRAFwTiyGAtvbFbvJbY4XMS4SzkjB4hk6KX1ha9Ljmm3AqOFDSpQnyuBzfrSiFuTT5Gm64BEgS9sFF71i8Wu5RP/jwZgdB04t89/1O/w1cDnyilFU=`
*   **User ID**: `U58f2e37ee1ccebb07d8f437c4fa5f976`

**操作建議：**
`verify_line_token.py` 會自動去讀這個檔案，所以您**不需要手動填寫**那段程式碼。
請只要確認：
1.  **更新 `verify_line_token.py`** (加入編碼修正的那版)。
2.  直接在 Pi 執行 `python verify_line_token.py`，它就會自動讀取上述這兩組設定來進行測試。
