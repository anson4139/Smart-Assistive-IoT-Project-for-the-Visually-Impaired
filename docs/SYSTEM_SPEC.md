# 智慧盲人行走輔助系統 – 程式面系統規格書（v2.3）

> 給人類開發者與 AI coding agent 使用。
> 核心原則：
>
> * 所有「安全相關判斷」必須在 **Safety Layer** 完成，LLM 不得直接決定安全動作。
> * 系統需支援：**先在筆電 (desktop) 開發 / 模擬，再部署到 Raspberry Pi 4 (pi4)**。

---

## 0. 專案與資料夾結構

根目錄預設名稱：`smart_cane/`

```text
smart_cane/
├─ .env.sample                  # 樣板環境變數（可複製到 .env）
├─ .pytest_cache/               # pytest cache（由 pytest 自動生成）
├─ .vscode/                     # VS Code workspace 設定（launch.json、settings.json）
├─ data/                        # 模擬資料、擷取影格與分析輸出
│   ├─ analyze/                 # `orchestrator` 與 LLM 產生的分析文字檔（含 `_voice` 標籤）
│   ├─ img/                     # `camera_capture` 儲存的快照（img_YYYYmmddHHMMSS.jpg）
│   └─ tof_simulated.json       # ToF 模擬距離序列
├─ docs/
│   ├─ SYSTEM_SPEC.md          # 本規格書
│   ├─ RulebyPY.md             # Python 程式總覽（更新後的 RulebyPY doc）
│   ├─ EVENT_SCHEMA.md         # Event schema 與範例
│   ├─ HW_BOM.md               # 硬體物料清單與接線摘要
│   └─ agents/
│       ├─ PG_AGENT.md         # PG agent 實作指引
│       ├─ SA_AGENT.md         # SA agent 安全維護手冊
│       └─ TEST_AGENT.md       # TEST agent 測試與驗證流程
├─ logs/                        # `smart_cane.log` + Python logging output
├─ models/                      # OpenVINO / NCS2 模型與子資料夾
│   ├─ intel/
│   │   └─ person-detection-retail-0013/
│   │       └─ FP16/
│   │           ├─ person-detection-retail-0013.bin
│   │           └─ person-detection-retail-0013.xml
│   ├─ person-detection-retail-0013.bin
│   └─ person-detection-retail-0013.xml
├─ pi4/                        # Python 主系統：Safety、LLM、Voice、Core
│   ├─ __init__.py
│   ├─ core/
│   │   ├─ analyzer.py          # 分析記錄與 JSON 儲存工具
│   │   ├─ config.py            # 集中設定（平台、LLM、TTS、硬體等）
│   │   ├─ event_bus.py         # Pub/Sub 事件總線
│   │   ├─ event_schema.py      # Event、ConversationContext 等 data class
│   │   ├─ logger.py            # logging 設定與等級
│   │   ├─ orchestrator.py      # 主流程控制與三層協調
│   │   ├─ safety_support.py    # Safety 側 helper（如 event buffering）
│   │   └─ voice_service.py     # VoiceOutput 抽象與排程支援
│   ├─ safety/
│   │   ├─ __init__.py
│   │   ├─ cane_client/
│   │   │   ├─ cane_safety.py
│   │   │   ├─ tof_receiver.py
│   │   │   ├─ tof_receiver_pi.py
│   │   │   ├─ tof_receiver_sim.py
│   │   │   └─ __init__.py
│   │   └─ vision/
│   │       ├─ camera_capture.py
│   │       ├─ camera_capture_pi.py
│   │       ├─ camera_capture_sim.py
│   │       ├─ frame_storage.py
│   │       ├─ ncs_inference.py
│   │       ├─ vision_safety.py
│   │       └─ __init__.py
│   ├─ llm/
│   │   ├─ __init__.py
│   │   ├─ conversation_chatgpt_client.py
│   │   └─ understanding_ollama_client.py
│   └─ voice/
│       ├─ __init__.py
│       ├─ line_api_message.py
│       ├─ voice_control.py
│       └─ voice_output.py
├─ pico_firmware/                # 拐杖端 Pico 2 WH 韌體
│   ├─ drivers/
│   │   └─ vl53l0x.py           # VL53L0X I2C driver
│   ├─ README.md
│   └─ src/
│       ├─ main.py
│       └─ tof_driver.py
├─ read_pico_tof_v2.py         # PC/Pi 端測試工具：讀取 Pico USB JSON
├─ README.md                    # 專案說明、快速指令與排錯
├─ requirements.txt            # `pip install -r requirements.txt`
├─ run_pipeline.py             # CLI 選單與測試 / 模擬 / 全流程入口
├─ tools/
│   ├─ __init__.py
│   ├─ calibrate_detection.py
│   ├─ camera_debug.py
│   ├─ detect_from_latest_image.py
│   ├─ export_as_text.py
│   ├─ pi4_quick.sh
│   ├─ restore_from_text.py
│   ├─ setup_env.py
│   └─ verify_openvino.py
└─ tests/
    ├─ __init__.py
    ├─ continuous_safety_monitor.py
    ├─ test_continuous_safety_monitor.py
    ├─ test_event_schema.py
    ├─ test_vision_safety.py
    ├─ test_cane_safety.py
    ├─ test_llm_clients.py
    ├─ test_llm_connectivity.py
    └─ test_voice_control.py
```

---

## 1. config.py – 平台與所有設定集中管理

檔案：`pi4/core/config.py`
原則：**所有可調設定都寫在這裡**。
API key 等敏感資訊從環境變數 / .env 讀取，**不可寫死**。

### 1.1 平台 / 模式

```python
from typing import Literal
import os

# 平台模式
PLATFORM: Literal["desktop", "pi4"] = os.getenv("SMART_CANE_PLATFORM", "desktop")
# 永遠以真實硬體為準，除非特別開啟模擬
USE_SIMULATED_SENSORS: bool = False
```

### 1.2 視覺 / ToF 硬體與模擬設定

