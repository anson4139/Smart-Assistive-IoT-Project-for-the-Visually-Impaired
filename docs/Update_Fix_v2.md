# 軟體修正更新 (V2)

您剛才的觀察是對的！程式碼**已更新**，但發生了兩個意料之外的問題導致看起來沒變。
1.  **AI 模型不符**: 您的 Pi 是新版 `gemma3`，程式原本死板地只找 `gemma2`，導致 AI 功能失效，回退到舊版語音。
2.  **LINE 發送過快**: 感測器每秒觸發多次，導致 LINE API 瞬間被灌爆 (429 Error)。

我已經針對這兩點進行了**緊急修正**。

## 需更新的檔案 (請再次覆蓋)

請將以下兩個檔案再次複製到 Pi 上覆蓋：

| 檔案名稱 | Windows 路徑 | 修正內容 |
| :--- | :--- | :--- |
| **orchestrator.py** | `pi4\core\orchestrator.py` | 新增 **LINE 冷卻時間 (3秒)**，防止瘋狂發送導致被封鎖。 |
| **understanding_ollama_client.py** | `pi4\llm\understanding_ollama_client.py` | 新增 **自動模型偵測**，若找不到 gemma2 會自動用 gemma3 代替。 |

## 驗證方式
覆蓋後重新執行 `python run_pipeline.py`，您應該會看到：
1.  Log 出現 `Falling back to similar model: gemma3:27b` (或其他可用模型)。
2.  語音內容變為「溫柔志工」口氣 (例如：『小心喔...』)。
3.  LINE 訊息能成功發送，且不會連續狂跳通知。
