
import sys
import os
from unittest.mock import MagicMock, patch

# Ensure we can import from the project root
sys.path.append(os.getcwd())

# Mock serial before importing anything that uses it
sys.modules["serial"] = MagicMock()
sys.modules["serial.tools"] = MagicMock()
sys.modules["serial.tools.list_ports"] = MagicMock()
sys.modules["cv2"] = MagicMock()
sys.modules["edge_tts"] = MagicMock()
sys.modules["pyttsx3"] = MagicMock()

# Mock LineNotifier at the module level BEFORE import
mock_line_module = MagicMock()
sys.modules["pi4.voice.line_api_message"] = mock_line_module

from pi4.core.event_schema import Event
from pi4.llm import understanding_ollama_client
# Now usage of orchestrator should be safe
from pi4.core.orchestrator import Orchestrator

def test_caregiver_rewrite():
    print(">>> Testing `rewrite_caregiver_text` logic...")
    original_voice = "前方有障礙物"
    events = [
        Event(event_id="test1", ts=123.0, type="vision.person", source="vision", severity="high", distance_m=2.5, object_label="person")
    ]
    
    # Mock Ollama availability to simulate offline/fallback first (faster check)
    with patch("pi4.llm.understanding_ollama_client._is_model_available", return_value=False):
        result = understanding_ollama_client.rewrite_caregiver_text(events, original_voice)
        print(f"[Offline Fallback] Result: {result}")
        assert "[系統自動回報]" in result
        
    print(">>> `rewrite_caregiver_text` logic passed (simulated fallback).")

def test_orchestrator_integration():
    print("\n>>> Testing `Orchestrator` LINE integration...")
    
    # Mock dependencies to avoid hardware errors
    with patch("pi4.core.orchestrator.tof_receiver") as mock_tof, \
         patch("pi4.core.orchestrator.camera_capture") as mock_cam, \
         patch("pi4.core.orchestrator.vision_safety") as mock_vision, \
         patch("pi4.core.orchestrator.understanding_ollama_client") as mock_llm, \
         patch("pi4.voice.line_api_message.LineNotifier") as MockLineNotifier:  # Mock the class
        
        # Setup Mocks
        mock_tof.read_latest_distance.return_value = 0.5  # Trigger distance
        import numpy as np
        # Return a white frame so it's not "blank"
        mock_cam.get_frame.return_value = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        # Simulate a HIGH severity event
        test_event = Event(event_id="test2", ts=123.0, type="vision.person", source="vision", severity="high", distance_m=0.5)
        mock_vision.process_frame.return_value = [test_event]
        
        mock_llm.rewrite_voice_text.return_value = ("小心", False)
        mock_llm.rewrite_caregiver_text.return_value = "Caregiver Alert: Person detected."
        
        # Initialize Orchestrator (which instantiates LineNotifier)
        orc = Orchestrator()
        
        # Verify LineNotifier was instantiated
        assert orc.line_notifier is not None
        print("[Check] LineNotifier instantiated.")
        
        # Run process once
        print("[Action] Triggering safety process simulation...")
        orc._process_safety()
        
        # Verify send was called
        orc.line_notifier.send.assert_called_with("Caregiver Alert: Person detected.")
        print(f"[Success] LineNotifier.send() was called with: 'Caregiver Alert: Person detected.'")

if __name__ == "__main__":
    try:
        test_caregiver_rewrite()
        test_orchestrator_integration()
        print("\n✅ Verification Successful: Logic is correctly wired up.")
    except AssertionError as e:
        print(f"\n❌ Verification Failed: {e}")
    except Exception as e:
        print(f"\n❌ Verification Error: {e}")