```python
# 相機
CAMERA_DEVICE_INDEX: int = 1
SIM_VIDEO_PATH: str = os.getenv("SMART_CANE_SIM_VIDEO", "./data/demo_video.mp4")

# ToF / UART
TOF_SERIAL_PORT: str = "COM3"
TOF_BAUDRATE: int = 115200

# 桌機 ToF 模擬資料
SIM_TOF_DATA_PATH: str = os.getenv("SMART_CANE_SIM_TOF", "./data/tof_simulated.json")
SIM_TOF_INTERVAL_SEC: float = float(os.getenv("SMART_CANE_SIM_TOF_INTERVAL", "0.1"))
```

### 1.3 Safety 門檻（相機＋拐杖）

```python
# 視覺 safety
PERSON_NEAR_DISTANCE_M: float = 1.5
CAR_APPROACHING_MIN_DISTANCE_M: float = 3.0
CAR_APPROACHING_SPEED_THRESHOLD: float = 1.0    # m/s 或等效指標

# ToF safety
DROP_MIN_DISTANCE_M: float = 0.05
DROP_MAX_DISTANCE_M: float = 0.40
STEP_MIN_HEIGHT_M: float = 0.10                 # 預留

# 危險事件收集時間窗（給理解層用）
DANGER_EVENT_WINDOW_SEC: float = 2.0

# 主迴圈
MAIN_LOOP_INTERVAL_SEC: float = 0.05
MAIN_LOOP_DURATION_SEC: float = 60.0  # run_pipeline 選項 9 的預設持續秒數
```

### 1.4 LLM 設定（Ollama / ChatGPT）

```python
# 共用
LLM_TIMEOUT_SEC: float = 15.0
OLLAMA_REWRITE_TIMEOUT_SEC: float = 12.0

# Ollama (Understanding Layer)
USE_UNDERSTANDING_LAYER: bool = True
OLLAMA_ENABLED: bool = True
OLLAMA_BASE_URL: str = "http://localhost:11434"
OLLAMA_MODEL: str = "gemma2:9b"
OLLAMA_REWRITE_TIMEOUT_SEC: float = 30.0

# ChatGPT (Conversation Layer)
USE_CONVERSATION_LAYER: bool = False  # 預設關閉
OPENAI_ENABLED: bool = True
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL: str = "gpt-4.1-mini"
OPENAI_API_BASE: str = "https://api.openai.com/v1"
```

**要求：**

* 若 `OPENAI_API_KEY` 是 `None` 或空字串，`conversation_chatgpt_client` 必須回傳「無合法 key」型態錯誤，而不是直接 crash。
* 若 `OLLAMA_ENABLED` 或 `OPENAI_ENABLED` 為 False，對應 client 要直接跳出不呼叫 API。

### 1.5 語音輸入 / 輸出設定

```python
# 語言
LANGUAGE_CODE: str = "zh-TW"

# TTS 引擎
from typing import Literal as _Literal
TTS_ENGINE: _Literal["edge-tts", "espeak", "local"] = "edge-tts"
TTS_TEMP_DIR: str = "/tmp/"

# 音訊輸出裝置 (視實作決定是否使用)
DESKTOP_AUDIO_OUTPUT_DEVICE: str | None = None
PI4_AUDIO_OUTPUT_DEVICE: str | None = None

# 喚醒詞
WAKE_WORDS: list[str] = ["小A", "嗨小A"]

# 錄音參數（可視實作精簡）
VOICE_SAMPLE_RATE: int = 16000
VOICE_CHUNK_MS: int = 30
```

### 1.6 Logging / bundle / 忽略資料夾

```python
LOG_LEVEL: str = "INFO"
LOG_DIR: pathlib.Path = pathlib.Path("./logs")
LOG_FILE_NAME: str = "smart_cane.log"

# 匯出 / 還原 bundle
BUNDLE_DEFAULT_OUTPUT: str = "smart_cane_bundle.txt"
BUNDLE_IGNORE_DIRS: list[str] = [".git", "__pycache__", ".venv", "logs", "tmp"]
```

---

## 2. 模組與 API 規格（摘要）

> 這節大致沿用 v2 的定義，這裡只補關鍵重點，詳細可以拆到各自的 .py 裡寫 docstring。

### 2.1 Event Schema（`pi4/core/event_schema.py`）

```python
from dataclasses import dataclass
from typing import Literal, Optional
from datetime import datetime

@dataclass
class Event:
    event_id: str
    ts: datetime
    type: str
    source: str                        # "camera" / "tof" / "voice" / "system"
    severity: Literal["low", "mid", "high", "critical"]
    distance_m: Optional[float] = None
    direction: Optional[str] = None
    extra: dict = None
```

### 2.2 Safety – 視覺（`pi4/safety/vision/*`）

* `camera_capture.py` 對外只暴露：

  ```python
  def get_frame() -> "np.ndarray":
      """依 config 返回一張影像 (BGR/RGB)。"""
  ```

* `ncs_inference.py`：

  ```python
  @dataclass
  class DetectedObject:
      label: Literal["person", "car", "bike", "other"]
      bbox: tuple[int, int, int, int]   # x1, y1, x2, y2
      confidence: float

  def detect_objects(frame) -> list[DetectedObject]:
      ...
  ```

