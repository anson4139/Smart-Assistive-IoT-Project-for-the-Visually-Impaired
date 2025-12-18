# 效能優化與除錯更新 (V3)

針對您遇到的「延遲」與「LINE 發送失敗」問題，我已完成關鍵修正。

## 1. 效能優化 (解決 20秒延遲)
**原因**: 您的 Pi 正在使用 `gemma3:27b` 模型，這個模型 **太巨大了** (270億參數)，Pi 4 跑不動，導致每次回應都要等很久，且會卡住語音。
**修正**: 我修改了 `pi4\core\orchestrator.py`，將 LINE 通知與 AI 思考移到 **背景執行 (Background Thread)**。
**結果**: 語音應該會立刻播報，不會再被 LINE 卡住。

## 2. LINE 除錯與修正
**原因**: 您懷疑 Token 有問題，且 Log 顯示 429 (請求過多)。
**修正**: 
1. `orchestrator.py` 已包含非同步發送與冷卻機制。
2. 新增檢查工具 `verify_line_token.py`。

## 請執行以下步驟

### 第一步：更新檔案
請用 WinSCP 更新以下檔案：
*   `pi4\core\orchestrator.py` (非同步優化版)
*   `verify_line_token.py` (新增到專案根目錄)

### 第二步：更換小模型 (非常重要！)
Log 顯示您在跑 27b 模型，這絕對會讓 Pi 當機。請在 Pi 終端機執行：
```bash
ollama pull gemma2:2b
```
*(下載 2b 小模型，速度會快 10 倍以上)*

### 第三步：檢查 LINE Token
更新檔案後，若 LINE 還是沒反應，請執行診斷工具：
```bash
python verify_line_token.py
```
它會告訴您是 Token 錯了，還是額度用完了 (免費版每月只有 200 則)。
