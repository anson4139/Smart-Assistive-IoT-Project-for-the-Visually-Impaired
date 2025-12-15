from __future__ import annotations

import math
import sys
import time

from pi4.core.config import PLATFORM
from pi4.core.logger import get_logger
from pi4.core.orchestrator import Orchestrator

# Import Voice Service if needed for future
# from pi4.core.voice_service import VoiceControlService

logger = get_logger("run_service")

def main() -> None:
    logger.info(f"Starting Smart Cane Service on {PLATFORM}...")
    
    # Initialize Orchestrator
    orchestrator = Orchestrator()
    
    # In the future, if we want Voice Launcher, we would initialization VoiceService here.
    # For now, we just run the safety loop indefinitely.
    
    logger.info("Entering infinite safety loop (Event-Triggered Mode).")
    try:
        # Check LLM connectivity once before starting (optional safe-check)
        # from tests import test_llm_connectivity
        # test_llm_connectivity.run_ollama_smoke_test()

        # Pass infinity for duration
        orchestrator.main_loop(duration_sec=float("inf"))
        
    except KeyboardInterrupt:
        logger.info("Service stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logger.error(f"Service crashed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