* `vision_safety.py`：

  ```python
  from pi4.core.event_schema import Event

  def process_frame(frame) -> list[Event]:
      """
      1. 呼叫 detect_objects()
      2. 估距離 & 方向
      3. 依 config 產生 camera_events / danger_events
      """

#### 2.2.2 常駐距離偵測與語音告警

* 每一張送進 `vision_safety.process_frame` 的 frame 都會分析 `DetectedObject` 之 `bbox_height`，再套用預設身高與焦距計算距離：
  ```python
  distance_m = (ACTUAL_HEIGHT_M * config.VISION_FOCAL_LENGTH) / bbox_height_px
  ```
* 這個距離會寫入 `Event.distance_m`、`Event.object_label`、以及 `Event.bbox`; 同時對 `Event.severity` 的決策仍由 `vision_safety` 以 `config.PERSON_NEAR_DISTANCE_M` / `config.CAR_APPROACHING_MIN_DISTANCE_M` 判斷。
* 只要 `distance_m` 低於對應門檻且 `severity >= mid`，`orchestrator` 會立刻用 voice 播出：「前方有 {object_label}，距離約 {distance_m:.1f} 公尺，請注意」。該語句會在 `VoiceOutput` log 中標記 priority 與 `data/analyze` 檔名新增 `_voice_distance` tag。
* 若 `distance_m` 超過門檻，Safety 仍會記錄 event 與 analyzer，但語音則由 Understanding/Conversation 依 `recent_danger_events` 與 `ConversationContext` 生成成段回覆。
* SA 必須在此段補齊：距離公式使用的 `config` 值、需要新增的 analyzer tag、以及 `Event` 需包含 `distance_m`/`object_label`/`bbox` 的 JSON 範例；後續 PG 實作必依此 spec 做最小修改。

#### 2.2.1 Detection → Event 詳細流程

* 主要使用 OpenVINO/NCS2 輸出標記：`DetectedObject(label, bbox, confidence)`。
* 由 `vision_safety` 根據配置的高度、寬度與座標，估算距離、方向、速度等數值。
* 只有符合 `config` 中 `PERSON_NEAR_DISTANCE_M`、`CAR_APPROACHING_MIN_DISTANCE_M` 或 `vision_safety` 專屬閾值時，才會為該物件建立 `severity` 為 `mid/high/critical` 的 `Event`，並發佈到 `camera.events` & `danger.events`。
* VoiceOutput 只有在 Safety 事件（camera/cane）產生且 severity ≥ mid 時才直接播報；Otherwise 只是記錄照片與語音標記，等待理解/對話層產生補充文字，這樣保證系統不是單純描述照片，而是真正偵測到變化才發聲。
* 若要新增新的 detection type、distance formula 或派生語音描述，**必須**把欄位/流程補入本規格 (Section 2、3、4)，確保後續 agent / 人類開發者能查到原因。每次變動應至少包含：
  * 變更哪個 `vision_safety` 或 `event_schema` 欄位
  * 需要新增的 voice 文案或 analyzer tag
  * 測試能模擬的 scenario
  ```

### 2.3 Safety – 拐杖 ToF（`pi4/safety/cane_client/*` + `pico_firmware`）

* Pico 端：`main.py` 每 0.1s 輸出：

  ```text
  {"ts": 1710000000.123, "distance_mm": 430}
  ```

* Pi4 端：

  ```python
  # tof_receiver.py
  def read_latest_distance() -> float | None:
      """回傳「最近一次」距離（公尺），沒有資料時回 None。"""

  # cane_safety.py
  from pi4.core.event_schema import Event

  def eval_distance(distance_m: float) -> list[Event]:
      """根據 config 判斷 drop / step，回傳 Event list。"""
  ```

### 2.4 LLM – Understanding (Ollama)

`pi4/llm/understanding_ollama_client.py`：

```python
from pi4.core.event_schema import Event

def summarize_events(events: list[Event]) -> str:
    """
    將 0~N 個 danger_events 整理成一句「短中文提示」。
    超時或失敗時，可丟例外或回傳空字串，由 orchestrator fallback。
    """
```

### 2.5 LLM – Conversation (ChatGPT)

`pi4/llm/conversation_chatgpt_client.py`：

```python
from dataclasses import dataclass
from datetime import datetime
from pi4.core.event_schema import Event

@dataclass
class ConversationContext:
    camera_events: list[Event]
    cane_events: list[Event]
    position: str
    time: datetime

def answer_question(ctx: ConversationContext, user_query: str) -> str:
    """
    根據 context + user_query 回一段中文說明。
    不得出現「一定安全」「完全沒問題」這種字眼。
    """
```

### 2.6 Voice

* `voice_control.listen_loop(callback_on_query)`：背景 loop；有喚醒詞時呼叫 callback。
* `voice_output.speak(text, priority)`：排入播放 queue，高優先 priority 可插隊。

### 2.7 Orchestrator / Event Bus

* `event_bus.EventBus` 提供 `publish()` / `subscribe()`。
* `orchestrator.main_loop()`：實機 / 桌機共用主流程。
* 可另外提供 `orchestrator.run_safety_simulation()` 給桌機模擬。

---

## 3. 資料流 & 串接關聯（獨立完整說明）

這一節專門講「資料怎麼流、誰跟誰講話」，讓你 / agent 一眼就懂整個 pipeline。

### 3.1 高階流程圖（文字版）

1. **Sensors（感測）**

   * Camera + NCS2 → 影像 frame → `vision_safety.process_frame()` → `camera_events` / `danger_events`
   * Pico + ToF → 距離資料 → `cane_safety.eval_distance()` → `cane_events` / `danger_events`
   * 麥克風 → `voice_control.listen_loop()` → `user_query`（含喚醒詞資訊）

2. **Safety Layer**

   * 持續接收 camera / ToF 原始資料；
   * **事件觸發 (Event-Triggered)**：
     * 平常相機處於待機 (Standby) 狀態，不進行辨識以節省資源。
     * 當收到 Pico 傳來的 `trigger` 訊號 (距離 < 1.2m) 時，立即喚醒相機抓拍一張影像。
   * 依 config 門檻生成 `Event`：

     * 安全相關的一律標為 `severity = mid/high/critical`；
   * 立即：

     * 發布 `danger.events` 到 event_bus；
     * 對嚴重事件可直接呼叫 `voice_output.speak(固定句型, priority="high")`；
   * **不需要 LLM 就能獨立運作**。

3. **Understanding Layer（可選）**

   * 每隔一小段時間，`orchestrator` 從「近期 `danger_events` 緩衝」抓出一批事件；
   * 若 `config.USE_UNDERSTANDING_LAYER` 為 True 且 Ollama 連線正常：

     * 呼叫 `summarize_events(events)` → 短中文提示；
     * 將摘要寫入 `log_analysis`（目前不會再播 summary 語音，以免與 Safety 重複）。
   * 若 Ollama 失敗或 disabled：

     * 使用本地 fallback：將危險事件逐條套固定句型講出來。

4. **Conversation Layer（對話）**

   * `voice_control.listen_loop()` 偵測到喚醒詞（「小A」…）＋ 使用者問題；
   * `orchestrator` 取出最近一段時間的：

     * `camera_events`（環境大致狀況）
     * `cane_events`（腳下狀況）
   * 組成 `ConversationContext` + `user_query` → `answer_question()`；
   * 回傳長一點的中文說明，交由 `voice_output` 播報。
   * **不做安全判斷，只做解釋 / 建議**。

