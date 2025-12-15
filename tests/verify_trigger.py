import sys
from unittest.mock import MagicMock, patch

# Mock pyttsx3 before importing modules that use it
sys.modules["pyttsx3"] = MagicMock()
sys.modules["cv2"] = MagicMock()
sys.modules["openvino"] = MagicMock()
sys.modules["openvino.runtime"] = MagicMock()
sys.modules["requests"] = MagicMock()

import unittest
from pi4.core.event_schema import Event
from pi4.core.orchestrator import Orchestrator
from pi4.safety.vision import camera_capture, vision_safety

class TestTriggerLogic(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_tof = patch('pi4.safety.cane_client.tof_receiver.read_latest_distance').start()
        self.mock_capture = patch('pi4.safety.vision.camera_capture.get_frame').start()
        # Mock detect_objects to return empty list or specific detections
        self.mock_detect = patch('pi4.safety.vision.ncs_inference.detect_objects').start()
        self.mock_detect.return_value = []
        
        # We don't need to mock process_frame if we mock detect_objects, 
        # but the test was mocking process_frame previously. 
        # Let's keep mocking process_frame as it's higher level and easier for this test.
        self.mock_process = patch('pi4.safety.vision.vision_safety.process_frame').start()
        
        self.mock_eval = patch('pi4.safety.cane_client.cane_safety.eval_distance').start()
        self.mock_speak = patch('pi4.voice.voice_output.VoiceOutput.speak').start()
        
        # Setup Orchestrator
        self.orchestrator = Orchestrator()
        # Disable background threads/services for unit test
        self.orchestrator.voice = MagicMock() 
        # Ensure is_busy returns False so we don't get stuck
        self.orchestrator.voice.is_busy.return_value = False 

    def tearDown(self):
        patch.stopall()

    def test_trigger_flow(self):
        import traceback
        try:
            print("\n=== Testing Trigger Flow ===")
            
            # 1. Simulate NO trigger
            self.mock_tof.return_value = None
            self.orchestrator.process_safety_once()
            
            # Assert: No camera capture
            self.mock_capture.assert_not_called()
            print("[Pass] No trigger -> No capture")

            # 2. Simulate Trigger (distance = 1.0m)
            self.mock_tof.return_value = 1.0
            # Mock a valid frame (not blank)
            import numpy as np
            self.mock_capture.return_value = np.ones((100, 100, 3), dtype=np.uint8) * 255
            # Mock vision events (e.g., person detected)
            from datetime import datetime
            fake_event = Event(
                event_id="test", ts=datetime.now(), type="person", source="camera", 
                severity="mid", distance_m=1.5, object_label="person"
            )
            self.mock_process.return_value = [fake_event]
            self.mock_eval.return_value = []
            
            self.orchestrator.process_safety_once()
            
            # Assert: Camera captured
            self.mock_capture.assert_called_once()
            print("[Pass] Trigger received -> Camera captured")
            
            # Assert: Voice output called (because severity=mid)
            # We need to check if orchestrator called voice.speak
            # Note: In the real code, orchestrator uses self.voice.speak
            self.orchestrator.voice.speak.assert_called()
            print("[Pass] Dangerous event -> Voice output triggered")
        except Exception:
            traceback.print_exc()
            raise

if __name__ == '__main__':
    # Manual run for debugging
    test = TestTriggerLogic()
    test.setUp()
    try:
        test.test_trigger_flow()
    except:
        import traceback
        traceback.print_exc()
    finally:
        test.tearDown()
