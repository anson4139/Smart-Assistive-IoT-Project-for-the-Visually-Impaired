# Event Schema

本專案的 `Event` 資料結構由 `pi4/core/event_schema.py` 定義，包含以下欄位：

```python
@dataclass
class Event:
    event_id: str
    ts: datetime
    type: str
    source: str  # camera / tof / voice / system
    severity: Literal["low", "mid", "high", "critical"]
    distance_m: Optional[float] = None
    direction: Optional[str] = None
    extra: dict = field(default_factory=dict)
```

## 範例事件

```json
{
  "event_id": "evt-123",
  "ts": "2025-11-18T23:30:00+00:00",
  "type": "vision.person",
  "source": "camera",
  "severity": "mid",
  "distance_m": 1.2,
  "direction": "center"
}
```

## 常見事件類型

| 類型 | 說明 |
| ---- | ---- |
| `vision.person` | 相機偵測到人靠近，severity `high` 且 direction 顯示左右 |
| `vision.car` | 以車為標籤，距離小於 `config.CAR_APPROACHING_MIN_DISTANCE_M` 時 severity `critical` |
| `tof.drop` | ToF 距離落在 `DROP_*` 門檻內，表示可能前方落差 |
| `tof.step_down` | ToF 距離落在 `STEP_DOWN_MIN_HEIGHT_M` 與 `STEP_MIN_HEIGHT_M` 之間 |
| `tof.step` | 小於 `STEP_MIN_HEIGHT_M` 但又在上方安全視線內的步階 |

Severity 值必須從 `low`, `mid`, `high`, `critical` 中選擇，會在 `vision_safety` 與 `cane_safety` 中根據距離 / 行為自動判定。