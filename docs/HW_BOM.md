# Hardware Bill of Materials (BOM)

## Pi4 主機端

| 類別 | 品名 / 型號 | 說明 |
| ---- | ----------- | ---- |
| 主控制板 | Raspberry Pi 4 Model B 4GB | 執行 Safety + LLM + Voice 的主機 |
| 相機 | USB 自動對焦模組 (IMX179, 8MP) | 相容 Pi4 USB，提供視覺來源 |
| 推論加速 | Intel Movidius NCS2 | OpenVINO 加速物件偵測 |
| 儲存 | microSD 32GB / 64GB | 安裝 Raspberry Pi OS 與專案 |
| 麥克風 | USB 麥克風 | 聽取喚醒詞與語音指令 |
| 音訊輸出 | 3.5mm 耳機 / 骨傳導 | 播報 Safety / LLM 提示 |
| 電源 | 5V / 3A USB-C | 提供 Pi4 穩定電力 |

## 拐杖端 Pico & ToF

| 類別 | 品名 / 型號 | 說明 |
| ---- | ----------- | ---- |
| 控制器 | Raspberry Pi Pico 2 WH | Pico 負責 ToF 讀取與 UART 通訊 |
| ToF 感測 | GY-530 VL53L0X | 測距 3cm–2m，面向地面 10–20° |
| 電源 | Pico UPS HAT | 為 Pico 提供 UPS 與充電管理 |
| 電池 | Samsung 18650 | 搭配 UPS 提供穩定電力 |
| 線材 | 杜邦線 / USB 線 | 接線並固定在拐杖上 |
| 固定 / 外殼 | 相機支架、螺絲 | 固定相機與保護 Pi4 / Pico |

## 備註

- 相機與 ToF 感測器需依據安裝角度調整，避免遮蔽物。
- 建議在 Pi4 安裝散熱片與風扇，維持長時間運作穩定。
