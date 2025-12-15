# 部署與移植指南 (Deployment & Migration Guide)

本文件提供將 `smart_cane` 專案從 Windows 開發環境移植到 Raspberry Pi 4 的逐步操作說明。

---

## 1. 準備工作 (Preparation)

### 1.1 硬體需求
*   **Raspberry Pi 4 (建議 4GB/8GB RAM)**
*   microSD 卡 (32GB+, Class 10/U1)，安裝 **Raspberry Pi OS (64-bit)**
*   電源供應器 (5V 3A USB-C)
*   網路連線 (Wi-Fi 或 Ethernet)

### 1.2 系統套件依賴 (在 Pi4 上)
請打開 Pi4 的終端機 (Terminal) 並執行：

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git
sudo apt install -y libatlas-base-dev portaudio19-dev  # numpy 與 PyAudio 所需
```

---

## 2. 檔案傳輸方式 (File Transfer Methods)

您需要將 Windows 上的專案檔案移動到 Pi4。以下推薦三種方式：

### 方法 A：USB「打包」傳輸 (推薦無網路環境)
由於您在 Windows 上，此方法可將整個專案打包成一個文字檔，方便移動。

1.  **在 Windows 上 (打包)**：
    執行 `run_pipeline.py` 或匯出工具來產生 `smart_cane_bundle.txt`。
    ```powershell
    python run_pipeline.py
    # 選擇選項 [8] "匯出專案為文字 bundle"
    # 或直接執行：python tools/export_as_text.py --output smart_cane_bundle.txt
    ```
2.  **傳輸**：
41:     將 `smart_cane_bundle.txt` 複製到 USB 隨身碟，再複製到 Pi 上 (例如放在 `/home/a113453003/Desktop/python script/pi/smart_cane_bundle.txt`)。
42: 3.  **在 Pi4 上 (解包)**：
43:     *   您可以先將 `tools/restore_from_text.py` 放到 Pi 上。
44:     *   **在該目錄執行還原** (注意路徑空格需用引號)：
45:     ```bash
46:     cd "/home/a113453003/Desktop/python script/pi"
47:     # 假設 bundle 檔也放在這
48:     python3 restore_from_text.py --input smart_cane_bundle.txt --target smart_cane
49:     ```
50: 
51: ### 方法 B：SFTP / SCP (推薦有網路環境)
52: 
53: 1.  **工具**：使用 **WinSCP** (圖形介面) 或 `scp` (指令列)。
54: 2.  **WinSCP (推薦)**：
55:     *   主機名稱：`raspberrypi.local`
56:     *   使用者名稱：`a113453003` (或其他目前使用者)
57:     *   直接拖拉到 `/home/a113453003/Desktop/python script/pi/`。
58: 3.  **指令列**：
59:     ```powershell
60:     scp -r d:\Anson\smart_cane_2 "a113453003@raspberrypi.local:/home/a113453003/Desktop/python script/pi/smart_cane"
61:     ```
62: 
63: ### 方法 C：Git
64: 
65: 1.  **在 Pi4 上**：
66:     ```bash
67:     cd "/home/a113453003/Desktop/python script/pi"
68:     git clone https://github.com/your-repo/smart_cane.git
69:     ```
70: 
71: ---
72: 
73: ## 3. 安裝與設定 (Installation & Setup)
74: 
75: 當檔案已放置在 `/home/a113453003/Desktop/python script/pi/smart_cane` 後：
76: 
77: ### 3.1 建立 Python 虛擬環境
78: 
79: ```bash
80: cd "/home/a113453003/Desktop/python script/pi/smart_cane"
81: python3 -m venv .venv
82: source .venv/bin/activate
83: ```

### 3.2 安裝 Python 套件
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 設定 OpenVINO (若未使用系統套件)
*   確認 `openvino` 已安裝 (通常在 requirements.txt 中)。
*   若模型檔案不在專案中，請將其複製到正確路徑 (檢查 `models/` 資料夾)。

### 3.4 硬體權限設定
*   **UART (給 Pico ToF 用)**：在 `raspi-config` 中啟用 Serial Port。
    *   執行 `sudo raspi-config` -> Interface Options -> Serial Port -> Login Shell 選 **No**, Hardware 選 **Yes**。
    *   重新開機 (`sudo reboot`)。
*   **Camera**：若使用舊版相機堆疊，需在 `raspi-config` 中啟用 Camera (Bullseye/Bookworm 系統通常預設已支援)。

### 3.5 Ollama 設定 (Ollama Setup - Optional)
本專案的 Understanding Layer 依賴 Ollama。您有兩種選擇：

#### 選項 A：連接至 PC 上的 Ollama (推薦)
若 Pi4 效能不足，建議將 Ollama 跑在同一網段的 PC 上。

1.  **在 PC 上**：
    *   安裝 Ollama (Windows/Mac/Linux)。
    *   啟動 Ollama 服務並允許外部連線 (設定環境變數 `OLLAMA_HOST=0.0.0.0`)。
    *   確認已 pull 模型：`ollama pull gpt-oss:120b-cloud` (或您在 config 指定的模型)。

2.  **在 Pi4 上**：
    *   修改環境變數或 `.env`：
        ```bash
        # 若使用 ZeroTier，請填入 PC 的 ZeroTier IP
        export OLLAMA_BASE_URL="http://<PC_ZEROTIER_IP>:11434"
        ```
    *   **提示**：強烈建議使用 **ZeroTier** 建立虛擬區網，這樣 Pi4 與 PC 即使在不同 Wi-Fi 下也能穩定連線，且 IP 固定。

#### 選項 B：在 Pi4 上直接安裝 (不推薦，速度慢)
若必須在無網路環境獨立運作：

1.  **安裝 Ollama**：
    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```
