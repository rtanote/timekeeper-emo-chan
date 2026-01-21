"""
スタンプ付きメッセージのAPIテスト
250文字のメッセージを送信して文字数制限を確認
"""

import os
from dotenv import load_dotenv

load_dotenv()

from emo_platform import Client, Tokens

# 250文字のテストメッセージ
TEST_MESSAGE = "あ" * 250

# スタンプUUID
STAMP_GANBARE = "f175953f-d29d-406a-bb19-43f3eb237c5e"

def main():
    access_token = os.getenv('BOCCO_ACCESS_TOKEN')
    refresh_token = os.getenv('BOCCO_REFRESH_TOKEN')
    room_id = os.getenv('BOCCO_ROOM_ID')

    print(f"Message length: {len(TEST_MESSAGE)} characters")
    print(f"Message: {TEST_MESSAGE[:50]}...")
    print()

    client = Client(
        tokens=Tokens(
            access_token=access_token,
            refresh_token=refresh_token
        ),
        use_cached_credentials=True
    )

    room_client = client.create_room_client(room_id)

    print("Sending stamp with 250 character message...")
    try:
        response = room_client.send_stamp(STAMP_GANBARE, TEST_MESSAGE)
        print(f"Success! Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