5. **Output（輸出）**

   * 所有播報都經過 `voice_output` 統一排程，避免互相蓋來蓋去；
   * 高優先權（Safety）的訊息可以中斷 / 插隊在 Understanding / Conversation 之前。

### 3.2 事件管線細節

* `vision_safety.process_frame()` 運作過程中：

  * 每個 frame 產生 0~N 個 `Event`，透過 event_bus 發布：

    * `topic="camera.events"`：所有視覺事件（包含安全與一般）；
    * 若 `severity` ≥ mid，另發 `topic="danger.events"`。

* `cane_safety.eval_distance(distance)` 類似：

  * 產生 `cane_events` / `danger_events`，發佈到 event_bus。

* `orchestrator` 內部維護：

  * `recent_camera_events`（例如最近 3~5 秒）
  * `recent_cane_events`
  * `recent_danger_events`（由 `danger.events` topic 收集）

### 3.3 Safety 與 LLM 的「責任切割」

* Safety Layer 負責：

  * 是否有危險？
  * 危險等級是什麼？
  * 需不需要立刻提醒？
* LLM 層（Understanding / Conversation）只負責：

  * **怎麼說**（語言包裝、合併多事件）
  * 解釋目前偵測到的狀況
* 如果 Safety 判斷「危險」：

  * 即使 LLM 認為貌似安全，也不可以取消 Safety 的警示；
  * LLM 回答中若出現與 Safety 結論衝突的內容，視為 bug。

  ### 3.4 影像與分析紀錄

  * `camera_capture.get_frame()` 會將每張影格保存到 `data/img/`，檔名格式為 `img_YYYYmmddHHMMSS.jpg`，並透過 `get_latest_image_name()` 暴露最新檔名供分析邏輯使用。
  * `pi4.core.analyzer.log_analysis()` 的紀錄寫入 `data/analyze/`：
    * 檔名由照片檔名、回應摘要與時間戳組成（例如 `img_20251119..._前方100公分有石塊_20251119120000.txt`）。
    * 檔案內容為 JSON 結構，包含照片名稱、描述文字、LLM 回應與產生時間，方便事後查閱分析歷程。

  ### 3.4.1 LINE Messaging API（準備中）

  * `pi4/voice/line_api_message.py` 封裝 LINE Messaging API 的 `/v2/bot/message/push` 呼叫，`LineNotifier.send(message, target_user_id)` 會把純文字推播到指定的 LINE user。若未提供 `target_user_id`，預設會使用 `LINE_TARGET_USER_ID`。
  * `LineNotifier` 使用 `LINE_CHANNEL_ACCESS_TOKEN` 進行授權，`LINE_CHANNEL_SECRET` 只作為紀錄與未來 webhook 驗證；Service 需要把 `LINE_TARGET_USER_ID`、`LINE_CHANNEL_ACCESS_TOKEN` 寫在 `pi4/core/config.py` 中，以利 `run_pipeline [13]` 或 Safety/Voice 事件直接呼叫。token 或 user_id 缺少時會記下 warning，並回傳 False。
  * `VoiceCommandHandler` 現在會在 `report_departure` / `report_arrival` handler 中呼叫 `_send_line_message`，使用 `LineNotifier` 傳送進度提醒；這也同時留下一個可供日後其他事件串接的 hook。
  * `docs/SYSTEM_SPEC.md` 中 Section 6 的 `run_pipeline` 選單的 [2] 項目是 LINE 訊息測試，方便單獨驗證 token 與網路是否可用。之後要把 Safety judgment 事件綁定到 LINE，直接復用同一個 `LineNotifier` instance 即可。

### 3.4.2 Ollama 用於語音播報的文字修飾

  * Safety Layer（`vision_safety` 或 `cane_safety`）會在 `danger.events` 中填入 `distance_m`、`direction`、`severity` 等欄位，並同步把原始語音文案（例如 "前方 1.2 公尺有行人"）存到 `extra['prompt']` 或 analyzer 記錄。
  * Understanding Layer（`llm.understanding_ollama_client`）未來會以此資料作 prompt：描述目前場景 + 期待產出「友善、口語化、適合盲人聽的語句」，避免使用過多 technical word，並在必要時加入重點提示（例如距離、方向、建議速度）。
  * `Orchestrator` 中的 flow 會改成：處理每個 `danger.events` 時先生成 Safety 原始的播報文字，若 `USE_UNDERSTANDING_LAYER` 開啟則呼叫 `understanding_ollama_client.rewrite_voice_text` 讓 Ollama 依照「親民、盲人友善」的 prompt 重寫，再交給 `VoiceOutput.speak()`；同時在 `data/analyze` 的 `voice_distance_alert` log 裡紀錄原始 (`voice_text`) 與重寫後 (`rewritten_voice_text`) 的內容，以便後續分析與測試。`understanding_ollama_client.summarize_events()` 則只負責產生中文摘要並透過 `log_analysis` 記錄，避免與 Safety voice 重複訊息。
  * 如需驗證，可以在 `tests` 中 mock 出一組 `Event`（`distance_m`、`direction`、`extra['prompt']`）給 `understanding_ollama_client.summarize_events()`，確認輸出符合「親民、盲人友善」的語音稿。

  ### 3.5 實機環境設定範本

  * 請依 `SMART_CANE_*` 變數設定相機、OpenVINO 模型、TTS 參數等；可以複製 `.env.sample` 並套入實機路徑與金鑰。
  * `SMART_CANE_OPENVINO_MODEL_XML` / `SMART_CANE_OPENVINO_MODEL_BIN` 應指向 OpenVINO detection model 的 XML / BIN。若模型無法載入，Safety flow 仍會安全退回不產生事件。
  * `SMART_CANE_TTS_ENGINE=edge-tts`：指定使用微軟 Edge-TTS。
  * `SMART_CANE_TTS_VOLUME`：控制播放音量 (透過 mpg123 或 alsa)。

### 3.5.1 `.env.sample` 與 `models/`

