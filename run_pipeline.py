from __future__ import annotations

import sys
from importlib import import_module

from pi4.core.config import MAIN_LOOP_DURATION_SEC, PLATFORM
from pi4.core.orchestrator import Orchestrator
from pi4.core.logger import get_logger

logger = get_logger("run_pipeline")

TEST_MODULES = [
    "tests.test_event_schema",
    "tests.test_vision_safety",
    "tests.test_cane_safety",
    "tests.test_llm_clients",
    "tests.test_voice_control",
]


def run_all_unit_tests() -> bool:
    results = []
    for module_path in TEST_MODULES:
        module = import_module(module_path)
        results.append(module.run_tests_unit())
    return all(results)


def run_single_test(module_name: str) -> bool:
    module = import_module(f"tests.{module_name}")
    return module.run_tests_unit()


def run_line_api_test() -> None:
    from pi4.core.config import LINE_TARGET_USER_ID
    from pi4.voice.line_api_message import LineNotifier

    notifier = LineNotifier()
    prompt = "請輸入要送出的 LINE 訊息（留空使用預設內容）："
    message = input(prompt).strip()
    if not message:
        message = "Smart Cane LINE API message test"
    user_prompt = "如果要指定特定 LINE user_id，請輸入；留空則使用 config 中的設定："
    user_input = input(user_prompt).strip()
    target_user = user_input or LINE_TARGET_USER_ID
    print(f"發送 LINE API 訊息：{message}")
    success = notifier.send(message, target_user_id=target_user)
    if success:
        print("LINE API 訊息已發送")
    else:
        print("LINE API 訊息發送失敗，請檢查 token 與網路設定。")


def main() -> None:
    # Initialize Core Services
    orchestrator = Orchestrator()
    
    # Voice Service is now initialized on demand to save resources
    from pi4.core.voice_service import VoiceControlService
    voice_service: VoiceControlService | None = None
    
    # print("正在啟動語音待機模式...")
    # try:
    #     voice_service.start_standby()
    #     print("語音待機模式已啟動。您可以隨時說出「啟動行人輔助」來開始。")
    # except Exception as e:
    #     print(f"語音服務啟動失敗 (可能是麥克風問題): {e}")
    #     print("將繼續以無語音模式執行。")

    while True:
        print("\n=== Smart Cane Pipeline Runner ===")
        print(f"平台: {PLATFORM}")
        
        if voice_service and voice_service.is_safety_running:
            print("狀態: [行人輔助執行中]")
        elif voice_service:
             print("狀態: [語音待機中]")
        else:
            print("狀態: [待機 (語音未啟動)]")
            
        print("[1] 執行全部單元測試")
        print("[2] 測試 LINE API 訊息發送")
        print("[3] 只測 LLM 邏輯")
        print("[4] 測試 Ollama 連線")
        print("[5] 測試 ChatGPT 連線")
        print("[6] 桌機模擬 Safety Layer")
        print("[7] 實機全流程 (手動啟動)")
        print("[8] 匯出專案為文字 bundle")
        print("[9] 從文字 bundle 還原專案")
        print("[10] 語音指令服務測試 (Debug)")
        print("[0] 離開")
        
        choice = input("請輸入選項編號：").strip()
        
        if choice == "0":
            if voice_service:
                voice_service.stop()
            break
        if choice == "1":
            run_all_unit_tests()
        elif choice == "2":
            run_line_api_test()
        elif choice == "3":
            run_single_test("test_llm_clients")
        elif choice == "4":
            from tests import test_llm_connectivity
            success = test_llm_connectivity.run_ollama_smoke_test()
            print("Ollama smoke test", "success" if success else "failed")
        elif choice == "5":
            from tests import test_llm_connectivity
            test_llm_connectivity.run_chatgpt_smoke_test()
        elif choice == "6":
            orchestrator.run_safety_simulation()
        elif choice == "7":
            # Ensure voice service is running for real flow
            if voice_service is None:
                print("正在啟動語音服務...")
                try:
                    voice_service = VoiceControlService(orchestrator=orchestrator)
                    voice_service.start_standby()
                except Exception as e:
                    print(f"語音服務啟動失敗: {e}")
                    voice_service = None

            if voice_service and voice_service.is_safety_running:
                print("行人輔助已經在背景執行中！")
                stop = input("是否停止背景執行並切換到前台顯示？(y/n): ").strip().lower()
                if stop == 'y':
                    voice_service.stop() # Stop background runner
                    # Re-init for foreground
                    voice_service = VoiceControlService(orchestrator=orchestrator) 
                    voice_service.start_standby()
                else:
                    continue
            
            # If still no voice service (failed to start), warn user
            if voice_service is None:
                print("警告: 語音服務未啟動，無法使用語音指令。")

            from tests import test_llm_connectivity
            print("先執行 Ollama smoke test 以驗證連線")
            success = test_llm_connectivity.run_ollama_smoke_test()
            print("Ollama smoke test", "success" if success else "failed")
            
            duration = MAIN_LOOP_DURATION_SEC
            print(f"本流程會運行約 {duration:.0f} 秒...")
            orchestrator.main_loop(duration_sec=duration)
            
        elif choice == "8":
            from tools import export_as_text
            export_as_text.main()
        elif choice == "9":
            from tools import restore_from_text
            restore_from_text.main()
        elif choice == "10":
            # Isolated Debug Mode
            print("啟動語音服務測試 (Debug Mode)...")
            
            # If a global service is running, we might want to use it or stop it?
            # To ensure clean state as requested, let's stop any existing one temporarily?
            # Or just use a separate instance if the global one is None.
            # If global one exists, it might be holding the mic.
            if voice_service:
                print("偵測到背景語音服務正在執行，將暫時停止以進行測試...")
                voice_service.stop()
                voice_service = None
            
            try:
                debug_vs = VoiceControlService(orchestrator=orchestrator)
                debug_vs.start_standby()
                debug_vs.say_greeting()
                
                input("按 Enter 停止語音服務並返回選單...")
                
                print("正在停止語音服務...")
                debug_vs.stop()
                print("語音服務已停止。")
            except Exception as e:
                print(f"語音測試發生錯誤: {e}")
                
        else:
            print("請輸入有效編號。")

if __name__ == "__main__":
    main()
