# 從桌機移轉到 Raspberry Pi 4 的流程

本文件描述如何將 `smart_cane` 專案從 Windows/桌機環境完整部署到 Pi 4，包含程式、設定、模型與依賴的準備步驟。

## 1. 在 Pi4 上準備系統
1. `sudo apt update && sudo apt upgrade` 更新系統。
2. 安裝 Python 3.11+ 與 pip：
   ```bash
   sudo apt install python3 python3-venv python3-pip git
   ```
3. 若使用 OpenVINO + NCS2：依照官方指引安裝 OpenVINO runtime、MYRIAD plugin 與 `usbboot` 驅動；確保 `lsusb` 可見 NCS2。
   ```bash
   sudo apt install mpg123 -y
   pip3 install edge-tts
   ```
4. 安裝 Ollama（若在 Pi 上跑）：從 https://ollama.com/download 下載相容版本，並確保 `ollama` CLI 可用（`ollama list`）。
5. 在 Windows 下載模型：
   ```bash
   ollama pull gemma2:9b
   ```

## 2. 複製專案到 Pi
1. 可直接在 Pi 上 `git clone https://…/smart_cane.git` 或從 Windows 用 `tools/export_as_text.py` 產生 `smart_cane_bundle.txt` 再用 `tools/restore_from_text.py` 還原。
2. 若用 `restore_from_text.py`：先在 Windows 生成 bundle，再透過 `scp`/USB 拷到 Pi，最後在 Pi 執行：
   ```bash
   cd "/home/a113453003/Desktop/python script/pi"
   python tools/restore_from_text.py --input smart_cane_bundle.txt --target smart_cane
   ```
3. 進入目錄，建立 virtualenv：
   ```bash
   python3 -m venv smartcane311
   source smartcane311/bin/activate
   pip install -r requirements.txt
   ```

## 3. 調整設定（環境變數 / config）
1. 建立或複製 `.env`：可以用 `cp .env.sample .env`，再根據 Pi 硬體填值。
2. 必填參數範例：
   ```env
   SMART_CANE_PLATFORM=pi4
   SMART_CANE_USE_SIMULATED=false
   SMART_CANE_CAMERA_INDEX=0
   SMART_CANE_OPENVINO_MODEL_XML=/home/pi/models/person-detection-retail-0013.xml
   SMART_CANE_OPENVINO_MODEL_BIN=/home/pi/models/person-detection-retail-0013.bin
   SMART_CANE_OPENVINO_DEVICE=CPU
   SMART_CANE_TOF_SERIAL=/dev/ttyACM0
   SMART_CANE_TTS_ENGINE=local
   SMART_CANE_ALERT_COOLDOWN=1.0
   ```
3. 若需要直接修改 `pi4/core/config.py` 的 default 值，記得同步更新 `docs/SYSTEM_SPEC.md` 以及 `.env` 示例，避免 doc 與實際程式不一致。
4. 確認 `OLLAMA_BASE_URL` 指向 Pi 上的 service（預設 `http://localhost:11434`），且 `OLLAMA_ENABLED=true`、`OLLAMA_MODEL=gemma2:9b`。
5. 若要使用 Edge-TTS（推薦），請確認 `pi4/voice/voice_output.py` 已更新支援 `python3 -m edge_tts`。

## 4. 準備模型與 ToF 硬體
1. 把 `models/person-detection-retail-0013.{xml,bin}` 複製到 Pi 上的 `/home/pi/models/`，或其它路徑並同步 `.env`。可直接從 Windows 拷貝或用 `git lfs`。
2. ToF：將 Pico 2 WH 火線連至 pi 的 `/dev/ttyACM0`，在 `pi4/safety/cane_client/tof_receiver_pi.py` 檢查預設 port 是否正確；如有需要可透過 `ls /dev/tty*` 找到。
3. 確保 `pico_firmware` 已燒錄到拐杖，ToF 資料會透過 UART 每 0.1s 傳遞 JSON；Pi 端的 `tof_receiver` 會解析。

## 5. 執行與驗證
1. 啟動環境：
   ```bash
   source smartcane311/bin/activate
   python run_pipeline.py
   ```
2. 選項 4/5：分別測 Ollama 與 ChatGPT 連線；若出錯可調整 `OLLAMA_BASE_URL` 或網路。
3. 選項 7：會執行 Ollama smoke test，若通過就跑 Safety + Voice；確認 Console 出現 `[Ollama]` 語音，並在 `logs/` 與 `data/analyze/` 看到 `voice_distance_alert` 內容。
4. 若需持續跑，可考慮用 `tmux` 或建立 systemd service 來背景執行 `python run_pipeline.py`。

## 6. 後續維護
1. 每次變更設定、模型或流程後，請同步更新 `docs/SYSTEM_SPEC.md`、`docs/RulebyPY.md` 與 `README.md`，確保 Pi 與桌機說明一致。
2. 可在 Pi 上定期執行 `python tools/export_as_text.py` 打包，在 Windows 保留異機備份。若要把 Pi 改回桌機，只需反向調整 `.env`（如 `SMART_CANE_PLATFORM=desktop`）。

以上流程可協助你順利把 `smart_cane` 從桌機移轉到 Raspberry Pi 4，完成後再跑 `python run_pipeline.py` 選 7 驗證整合，確保 Ollama、OpenVINO、ToF 與 Voice 都正常運作。*** End Patch