* 根目錄提供 `.env.sample` 作為任何平台的環境變數範本，內容涵蓋：
  * `SMART_CANE_PLATFORM=pi4`、`SMART_CANE_USE_SIMULATED=false`：指定 Pi4 實機；`CAMERA_DEVICE_INDEX` 預設已在 `pi4/core/config.py` 設為 `1`，若要測試其他 camera 不需重新設定 `.env`，可直接在那裡調整。
  * `SMART_CANE_OPENVINO_ENABLED=true`、`SMART_CANE_OPENVINO_MODEL_XML=/home/pi/models/person-detection-retail-0013.xml`、`SMART_CANE_OPENVINO_MODEL_BIN=/home/pi/models/person-detection-retail-0013.bin`、`SMART_CANE_OPENVINO_DEVICE=CPU`、`SMART_CANE_OPENVINO_CONFIDENCE=0.6`：指向 Pi4 上的 OpenVINO models 目錄並設定 confidence 閾值。
  * `SMART_CANE_TTS_ENGINE=edge-tts`：設定語音引擎。
  * `SMART_CANE_LLM_MODEL=gemma2:9b`：指定 Ollama 使用的 LLM 模型。
  * `OPENAI_API_KEY=your-secret-key`：測試用 placeholder，實際部署請提供真實金鑰。
  * `SMART_CANE_LOG_DIR=./logs`：自訂 log 目錄。
* `models/` 目錄儲存 OpenVINO 模型：根下有 `person-detection-retail-0013.xml` / `.bin`，以及 `models/intel/person-detection-retail-0013/FP16/` 中的同名檔案。這些可以直接複製到 Pi4 `/home/pi/models/`，或根據 `.env` 指定的路徑進行調整。

  ---

  ## 9. 規格維護要求

  * 每次 Safety Layer、Event Schema、Voice、LLM 或工具的行為變動後，**SA agent / 開發者必須補上本規格的對應章節**，說明變更的動機與影響。舉例：
    * 新增 `DetectedObject` label 或 `Event` type → 更新 Section 2.2 / 2.1 描述；並在 `docs/EVENT_SCHEMA.md` 補充範例。
    * 調整 voice 播報策略或 analyzer tag → 更新 Section 3.4 及 README 相關段落。
    * 更換推理模型或相機 index → 更新 Section 1、Section 3.5、`.env.sample`。
   * 所有變更需在 git commit message/PR 描述內提及對應的 spec 章節，方便 reviewer 確認文件同步。

---

## 4. 專案封裝與還原（export / restore）

和你前面講的一樣，我只把重點留在規格：

### 4.1 tools/export_as_text.py（筆電）

* CLI：

  ```bash
  python tools/export_as_text.py --root . --output smart_cane_bundle.txt

  When running from Windows or other non-Pi hosts, pass `--platform desktop` so the tool uses an OS-friendly default bundle path instead of the Pi-specific home directory.
  ```

* 功能：

  * 遞迴列出 `root` 底下所有檔案，排除 `config.BUNDLE_IGNORE_DIRS`；
  * 以 JSON Lines 格式輸出，每行：

    ```json
    {
      "path": "pi4/core/config.py",
      "type": "text",
      "mode": "644",
      "content": "...."
    }
    ```

### 4.2 tools/restore_from_text.py（Pi4）

* CLI：

  ```bash
  python tools/restore_from_text.py --input smart_cane_bundle.txt --target /home/pi/smart_cane
  ```

* 功能：

  * 逐行解析 JSON；
  * 建立資料夾；
  * 寫回檔案（text / binary）；
  * 依 `mode` `chmod` 權限；
  * 若 target 存在，可要求 `--force` 才覆寫。

---

## 5. 測試規格（含 LLM 連線測試）

每個 `tests/*.py`：

* 透過 `pytest` 撰寫單元測試；
* 另外提供 **給 run_pipeline 用的函式**。

### 5.1 test_event_schema.py

* 單元測試範例：

  * 正常建立 Event；
  * severity 非法時要 raise；
  * JSON 序列化 / 反序列化。

* 對外介面：

  ```python
  def run_tests_unit() -> bool:
      """執行本檔單元測試，回傳 True/False。"""
  ```

### 5.2 test_vision_safety.py

* 單元測試：

  * 模擬 car approaching / person near；
  * 使用 monkeypatch mock 掉 `detect_objects()`。

* 對外介面：

  ```python
  def run_tests_unit() -> bool: ...
  ```

### 5.3 test_cane_safety.py

* 直接呼叫 `eval_distance(distance_m)`，確認事件正確。

* 對外介面：

  ```python
  def run_tests_unit() -> bool: ...
  ```

### 5.4 test_llm_clients.py（邏輯測試，用 mock）

* 不打真 API，只測：

  * `summarize_events()` 接收到 events 後是否組裝正確、錯誤行為如何處理；
  * `answer_question()` 回覆中不得包含「一定安全」等字詞。

* 對外介面：

  ```python
  def run_tests_unit() -> bool: ...
  ```

### 5.5 test_llm_connectivity.py（真實連線測試）

* 專門測：

  * Ollama 連線是否正常；
  * ChatGPT 連線是否正常。

* 對外介面：

  ```python
  def run_ollama_smoke_test() -> bool: ...
  def run_chatgpt_smoke_test() -> bool: ...
  ```

### 5.6 連續安全偵測腳本

* 檔案：`tests/continuous_safety_monitor.py`，使用現有的 `camera_capture` + `vision_safety` 並搭配 `VoiceOutput`，會持續讀取畫面、印出每個 `Event` 的 label/距離與 severity，並在距離小於 1 公尺且 severity ≥ mid 時播語音警告。
* 使用方式：

  ```bash
  python -m tests.continuous_safety_monitor
  ```

 直到按下 `Ctrl+C` 前都會維持 camera open、輸出與語音警示。

---

## 6. run_pipeline 主程式（選單 & 低耦合）

檔案：`run_pipeline.py`

### 6.1 選單項目

執行：

```bash
python run_pipeline.py
```

**語音喚醒 (Voice Launcher)** (Pending / 暫緩實作)：
*   目前僅保留機制設計，暫不實作。
*   (Original Plan: 程式啟動後，預設進入「語音待機模式」... 使用者說「啟動行人輔助」...)

