# Python 概覽（RulebyPY）

此文件以表格方式列出 `smart_cane` 主要 Python 模組的職責與互動，讓開發者與 agent 可快速掌握每個 `.py` 的定位。

| 區域 | 檔案 / 模組 | 主要責任 | 備註 |
| --- | --- | --- | --- |
| CLI / 測試 | `run_pipeline.py` | 提供 [1]~[10] CLI 選單連結各種單元/連線/整合測試、`tools`、`pi4.core.orchestrator` 等功能，選項 7 會在進 Safety 前先驗證 Ollama。 | 不直接存取硬體/API，只呼叫高層 helper。 |
| 核心協調 | `pi4/core/config.py` | 集中平台/相機/ToF/LLM/OpenVINO/TTS/語音冷卻的設定，支援 `SMART_CANE_*` 環境變數，新增 `OLLAMA_REWRITE_TIMEOUT_SEC` 等可調參數。 | 其他模組從這裡 import；需變更預設時同步更新 `docs/SYSTEM_SPEC.md`。 |
|  | `pi4/core/orchestrator.py` | 安排 Safety 主 loop：等 Voice 空閒後讀 frame/距離、發事件、播 Safety 語音、呼叫 Ollama rewrite、寫 log，並在每圈後以 `summarize_events()` 產生摘要供 `log_analysis`。 | 透過 `MAIN_LOOP_INTERVAL_SEC` 控制頻率；若 Voice 忙碌會暫停 frame 讀取。 |
|  | `pi4/core/event_bus.py` + `event_schema.py` | 提供事件發佈/訂閱與 `Event`/`ConversationContext` 資料結構，包含 severity、distance_m、direction、extra 等欄位。 | `log_analysis()` 寫入 `data/analyze/`。 |
|  | `pi4/core/analyzer.py` / `pi4/core/logger.py` | 實作 JSON logging、分析記錄與全域 logger 設定。 | 用於 `orchestrator` / LLM / Voice 的統一 log。 |
| 感測與 Safety | `pi4/safety/vision/*.py` | `camera_capture` 取得影格、`ncs_inference` 推 OpenVINO、`vision_safety` 估距離與 severity、`frame_storage` 管理快照。 | 產生 `camera.events` / `danger.events`，並記錄 `distance_m`、`object_label` / `bbox` 等欄位。 |
|  | `pi4/safety/cane_client/*.py` | `tof_receiver` 讀取最新 ToF 距離、`cane_safety.eval_distance` 針對 drop/step/hole 輸出 `Event`。 | 與 camera 事件共同構成 Safety 判斷；有實體與模擬版本。 |
| LLM｜理解 | `pi4/llm/understanding_ollama_client.py` | `rewrite_voice_text` 呼叫 `http://localhost:11434/v1/chat/completions` 將 Safety 語句改寫、`summarize_events` 整理摘要供 log、`_get_available_models` 快取清單。 | 以 `OLLAMA_REWRITE_TIMEOUT_SEC` 控制 rewrite timeout；成功會在 `VoiceOutput` 標記 `[Ollama]`。 |
|  | `pi4/llm/conversation_chatgpt_client.py` | `ConversationContext` 集中 camera/cane 事件；`answer_question` 對 ChatGPT 請求。 | 若 `OPENAI_ENABLED` 關閉或缺 `OPENAI_API_KEY`，會返回友善提示而不 crash。 |
| 語音 I/O | `pi4/voice/voice_output.py` | `pyttsx3` queue 排程，播放前 `init()`, `say()`, `runAndWait()`，完後 `engine.stop()`。 | `source` 字串標記 `[Ollama]` / `[NAN]`，方便 `data/analyze` 對照。 |
|  | `pi4/voice/voice_control.py` | 監聽 `WAKE_WORDS`，包裝 callback，供選項 10 啟動語音控制。 | 依賴 `speech_recognition` / `PyAudio`。 |
|  | `pi4/voice/line_api_message.py` | `LineNotifier` 封裝 LINE Push，選項 2 測 `LINE_CHANNEL_ACCESS_TOKEN` / `LINE_TARGET_USER_ID`。 | 用於推播警示或進度。 |
| 測試 | `tests/*.py` | 每支測試檔提供 `run_tests_unit()` / `run_*_smoke_test()`，`run_pipeline` 將其綁定成選項。 | `test_llm_connectivity` 會實際 ping Ollama/OpenAI；`continuous_safety_monitor` 可獨立跑 Safety + Voice。 |
| 工具 | `tools/*.py` | 提供相機 debug、OpenVINO 驗證、環境設定、專案 bundle/還原等腳本。 | `export_as_text` / `restore_from_text` 會過濾 `config.BUNDLE_IGNORE_DIRS`。 |
| 拐杖端 | `pico_firmware/src/main.py` + `tof_driver.py` | Pico 以 `VL53L0X` 每 0.1s 輸出 JSON，透過 UART 傳給 Pi4；`tof_receiver` 解析。 | 提供 Pi4 ToF 原始資料。 |

## 互動流程補充
1. `run_pipeline` 選項 7 → `orchestrator.main_loop()` → camera + ToF 產生 `Event` → Safety 播出、`understanding_ollama_client.rewrite_voice_text()` 取得 `[Ollama]` 版本並在 `voice_distance_alert` log 記錄原始/重寫內容。
2. 每圈結束後 `recent_danger_events` 交給 `summarize_events()` 產生摘要，僅寫入 `log_analysis`（`understanding_summary_*`），避免與 Safety 語音重複。
3. 選項 4/5 讓手動確認 Ollama / ChatGPT；`tests.test_llm_connectivity` 與選項 7 前的 Ollama smoke test 自動驗證 LLM，可在 `OLLAMA_ENABLED` 或 `OPENAI_ENABLED` 關閉時 graceful fail。

---

任何新增 Python 功能請同步更新這份 RulebyPY，讓 agent / 開發者能快速釐清行為與測試流程。