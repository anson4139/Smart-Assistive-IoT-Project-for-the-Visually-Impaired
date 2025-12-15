import sys
import time

print("Python executable:", sys.executable)

print("Attempting to import speech_recognition...")
try:
    import speech_recognition as sr
    print("speech_recognition imported successfully.")
    print("Version:", sr.__version__)
except ImportError as e:
    print("Failed to import speech_recognition:", e)
    sr = None

print("\nAttempting to import pyttsx3...")
try:
    import pyttsx3
    print("pyttsx3 imported successfully.")
except ImportError as e:
    print("Failed to import pyttsx3:", e)
    pyttsx3 = None

if sr:
    print("\n=== Available Microphones ===")
    try:
        mics = sr.Microphone.list_microphone_names()
        for i, mic_name in enumerate(mics):
            print(f"[{i}] {mic_name}")
    except Exception as e:
        print(f"Error listing microphones: {e}")
    print("=============================\n")

if pyttsx3:
    print("Testing TTS...")
    try:
        engine = pyttsx3.init()
        print("Speaking first time...")
        engine.say("Testing voice output one.")
        engine.runAndWait()
        print("First speak done.")
        
        time.sleep(1)
        
        print("Speaking second time...")
        engine.say("Testing voice output two.")
        engine.runAndWait()
        print("Second speak done.")
    except Exception as e:
        print(f"TTS Error: {e}")