預期選單：

```text
=== Smart Cane Pipeline Runner ===
平台: desktop / pi4 (來自 config.PLATFORM)

[1] 執行「全部單元測試」
[2] 測試 LINE API 訊息發送
[3] 只測 LLM 邏輯 (mock)
[4] 測試 Ollama 連線 (真實呼叫一次)
[5] 測試 ChatGPT 連線 (真實呼叫一次)
[6] 桌機模擬：Safety Layer (視覺 + 拐杖) 事件列印
[7] 實機全流程：Safety Layer（Understanding/Conversation 預設關閉，需改 env 才啟動）
[8] 匯出專案為文字 bundle
[9] 從文字 bundle 還原專案
[10] 以語音指令啟動行人輔助
[0] 離開

請輸入選項編號：
```

### 6.2 選項行為（重點）

* [1]：呼叫 `run_all_unit_tests()`，內部依序呼叫各 `run_tests_unit()`。
* [2]：`run_line_api_test()`，單獨測試 `pi4.voice.line_api_message.LineNotifier`，可輸入自訂訊息或使用預設文字，便於確認 LINE token 與網路連線是否可用。
* [3]：`run_tests_unit()`，執行 `tests.test_llm_clients`。
* [4]：`test_llm_connectivity.run_ollama_smoke_test()`。
* [5]：`test_llm_connectivity.run_chatgpt_smoke_test()`。
* [6]：`orchestrator.run_safety_simulation()`（只 print 事件，不播聲音）。
* [7]：在進入 `orchestrator.main_loop(duration=MAIN_LOOP_DURATION_SEC)` 之前會先呼叫 `tests.test_llm_connectivity.run_ollama_smoke_test()`，確認 Ollama 連線再開始實機 Safety Layer，全程等待 TTS 完成，Understanding/Conversation 需要設定為 true 才會插入。
* [8]：`tools.export_as_text.main()`。
* [9]：`tools.restore_from_text.main()`。
* [10]：`VoiceControlService` 的 `start()` / `stop()` 入口，支援透過語音指令操作行人輔助狀態，僅用於確認語音控制流程。

**限制：**

* `run_pipeline.py` 不應直接操作硬體或 HTTP，只透過這些高階函式。

---

## 7. IoT 物料資訊（BOM）

這一節就是你說「本來有物料那塊」——我重新整理成標準 BOM 表，放在這裡，之後可同步複製到 `docs/HW_BOM.md`。

### 7.1 主機端（Pi4）與視覺系統

| 類別      | 品名 / 型號                             | 說明與用途                          |
| ------- | ----------------------------------- | ------------------------------ |
| 主控制板    | **Raspberry Pi 4 Model B 4GB 全配套件** | 系統主機：跑 Linux、視覺、安全、LLM 整合      |
| 相機      | **USB 自動對焦攝影鏡頭模組 (IMX179, 8MP)**    | 視覺「眼睛」，接 Pi4 USB；支援自動對焦        |
| 推論加速    | **Intel Movidius NCS2**             | OpenVINO 硬體加速，跑行人 / 車輛偵測模型     |
| 儲存 / 系統 | microSD (32GB 以上)                   | 安裝 Raspberry Pi OS             |
| 網路      | Pi4 內建 Wi-Fi                        | 連線 ChatGPT API / 外部 Ollama 伺服器 |
| 音訊輸入    | USB 麥克風                             | 語音指令 / 喚醒詞偵測使用                 |
| 音訊輸出    | 3.5mm 有線耳機 or 骨傳導耳機                 | 播放警示與 LLM 回覆                   |
| 電源      | 官方或品質良好的 5V/3A USB-C 電源             | 提供 Pi4 穩定供電                    |

### 7.2 拐杖端（Pico + ToF）

| 類別       | 品名 / 型號                              | 說明與用途                          |
| -------- | ------------------------------------ | ------------------------------ |
| 控制板      | **Raspberry Pi Pico 2 WH (WiFi 版本)** | 拐杖端微控制器，負責 ToF 讀取與 UART 通訊     |
| ToF 感測器  | **GY-530 VL53L0X ToF 測距模組**          | 測距範圍約 3cm–2m，安裝在拐杖前端、朝下 10–20° |
| 電源 / UPS | **Pico UPS HAT / UPS 模組**（支援 18650）  | 為 Pico 端提供不斷電電源，內建充電管理與保護      |
| 電池       | **三星 18650 鋰電池**（有 BSMI 認證）          | 適配 UPS 模組，提供拐杖端電力              |
| 線材       | 杜邦線、USB 線、固定座等                       | 連接 Pico、ToF、電源模組，並固定在拐杖上       |

### 7.3 其他建議零件 / 工具

| 類別 | 品名 / 型號          | 說明                |
| -- | ---------------- | ----------------- |
| 支架 | 相機固定支架 / 3D 列印零件 | 將相機固定在合適高度與角度     |
| 外殼 | 防水 / 緩衝外殼        | 保護 Pi4 與 Pico 電路板 |
| 工具 | 烙鐵、熱縮套管、綁線帶      | 接線與整理線材使用         |

> 之後你也可以在 `HW_BOM.md` 多加「實際購買連結」、「單價」、「備註（如：有 BSMI）」。

---

## 8. 給 AI agent 的實作守則（總結）

1. **不得修改資料夾結構第一層**，所有新程式放入既有目錄。
2. 所有硬編常數，若屬「設定」，必須放到 `config.py`。
3. Safety Layer 內部程式不得呼叫任何 LLM API。
4. LLM 模組不得直接操作硬體（camera / UART / GPIO 等）。
5. `run_pipeline.py` 只負責選單與呼叫高層函式，不直接做重工作。
6. 撰寫 tests/ 時，盡量使用 mock / 假資料，不要直接依賴真實硬體或真實 API（除了 `test_llm_connectivity`）。

---

## 11. 部署與操作 (Deployment & Operation) (Pi4)

### 11.1 啟動方式 (Startup)

1.  **開發與測試 (Development)**：
    *   透過 SSH 連入 Pi4，執行 `python run_pipeline.py`，選擇 `[7]` 進行有時限的實機測試。
    *   執行 `python run_service.py` 進行**不限時**的背景執行測試。

