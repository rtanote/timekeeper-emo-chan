#!/usr/bin/env python3
"""
BOCCO emo Room ID取得ツール
アクセストークンを使ってルームIDとルーム情報を取得します
"""

import sys
import os
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

print("=" * 70)
print("BOCCO emo Room ID Retrieval Tool")
print("=" * 70)

# emo-platform-api-sdk のチェック
try:
    from emo_platform import Client, Tokens, BizBasicClient, BizAdvancedClient
    SDK_AVAILABLE = True
except ImportError:
    print("\n[ERROR] emo-platform-api-sdk is not installed")
    print("Install it with: pip install emo-platform-api-sdk")
    SDK_AVAILABLE = False
    sys.exit(1)

def get_rooms_personal():
    """個人アカウントのルーム一覧を取得"""
    access_token = os.getenv('BOCCO_ACCESS_TOKEN')
    refresh_token = os.getenv('BOCCO_REFRESH_TOKEN')

    if not access_token or not refresh_token:
        print("\n[ERROR] BOCCO tokens not found in .env file")
        print("Please set the following environment variables:")
        print("  BOCCO_ACCESS_TOKEN=your_access_token")
        print("  BOCCO_REFRESH_TOKEN=your_refresh_token")
        print("\nGet tokens from: https://platform-api.bocco.me/api-docs/")
        return None

    try:
        # クライアント初期化
        print("\n[1/2] Initializing BOCCO emo client...")
        client = Client(tokens=Tokens(
            access_token=access_token,
            refresh_token=refresh_token
        ))
        print("[OK] Client initialized")

        # ルーム一覧取得（部屋名も含む）
        print("\n[2/2] Fetching room list...")
        rooms_info = client.get_rooms_list()

        if not rooms_info or not rooms_info.rooms:
            print("[WARNING] No rooms found")
            return None

        print(f"[OK] Found {len(rooms_info.rooms)} room(s)")

        return rooms_info.rooms, client

    except Exception as e:
        print(f"[ERROR] Failed to get rooms: {e}")
        return None

def get_rooms_business(account_type='biz_basic'):
    """ビジネスアカウントのルーム一覧を取得"""
    api_key = os.getenv('BOCCO_API_KEY')

    if not api_key:
        print("\n[ERROR] BOCCO API key not found in .env file")
        print("Please set: BOCCO_API_KEY=your_api_key")
        return None

    try:
        # クライアント初期化
        print("\n[1/2] Initializing BOCCO emo business client...")
        if account_type == 'biz_basic':
            client = BizBasicClient()
        else:
            client = BizAdvancedClient()
        print("[OK] Client initialized")

        # ルーム一覧取得（部屋名も含む）
        print("\n[2/2] Fetching room list...")
        rooms_info = client.get_rooms_list(api_key)

        if not rooms_info or not rooms_info.rooms:
            print("[WARNING] No rooms found")
            return None

        print(f"[OK] Found {len(rooms_info.rooms)} room(s)")

        return rooms_info.rooms, client

    except Exception as e:
        print(f"[ERROR] Failed to get rooms: {e}")
        return None

def display_rooms(rooms, client, account_type='personal'):
    """ルーム情報を表示"""
    print("\n" + "=" * 70)
    print("Room Information")
    print("=" * 70)

    for i, room in enumerate(rooms, 1):
        print(f"\n[Room {i}]")
        print(f"  Room ID: {room.uuid}")
        print(f"  Room Name: {room.name}")
        print(f"  Room Type: {room.room_type}")

    print("\n" + "=" * 70)
    print("\nTo use a room in timekeeper-emo-chan:")
    print("Add the following to your .env file:")
    print(f"\n  BOCCO_ROOM_ID={rooms[0].uuid}")
    print(f"  # {rooms[0].name}")
    print("\n(If not specified, the first room will be used automatically)")
    print("=" * 70)

def main():
    """メインエントリーポイント"""
    # アカウントタイプの確認
    account_type = os.getenv('BOCCO_ACCOUNT_TYPE', 'personal')

    print(f"\nAccount Type: {account_type}")

    if account_type == 'personal':
        result = get_rooms_personal()
    elif account_type in ['biz_basic', 'biz_advanced']:
        result = get_rooms_business(account_type)
    else:
        print(f"[ERROR] Unknown account type: {account_type}")
        print("Valid types: personal, biz_basic, biz_advanced")
        sys.exit(1)

    if result:
        rooms, client = result
        display_rooms(rooms, client, account_type)
    else:
        print("\n[FAILED] Could not retrieve room information")
        sys.exit(1)

if __name__ == '__main__':
    main()
