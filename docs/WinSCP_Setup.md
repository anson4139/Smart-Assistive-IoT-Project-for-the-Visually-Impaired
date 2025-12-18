# WinSCP 連線設定指南

要連線到您的 Raspberry Pi (Pi 4)，請在 WinSCP 視窗中填寫以下資訊：

## 1. 連線資訊
*   **檔案協定 (File protocol)**: `SFTP` (預設值)
*   **主機名稱 (Host name)**:
    *   **IP 位址**: 輸入 Pi 的 IP (例如 `192.168.1.xxx`)。
    *   **替代方案**: 嘗試輸入 `raspberrypi.local` 或 `raspberrypi`。
*   **連接埠 (Port number)**: `22` (預設值)
*   **使用者名稱 (User name)**:
    *   預設: `pi`
    *   **專案可能設定**: `a113453003` (參考自 `Desktop_to_PI.md` 中的路徑)
*   **密碼 (Password)**: 您設定的 Pi 密碼 (舊版預設為 `raspberry`)。

## 2. 如何查詢 IP 位址
如果輸入主機名稱無法連線，請嘗試以下方法找出 IP：
1.  **直接操作 Pi**: 接上螢幕與鍵盤，輸入 `hostname -I`。
2.  **查看路由器/熱點**: 檢查您的路由器或手機熱點連線裝置列表。
3.  **Ping 測試**: 在電腦 CMD 輸入 `ping raspberrypi.local`。
