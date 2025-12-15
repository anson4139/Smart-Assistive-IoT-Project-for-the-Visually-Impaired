
# Minimal VL53L0X MicroPython driver (I2C)
import time
_VL53_ADDR = 0x29

SYSRANGE_START       = 0x00
RESULT_RANGE_STATUS  = 0x14
SYSTEM_SEQUENCE_CONFIG = 0x01
SYSTEM_INTERRUPT_CLEAR = 0x0B
FINAL_RANGE_CONFIG_MIN_COUNT_RATE_RTN_LIMIT = 0x44
MSRC_CONFIG_CONTROL  = 0x60
SYSTEM_INTERMEASUREMENT_PERIOD = 0x04
GLOBAL_CONFIG_REF_EN_START_SELECT = 0xB6

def _i2c_write8(i2c, reg, val):
    i2c.writeto_mem(_VL53_ADDR, reg, bytes([val & 0xFF]))

def _i2c_write16(i2c, reg, val):
    i2c.writeto_mem(_VL53_ADDR, reg, bytes([(val >> 8) & 0xFF, val & 0xFF]))

def _i2c_read8(i2c, reg):
    return i2c.readfrom_mem(_VL53_ADDR, reg, 1)[0]

def _i2c_read16(i2c, reg):
    b = i2c.readfrom_mem(_VL53_ADDR, reg, 2)
    return (b[0] << 8) | b[1]

class VL53L0X:
    def __init__(self, i2c, address=_VL53_ADDR):
        self.i2c = i2c
        self.addr = address
        try:
            _ = _i2c_read8(self.i2c, 0xC0)
        except OSError:
            raise OSError("VL53L0X not found at 0x%02X" % self.addr)
        self._init_sensor()

    def _init_sensor(self):
        _i2c_write8(self.i2c, 0x88, 0x00)
        _i2c_write8(self.i2c, 0x80, 0x01)
        _i2c_write8(self.i2c, 0xFF, 0x01)
        _i2c_write8(self.i2c, 0x00, 0x00)
        stop_variable = _i2c_read8(self.i2c, 0x91)
        _i2c_write8(self.i2c, 0x00, 0x01)
        _i2c_write8(self.i2c, 0xFF, 0x00)
        _i2c_write8(self.i2c, 0x80, 0x00)

        _i2c_write8(self.i2c, MSRC_CONFIG_CONTROL, _i2c_read8(self.i2c, MSRC_CONFIG_CONTROL) | 0x12)
        _i2c_write16(self.i2c, FINAL_RANGE_CONFIG_MIN_COUNT_RATE_RTN_LIMIT, 0x00FF)

        _i2c_write8(self.i2c, 0xFF, 0x01)
        _i2c_write8(self.i2c, 0x4F, 0x00)   # DYNAMIC_SPAD_REF_EN_START_OFFSET
        _i2c_write8(self.i2c, 0x4E, 0x2C)   # DYNAMIC_SPAD_NUM_REQUESTED_REF_SPAD
        _i2c_write8(self.i2c, 0xFF, 0x00)
        _i2c_write8(self.i2c, GLOBAL_CONFIG_REF_EN_START_SELECT, 0xB4)

        _i2c_write8(self.i2c, SYSTEM_SEQUENCE_CONFIG, 0xFF)
        _i2c_write8(self.i2c, SYSTEM_INTERRUPT_CLEAR, 0x01)

        self._stop_variable = stop_variable
        self.stop()

    def start(self, period_ms=0):
        _i2c_write8(self.i2c, 0x80, 0x01)
        _i2c_write8(self.i2c, 0xFF, 0x01)
        _i2c_write8(self.i2c, 0x00, 0x00)
        _i2c_write8(self.i2c, 0x91, self._stop_variable)
        _i2c_write8(self.i2c, 0x00, 0x01)
        _i2c_write8(self.i2c, 0xFF, 0x00)
        _i2c_write8(self.i2c, 0x80, 0x00)
        if period_ms and period_ms > 0:
            _i2c_write16(self.i2c, SYSTEM_INTERMEASUREMENT_PERIOD, period_ms)
        _i2c_write8(self.i2c, SYSRANGE_START, 0x02)

    def stop(self):
        _i2c_write8(self.i2c, SYSRANGE_START, 0x00)

    def _read_blocking_range(self):
        for _ in range(100):
            if _i2c_read8(self.i2c, RESULT_RANGE_STATUS) & 0x01:
                break
            time.sleep_ms(10)
        dist = _i2c_read16(self.i2c, RESULT_RANGE_STATUS + 10)
        _i2c_write8(self.i2c, SYSTEM_INTERRUPT_CLEAR, 0x01)
        return dist

    def read(self):
        if _i2c_read8(self.i2c, SYSRANGE_START) == 0x00:
            _i2c_write8(self.i2c, SYSRANGE_START, 0x01)
        return self._read_blocking_range()
