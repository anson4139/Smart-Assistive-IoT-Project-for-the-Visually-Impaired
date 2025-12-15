# read_pico_tof_v2.py
# Robust reader for Pico JSON stream with helpful diagnostics.
# Usage (Windows):  python read_pico_tof_v2.py --port COM3
# Usage (Pi/Linux): python3 read_pico_tof_v2.py --port /dev/ttyACM0
#
# Extra flags:
#   --softreboot   Send Ctrl-D once on open (only works if Pico sits at REPL)
#   --interrupt    Send Ctrl-C once on open (to stop a stuck script)
#   --raw          Print raw bytes lines instead of parsing JSON
#   --verbose      Show waiting heartbeats and connection info

import argparse, json, sys, time
import serial
from serial.tools import list_ports

def list_available():
    ports = list_ports.comports()
    return [p.device for p in ports]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=None, help="Serial port, e.g. COM3 or /dev/ttyACM0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--softreboot", action="store_true", help="Send Ctrl-D once on open")
    ap.add_argument("--interrupt", action="store_true", help="Send Ctrl-C once on open")
    ap.add_argument("--raw", action="store_true", help="Print raw lines (no JSON parse)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not args.port:
        cand = list_available()
        if not cand:
            print("[error] no serial ports found"); return
        print("[info] detected ports:", cand)
        args.port = cand[0]
        print(f"[info] using {args.port}")

    # Open serial and gently "kick"
    ser = serial.Serial(args.port, args.baud, timeout=1)
    # Toggle DTR/RTS to ensure the stream starts on some hosts
    ser.dtr = True
    ser.rts = False
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    if args.interrupt:
        # Ctrl-C interrupts a running script
        ser.write(b"\x03")
        time.sleep(0.1)
    if args.softreboot:
        # Ctrl-D soft reboots ONLY if Pico is at REPL
        ser.write(b"\x04")
        time.sleep(0.2)

    print(f"[info] opened {args.port} @ {args.baud} (DTR={ser.dtr}, RTS={ser.rts})")
    last = time.time()
    try:
        while True:
            line = ser.readline()
            if not line:
                if args.verbose and time.time() - last > 1.0:
                    print("[waiting...]")
                    last = time.time()
                continue
            try:
                s = line.decode("utf-8", errors="ignore").strip()
            except Exception:
                s = str(line)
            if not s:
                continue
            if args.raw:
                print(s)
                continue
            # Try parse JSON; if fail, show raw
            try:
                obj = json.loads(s)
            except json.JSONDecodeError:
                print("[raw]", s)
                continue
            if obj.get("type") == "tof":
                print(f"distance: {obj.get('d_mm')} mm")
            else:
                print(obj)
    except KeyboardInterrupt:
        print("\n[info] bye")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