2.  **啟動服務**：
    ```bash
    ollama serve
    ```
3.  **下載模型** (需極大空間與時間)：
    ```bash
    ollama pull gpt-oss:120b-cloud  # 或者是較小的模型如 llama3:8b
    ```
4.  **注意**：Pi4 只有 CPU，推論速度可能極慢 (數秒至數分鐘)。

---

## 4. 驗證 (Verification)

執行驗證步驟以確保硬體偵測正常。

1.  **啟用環境**：`source .venv/bin/activate`
2.  **執行 Pipeline**：
    ```bash
    python run_pipeline.py
    ```
3.  **選擇選項 [7]**：「實機全流程」。
    *   確認相機是否開啟。
    *   確認 ToF 觸發是否運作 (用手遮擋感測器)。
    *   確認聲音是否播放。

---

## 5. 部署與自動啟動 (Deployment)

若要讓程式開機即自動執行：

1.  **編輯服務檔**：
    (參考 `SYSTEM_SPEC.md` 第 11 節的 `systemd` 設定內容)。

2.  **安裝與啟動**：
    ```bash
    sudo nano /etc/systemd/system/smart-cane.service
    # 貼上 SYSTEM_SPEC [11.1] 的內容
    sudo systemctl enable smart-cane.service
    sudo systemctl start smart-cane.service
    ```

3.  **檢查狀態**：
    ```bash
    systemctl status smart-cane.service
    ```

---

## 6. 如何更新程式碼？

1.  **停止服務**：`sudo systemctl stop smart-cane.service`
2.  **更新檔案**：(透過 Git pull, SCP 覆蓋, 或 bundle 還原)
---

## 7. 除錯與維護 (Debugging & Maintenance)

如果在 Pi 上發現問題，**不需要** 每次都在 Windows 改好再覆蓋。您可以直接在 Pi 上進行除錯：

### 7.1 方法一：VS Code Remote - SSH (強烈推薦)
這是在 Windows 上開發 Pi 程式最快、最現代化的方式。

1.  **安裝外掛**：在 Windows 的 VS Code 安裝 **"Remote - SSH"** extension。
2.  **連線**：點擊 VS Code 左下角的綠色按鈕 `><` -> `Connect to Host...` -> 輸入 `pi@raspberrypi.local` (或 IP)。
3.  **開發**：連線成功後，VS Code 的檔案總管會直接顯示 Pi 裡的檔案。
    *   您可以直接編輯 `.py` 檔並存檔 (會即時存到 Pi)。
    *   可以直接在 VS Code 下方的 Terminal 執行 `python run_pipeline.py`。
    *   甚至可以使用 VS Code 的 Debugger (F5) 直接設中斷點除錯。

### 7.2 方法二：查看 Log 紀錄
如果不方便開 VS Code，最基本的方式是檢查 Log 檔：

*   **即時查看服務輸出**：
    ```bash
    journalctl -u smart-cane.service -f
    ```
    (按 `Ctrl+C` 離開)

*   **查看專案 Log 檔**：
    ```bash
    cat /home/pi/smart_cane/logs/smart_cane.log
    # 或即時監控
    tail -f /home/pi/smart_cane/logs/smart_cane.log
    ```

### 7.3 常見問題排查
*   **相機打不開**：檢查 `ls /dev/video*` 是否存在，或執行 `vcgencmd get_camera`。
*   **聲音出不來**：檢查 `aplay -l` 還有 `alsamixer` 音量設定。
*   **ToF 沒反應**：檢查 `/dev/ttyACM0` 或 `/dev/ttyUSB0` 是否存在，以及權限 (是否已加入 dialout 群組)。
