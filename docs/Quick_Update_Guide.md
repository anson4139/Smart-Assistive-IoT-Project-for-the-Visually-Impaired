# 快速更新指南：從 Windows 到 Pi

如果您想透過 WinSCP 直接將 Windows 上的程式碼更新到 Raspberry Pi，請遵循以下安全步驟。

## 1. 允許直接覆蓋的檔案
您可以直接全選並拖曳覆蓋大部分的程式碼與資料夾：
*   `pi4/`
*   `tools/`
*   `docs/`
*   `*.py` (如 `run_pipeline.py`)
*   `requirements.txt`

## 2. [危險] 絕對不要覆蓋的檔案
請在傳輸前，從選取範圍中**排除**以下檔案：

### ❌ `.env` (環境設定檔)
*   **原因**: Windows 的 `.env` 包含 `D:\...` 等路徑，覆蓋後會導致 Pi 找不到模型或檔案，且平台設定 (`SMART_CANE_PLATFORM`) 會錯誤。
*   **補救**: 若不慎覆蓋，請參閱 `.env.sample` 重新設定 Pi 的路徑 (/home/pi/...)。

### ❌ `venv` / `smartcane311` / `__pycache__`
*   **原因**: 這是 Windows 的執行環境，在 Pi (Linux) 上無法運作。
*   **補救**: 若不慎覆蓋，請刪除該資料夾，並在 Pi 上重新建立虛擬環境。

## 3. 更新後的執行步驟
更新完檔案後，請在 Pi 的終端機執行：

1.  **進入專案目錄**
    ```bash
    cd smart_cane
    ```

2.  **更新依賴 (若 requirements.txt 有變)**
    ```bash
    source smartcane311/bin/activate
    pip install -r requirements.txt
    ```

3.  **執行主程式**
    ```bash
    python run_pipeline.py
    ```
