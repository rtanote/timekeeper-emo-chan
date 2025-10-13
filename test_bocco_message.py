#!/usr/bin/env python3
"""
BOCCO emo メッセージ送信テスト
"""

import os
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

print("=" * 60)
print("BOCCO emo Message Test")
print("=" * 60)

# main.pyからBoccoEmoClientをインポート
from main import BoccoEmoClient

# クライアント初期化
print("\n[1/2] Initializing BOCCO emo client...")
emo = BoccoEmoClient(
    access_token=os.getenv('BOCCO_ACCESS_TOKEN'),
    refresh_token=os.getenv('BOCCO_REFRESH_TOKEN'),
    room_id=os.getenv('BOCCO_ROOM_ID'),
    account_type='personal'
)

# テストメッセージ送信
print("\n[2/2] Sending test message...")
test_messages = [
    "こんにちは！Timekeeper Emo-chanのテストです",
    "メッセージ送信が正常に動作しています！",
]

for i, msg in enumerate(test_messages, 1):
    print(f"\nMessage {i}: {msg}")
    response = emo.send_message(msg)
    if response:
        print(f"  Response: {response}")

    # 連続送信を避けるため少し待機
    import time
    time.sleep(2)

print("\n" + "=" * 60)
print("Test completed!")
print("Check your BOCCO emo device to see if messages were received.")
print("=" * 60)
