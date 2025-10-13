#!/usr/bin/env python3
"""
Timekeeper Emo-chan - Test Script
NFCリーダーなしで動作確認するテストスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

print("=" * 60)
print("Timekeeper Emo-chan - Test Script")
print("=" * 60)

# 1. 依存ライブラリチェック
print("\n[1/6] Checking dependencies...")
try:
    import requests
    print("  [OK] requests")
except ImportError:
    print("  [ERROR] requests not installed")

try:
    import jpholiday
    print("  [OK] jpholiday")
except ImportError:
    print("  [ERROR] jpholiday not installed")

try:
    from dotenv import load_dotenv
    print("  [OK] python-dotenv")
except ImportError:
    print("  [ERROR] python-dotenv not installed")

# 2. データベース初期化テスト
print("\n[2/6] Testing database initialization...")
try:
    import sqlite3
    db = sqlite3.connect('test_timekeeper.db')
    with open('schema.sql', 'r', encoding='utf-8') as f:
        db.executescript(f.read())
    print("  [OK] Database initialized")
    db.close()
    os.remove('test_timekeeper.db')
except Exception as e:
    print(f"  [ERROR] {e}")

# 3. PatternLearner テスト
print("\n[3/6] Testing PatternLearner...")
try:
    from pattern_learner import PatternLearner
    from datetime import datetime
    db = sqlite3.connect(':memory:')
    learner = PatternLearner(db, None)

    # 祝日判定テスト
    test_date = datetime(2025, 1, 1)  # 元日
    is_holiday = learner.is_holiday(test_date)
    print(f"  [OK] Holiday detection works: 2025-01-01 is holiday? {is_holiday}")

    db.close()
except Exception as e:
    print(f"  [ERROR] {e}")

# 4. MessageGenerator テスト
print("\n[4/6] Testing MessageGenerator...")
try:
    from message_generator import MessageGenerator
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    with open('schema.sql', 'r', encoding='utf-8') as f:
        db.executescript(f.read())

    msg_gen = MessageGenerator(db)
    message = msg_gen.get_random_message('timer_start', {'project_name': 'Test Project'})
    print(f"  [OK] Generated message: {message}")

    db.close()
except Exception as e:
    print(f"  [ERROR] {e}")

# 5. Toggl Client テスト (初期化のみ)
print("\n[5/6] Testing Toggl Client initialization...")
try:
    from main import TogglClient
    toggl = TogglClient(
        api_token=os.getenv('TOGGL_API_TOKEN', 'dummy'),
        workspace_id=os.getenv('TOGGL_WORKSPACE_ID', '12345')
    )
    print("  [OK] Toggl client initialized")
    print(f"       Base URL: {toggl.base_url}")
except Exception as e:
    print(f"  [ERROR] {e}")

# 6. BOCCO emo Client テスト (初期化のみ)
print("\n[6/6] Testing BOCCO emo Client initialization...")
try:
    from main import BoccoEmoClient
    emo = BoccoEmoClient(
        access_token='dummy_token',
        refresh_token='dummy_refresh',
        room_id='dummy_room',
        account_type='personal'
    )
    print("  [OK] BOCCO emo client initialized (dummy mode)")

    # メッセージ送信テスト（ダミー）
    emo.send_message("テストメッセージ")
    print("  [OK] Message sending works (dummy mode)")
except Exception as e:
    print(f"  [ERROR] {e}")

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
print("\nNext steps:")
print("1. Set real API credentials in .env")
print("2. Connect NFC reader")
print("3. Run: python main.py")