2.  **正式運作 (Production)**：
    *   建立 `systemd` 服務檔 `/etc/systemd/system/smart-cane.service`，設定開機自動執行 `run_service.py`。
    *   **範例 `smart-cane.service`**：

    ```ini
    [Unit]
    Description=Smart Cane Safety Service
    After=network.target sound.target

    [Service]
    Type=simple
    User=pi
    WorkingDirectory=/home/pi/smart_cane
    ExecStart=/usr/bin/python3 /home/pi/smart_cane/run_service.py
    Restart=always
    RestartSec=5

    [Install]
    WantedBy=multi-user.target
    ```

    *   啟用指令：
        ```bash
        sudo systemctl enable smart-cane.service
        sudo systemctl start smart-cane.service
        ```

### 11.2 關閉與待機 (Shutdown & Idle)

1.  **待機模式 (Idle Mode)**：
    *   本系統採用 **Event-Triggered (事件觸發)** 架構。
    *   若 ToF 測得距離 > 1.2m（例如將拐杖提起或朝向無障礙物處），系統即自動進入低功耗待機狀態（不拍照、不辨識、不說話）。
    *   **不需要** 額外操作來暫停感測，只要遠離障礙物即可。

2.  **完全關閉 (Power Off)**：
    *   若要長時間不使用，請直接切換 UPS 電源開關或拔除電源。
    *   若需軟體關閉（例如維護時），可透過 SSH 執行：
        ```bash
        sudo systemctl stop smart-cane.service
        ```

---


## 10. 開發進度與待辦事項 (Progress & Todo)

> 每次開發結束前，請更新此區塊，記錄日期、完成項目與下一步，方便 Agent 接手。

### 2025-11-26
*   **進度**：
    *   [x] 確認系統架構轉移至 **Event-Triggered (USB Trigger)** 模式。
    *   [x] 完成 Pico 端韌體 (`pico_firmware/src/main.py`) 與驅動 (`vl53l0x.py`) 開發，支援真實感測器讀取。
    *   [x] 完成 PC 端測試工具 `read_pico_tof_v2.py`，驗證 USB JSON 資料傳輸正常。
    *   [x] 更新 System Spec，定義觸發流程與感測器距離建議 (1.2m)。
*   **待辦事項 (Todo)**：
### 5.1 test_event_schema.py

* 單元測試範例：

  * 正常建立 Event；
  * severity 非法時要 raise；
  * JSON 序列化 / 反序列化。

* 對外介面：

  ```python
  def run_tests_unit() -> bool:
      """執行本檔單元測試，回傳 True/False。"""
  ```

### 5.2 test_vision_safety.py

* 單元測試：

  * 模擬 car approaching / person near；
  * 使用 monkeypatch mock 掉 `detect_objects()`。

* 對外介面：

  ```python
  def run_tests_unit() -> bool: ...
  ```

### 5.3 test_cane_safety.py

* 直接呼叫 `eval_distance(distance_m)`，確認事件正確。

* 對外介面：

  ```python
  def run_tests_unit() -> bool: ...
  ```

### 5.4 test_llm_clients.py（邏輯測試，用 mock）

* 不打真 API，只測：

  * `summarize_events()` 接收到 events 後是否組裝正確、錯誤行為如何處理；
  * `answer_question()` 回覆中不得包含「一定安全」等字詞。

* 對外介面：

  ```python
  def run_tests_unit() -> bool: ...
  ```

### 5.5 test_llm_connectivity.py（真實連線測試）

* 專門測：

  * Ollama 連線是否正常；
  * ChatGPT 連線是否正常。

* 對外介面：

  ```python
  def run_ollama_smoke_test() -> bool: ...
  def run_chatgpt_smoke_test() -> bool: ...
  ```

### 5.6 連續安全偵測腳本

* 檔案：`tests/continuous_safety_monitor.py`，使用現有的 `camera_capture` + `vision_safety` 並搭配 `VoiceOutput`，會持續讀取畫面、印出每個 `Event` 的 label/距離與 severity，並在距離小於 1 公尺且 severity ≥ mid 時播語音警告。
* 使用方式：

  ```bash
  python -m tests.continuous_safety_monitor
  ```

 直到按下 `Ctrl+C` 前都會維持 camera open、輸出與語音警示。

---

## 6. run_pipeline 主程式（選單 & 低耦合）

檔案：`run_pipeline.py`

### 6.1 選單項目

執行：

```bash
python run_pipeline.py
```

**語音喚醒 (Voice Launcher)** (Pending / 暫緩實作)：
*   目前僅保留機制設計，暫不實作。
*   (Original Plan: 程式啟動後，預設進入「語音待機模式」... 使用者說「啟動行人輔助」...)

預期選單：

```text
=== Smart Cane Pipeline Runner ===
平台: desktop / pi4 (來自 config.PLATFORM)

[1] 執行「全部單元測試」
[2] 測試 LINE API 訊息發送
[3] 只測 LLM 邏輯 (mock)
[4] 測試 Ollama 連線 (真實呼叫一次)
[5] 測試 ChatGPT 連線 (真實呼叫一次)
[6] 桌機模擬：Safety Layer (視覺 + 拐杖) 事件列印
[7] 實機全流程：Safety Layer（Understanding/Conversation 預設關閉，需改 env 才啟動）
[8] 匯出專案為文字 bundle
[9] 從文字 bundle 還原專案
[10] 以語音指令啟動行人輔助
[0] 離開

請輸入選項編號：
```

### 6.2 選項行為（重點）

