# main.py (robust, no flush) — VL53L0X JSON streamer with boot-time retry
from machine import Pin, I2C
import sys, ujson, utime

LED = None
try:
    LED = Pin("LED", Pin.OUT)
except Exception:
    pass

def led(on=None, toggle=False):
    if not LED:
        return
    if toggle:
        LED.toggle()
    elif on is None:
        return
    else:
        LED.value(1 if on else 0)

def _flush():
    # Some MicroPython streams don't implement .flush()
    try:
        sys.stdout.flush()
    except Exception:
        pass

def send(obj):
    try:
        sys.stdout.write(ujson.dumps(obj) + "\n")
        _flush()
    except Exception:
        # As a last resort, try a minimal print
        try:
            print(ujson.dumps(obj))
        except Exception:
            pass

# ---- Wake sensor on XSHUT if available ----
try:
    xshut = Pin(2, Pin.OUT, value=1)   # drive high
except Exception:
    xshut = None

# ---- I2C setup ----
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
utime.sleep_ms(150)  # small settle delay

def wait_for_sensor(timeout_ms=5000):
    t0 = utime.ticks_ms()
    while True:
        try:
            addrs = i2c.scan()
        except Exception:
            addrs = []
        if 0x29 in addrs:
            return True
        led(toggle=True)
        if utime.ticks_diff(utime.ticks_ms(), t0) > timeout_ms:
            return False
        utime.sleep_ms(100)

ready = wait_for_sensor(5000)
if not ready and xshut:
    xshut.value(0); utime.sleep_ms(80); xshut.value(1); utime.sleep_ms(200)
    ready = wait_for_sensor(5000)

if not ready:
    send({"src":"pico","event":"warn","msg":"VL53L0X not found at boot; will keep retrying"})
else:
    send({"src":"pico","event":"boot","msg":"VL53L0X detected"})

def make_sensor():
    from vl53l0x import VL53L0X
    return VL53L0X(i2c)

sensor = None
while sensor is None:
    try:
        sensor = make_sensor()
    except Exception as e:
        send({"src":"pico","event":"retry","detail":str(e)})
        utime.sleep_ms(300)

# Trigger settings
TRIGGER_DIST_MM = 1200
TRIGGER_COOLDOWN_MS = 2000
last_trigger_time = 0

while True:
    try:
        d = int(sensor.read())
        led(toggle=True)
        
        now = utime.ticks_ms()
        # Always send raw data for debugging/logging (optional, or reduce frequency)
        # For event-triggered system, we might still want a heartbeat or periodic update
        # But let's stick to the plan: send trigger when close.
        
        # Check trigger
        if d > 0 and d < TRIGGER_DIST_MM:
            if utime.ticks_diff(now, last_trigger_time) > TRIGGER_COOLDOWN_MS:
                send({"src":"pico", "event":"trigger", "d_mm": d, "ts": now})
                last_trigger_time = now
                # Blink fast to indicate trigger
                for _ in range(3):
                    led(toggle=True)
                    utime.sleep_ms(50)
        
        # Send heartbeat/status every 1s so Pi knows we are alive
        if utime.ticks_diff(now, last_trigger_time) > 5000: # If no trigger for 5s, send a keepalive
             # We can just send the distance as a regular update
             send({"src":"pico", "type":"tof", "d_mm": d, "ts": now})
        
        utime.sleep_ms(100) # 10Hz sampling
        
    except KeyboardInterrupt:
        send({"src":"pico","event":"stopped"})
        led(on=False)
        break
    except Exception as e:
        send({"src":"pico","event":"error","detail":str(e)})
        utime.sleep_ms(200)
        try:
            sensor = make_sensor()
        except Exception:
            pass
