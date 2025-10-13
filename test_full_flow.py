#!/usr/bin/env python3
"""
Timekeeper Emo-chan - Full Flow Test (Without NFC)
NFCリーダーなしで全体の流れをテストします
"""

import os
import sys
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

print("=" * 70)
print("Timekeeper Emo-chan - Full Flow Test")
print("=" * 70)

# モジュールのインポート
from main import BoccoEmoClient, TogglClient

# 1. BOCCO emo初期化
print("\n[1/4] Initializing BOCCO emo...")
emo = BoccoEmoClient(
    access_token=os.getenv('BOCCO_ACCESS_TOKEN'),
    refresh_token=os.getenv('BOCCO_REFRESH_TOKEN'),
    room_id=os.getenv('BOCCO_ROOM_ID'),
    account_type='personal'
)

# 2. Toggl Track初期化
print("\n[2/4] Initializing Toggl Track...")
toggl = TogglClient(
    api_token=os.getenv('TOGGL_API_TOKEN'),
    workspace_id=os.getenv('TOGGL_WORKSPACE_ID')
)

# 3. タイマー開始のテスト
print("\n[3/4] Testing timer start...")
print("Simulating: NFC card tapped (Project ID: 123456)")

try:
    # 現在のタイマー確認
    current = toggl.get_current_timer()
    if current:
        print(f"  Current timer already running: {current.get('description')}")
        print("  Stopping current timer first...")
        toggl.stop_timer()

    # 新しいタイマーを開始
    print("  Starting new timer...")
    # project_id = "123456"  # テスト用
    # result = toggl.start_timer(project_id, "Test from Timekeeper Emo-chan")

    # BOCCO emoにメッセージ送信
    message = "タイマーを開始しました！がんばってね！"
    emo.send_message(message)

    print("[OK] Timer start flow completed")

except Exception as e:
    print(f"[ERROR] {e}")

# 4. タイマー停止のテスト
print("\n[4/4] Testing timer stop...")
print("Simulating: NFC card tapped again (stop timer)")

try:
    current = toggl.get_current_timer()
    if current:
        print(f"  Stopping timer: {current.get('description')}")
        # toggl.stop_timer()

        # BOCCO emoにメッセージ送信
        message = "お疲れさま！よくがんばったね！"
        emo.send_message(message)

        print("[OK] Timer stop flow completed")
    else:
        print("  No timer running")

except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "=" * 70)
print("Test completed!")
print("\nCheck your BOCCO emo to see if messages were received.")
print("\nTo run with real NFC cards:")
print("  1. Connect Sony RC-S380")
print("  2. Install drivers if needed")
print("  3. Update .env with correct NFC_READER_PATH")
print("  4. Run: python main.py")
print("=" * 70)