* [1]：呼叫 `run_all_unit_tests()`，內部依序呼叫各 `run_tests_unit()`。
* [2]：`run_line_api_test()`，單獨測試 `pi4.voice.line_api_message.LineNotifier`，可輸入自訂訊息或使用預設文字，便於確認 LINE token 與網路連線是否可用。
* [3]：`run_tests_unit()`，執行 `tests.test_llm_clients`。
* [4]：`test_llm_connectivity.run_ollama_smoke_test()`。
* [5]：`test_llm_connectivity.run_chatgpt_smoke_test()`。
* [6]：`orchestrator.run_safety_simulation()`（只 print 事件，不播聲音）。
* [7]：在進入 `orchestrator.main_loop(duration=MAIN_LOOP_DURATION_SEC)` 之前會先呼叫 `tests.test_llm_connectivity.run_ollama_smoke_test()`，確認 Ollama 連線再開始實機 Safety Layer，全程等待 TTS 完成，Understanding/Conversation 需要設定為 true 才會插入。
* [8]：`tools.export_as_text.main()`。
* [9]：`tools.restore_from_text.main()`。
* [10]：`VoiceControlService` 的 `start()` / `stop()` 入口，支援透過語音指令操作行人輔助狀態，僅用於確認語音控制流程。

**限制：**

* `run_pipeline.py` 不應直接操作硬體或 HTTP，只透過這些高階函式。

---

## 7. IoT 物料資訊（BOM）

這一節就是你說「本來有物料那塊」——我重新整理成標準 BOM 表，放在這裡，之後可同步複製到 `docs/HW_BOM.md`。

### 7.1 主機端（Pi4）與視覺系統

| 類別      | 品名 / 型號                             | 說明與用途                          |
| ------- | ----------------------------------- | ------------------------------ |
| 主控制板    | **Raspberry Pi 4 Model B 4GB 全配套件** | 系統主機：跑 Linux、視覺、安全、LLM 整合      |
| 相機      | **USB 自動對焦攝影鏡頭模組 (IMX179, 8MP)**    | 視覺「眼睛」，接 Pi4 USB；支援自動對焦        |
| 推論加速    | **Intel Movidius NCS2**             | OpenVINO 硬體加速，跑行人 / 車輛偵測模型     |
| 儲存 / 系統 | microSD (32GB 以上)                   | 安裝 Raspberry Pi OS             |
| 網路      | Pi4 內建 Wi-Fi                        | 連線 ChatGPT API / 外部 Ollama 伺服器 |
| 音訊輸入    | USB 麥克風                             | 語音指令 / 喚醒詞偵測使用                 |
| 音訊輸出    | 3.5mm 有線耳機 or 骨傳導耳機                 | 播放警示與 LLM 回覆                   |
| 電源      | 官方或品質良好的 5V/3A USB-C 電源             | 提供 Pi4 穩定供電                    |

### 7.2 拐杖端（Pico + ToF）

| 類別       | 品名 / 型號                              | 說明與用途                          |
| -------- | ------------------------------------ | ------------------------------ |
| 控制板      | **Raspberry Pi Pico 2 WH (WiFi 版本)** | 拐杖端微控制器，負責 ToF 讀取與 UART 通訊     |
| ToF 感測器  | **GY-530 VL53L0X ToF 測距模組**          | 測距範圍約 3cm–2m，安裝在拐杖前端、朝下 10–20° |
| 電源 / UPS | **Pico UPS HAT / UPS 模組**（支援 18650）  | 為 Pico 端提供不斷電電源，內建充電管理與保護      |
| 電池       | **三星 18650 鋰電池**（有 BSMI 認證）          | 適配 UPS 模組，提供拐杖端電力              |
| 線材       | 杜邦線、USB 線、固定座等                       | 連接 Pico、ToF、電源模組，並固定在拐杖上       |

### 7.3 其他建議零件 / 工具

| 類別 | 品名 / 型號          | 說明                |
| -- | ---------------- | ----------------- |
| 支架 | 相機固定支架 / 3D 列印零件 | 將相機固定在合適高度與角度     |
| 外殼 | 防水 / 緩衝外殼        | 保護 Pi4 與 Pico 電路板 |
| 工具 | 烙鐵、熱縮套管、綁線帶      | 接線與整理線材使用         |

> 之後你也可以在 `HW_BOM.md` 多加「實際購買連結」、「單價」、「備註（如：有 BSMI）」。

---

## 8. 給 AI agent 的實作守則（總結）

1. **不得修改資料夾結構第一層**，所有新程式放入既有目錄。
2. 所有硬編常數，若屬「設定」，必須放到 `config.py`。
3. Safety Layer 內部程式不得呼叫任何 LLM API。
4. LLM 模組不得直接操作硬體（camera / UART / GPIO 等）。
5. `run_pipeline.py` 只負責選單與呼叫高層函式，不直接做重工作。
6. 撰寫 tests/ 時，盡量使用 mock / 假資料，不要直接依賴真實硬體或真實 API（除了 `test_llm_connectivity`）。

---

## 10. 開發進度與待辦事項 (Progress & Todo)

> 每次開發結束前，請更新此區塊，記錄日期、完成項目與下一步，方便 Agent 接手。

### 2025-11-26
*   **進度**：
    *   [x] 確認系統架構轉移至 **Event-Triggered (USB Trigger)** 模式。
    *   [x] 完成 Pico 端韌體 (`pico_firmware/src/main.py`) 與驅動 (`vl53l0x.py`) 開發，支援真實感測器讀取。
    *   [x] 完成 PC 端測試工具 `read_pico_tof_v2.py`，驗證 USB JSON 資料傳輸正常。
    *   [x] 更新 System Spec，定義觸發流程與感測器距離建議 (1.2m)。
*   **待辦事項 (Todo)**：
    *   [x] **Pico Firmware**: 修改 `main.py` 加入觸發邏輯 (距離 < 1200mm 時送出 `{"event": "trigger"}`)。
    *   [x] **Pi4 Receiver**: 將 `read_pico_tof_v2.py` 的讀取邏輯整合進 `pi4/safety/cane_client/tof_receiver.py`。
    *   [x] **Orchestrator**: 修改 `orchestrator.py`，實作「收到 Trigger -> 拍照 -> 辨識 -> 語音」的流程。
    *   [x] **Config**: 在 `config.py` 新增 `TRIGGER_DISTANCE_MM` 與 `TRIGGER_COOLDOWN_SEC`。
    *   [ ] **Verification**: 執行模擬或實機測試，驗證觸發邏輯是否正確。
    *   [ ] **Voice Launcher** (Pending): 修改 `run_pipeline.py` 加入語音喚醒與選單語音控制功能（目前暫緩，專注於驗證 Trigger 機制）。
