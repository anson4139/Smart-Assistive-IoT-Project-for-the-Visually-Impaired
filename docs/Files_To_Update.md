# 需更新檔案清單 (2025/12/18)

請更新以下檔案以部署最新的 LINE 通知功能。

| 檔案名稱 | Windows 路徑 (請複製) | Pi 目標路徑 |
| :--- | :--- | :--- |
| **understanding_ollama_client.py** | `pi4\llm\understanding_ollama_client.py` | `smart_cane/pi4/llm/` |
| **orchestrator.py** | `pi4\core\orchestrator.py` | `smart_cane/pi4/core/` |
| **line_api_message.py** | `pi4\voice\line_api_message.py` | `smart_cane/pi4/voice/` |
| **verify_caregiver_logic.py** | `verify_caregiver_logic.py` | `smart_cane/` |

## 驗證步驟
1. 傳輸完成後，在 Pi 上執行：
   ```bash
   python verify_caregiver_logic.py
   ```
2. 若看到 `Test passed`，則執行主程式：
   ```bash
   python run_pipeline.py
   ```
