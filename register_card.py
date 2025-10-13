#!/usr/bin/env python3
"""
NFC Card Registration Script
NFCカードをToggl Trackのプロジェクトに登録するツール
"""

import json
import os
import sys
from dotenv import load_dotenv

# nfcpy のインポート
try:
    import nfc
    NFC_AVAILABLE = True
except ImportError:
    print("Error: nfcpy is not installed")
    print("Install it with: pip install nfcpy")
    NFC_AVAILABLE = False
    sys.exit(1)


class CardRegistration:
    """NFCカード登録ツール"""

    def __init__(self, device_path: str = "/dev/ttyUSB0"):
        """
        Args:
            device_path: NFCリーダーのデバイスパス
        """
        self.device_path = device_path
        self.mapping_file = "card_mapping.json"
        self.cards = self.load_mapping()

    def load_mapping(self) -> dict:
        """
        既存のマッピングをロード

        Returns:
            カードマッピング辞書
        """
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load {self.mapping_file}: {e}")
                return {}
        return {}

    def save_mapping(self):
        """マッピングをファイルに保存"""
        try:
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.cards, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Mapping saved to {self.mapping_file}")
        except Exception as e:
            print(f"Error saving mapping: {e}")

    def read_card(self, clf) -> str:
        """
        NFCカードを読み取り

        Args:
            clf: NFC ContactlessFrontend

        Returns:
            カードID（16進数文字列）
        """
        print("\nPlease tap your NFC card on the reader...")

        tag = clf.connect(
            rdwr={
                'on-connect': lambda tag: False  # 接続したら即座に切断
            }
        )

        if tag:
            card_id = tag.identifier.hex()
            print(f"✓ Card detected: {card_id}")
            return card_id

        return None

    def register_card(self):
        """カード登録メインフロー"""
        print("=" * 60)
        print("NFC Card Registration Tool")
        print("=" * 60)

        # NFCリーダー初期化
        try:
            clf = nfc.ContactlessFrontend(self.device_path)
            print(f"✓ NFC Reader initialized: {clf}\n")
        except Exception as e:
            print(f"Error: Failed to initialize NFC reader: {e}")
            print(f"Device path: {self.device_path}")
            print("\nTips:")
            print("- Check if the NFC reader is connected")
            print("- Try: lsusb | grep Sony")
            print("- Check permissions: ls -l /dev/ttyUSB*")
            sys.exit(1)

        try:
            while True:
                # カードを読み取り
                card_id = self.read_card(clf)

                if not card_id:
                    print("No card detected, please try again")
                    continue

                # 既存登録のチェック
                if card_id in self.cards:
                    print(f"\n! This card is already registered:")
                    print(f"  Card ID: {card_id}")
                    print(f"  Project ID: {self.cards[card_id]}")

                    overwrite = input("\nOverwrite this registration? (y/n): ").strip().lower()
                    if overwrite != 'y':
                        print("Skipped.")
                        continue

                # プロジェクトIDの入力
                print(f"\nCard ID: {card_id}")
                project_id = input("Enter Toggl Project ID: ").strip()

                if not project_id:
                    print("Error: Project ID cannot be empty")
                    continue

                # プロジェクト名の入力（オプション）
                project_name = input("Enter Project Name (optional): ").strip()

                # 登録
                self.cards[card_id] = {
                    "project_id": project_id,
                    "project_name": project_name if project_name else "Unknown Project"
                }

                print(f"\n✓ Registered:")
                print(f"  Card ID: {card_id}")
                print(f"  Project ID: {project_id}")
                print(f"  Project Name: {project_name or '(not set)'}")

                # 保存
                self.save_mapping()

                # 続行確認
                another = input("\nRegister another card? (y/n): ").strip().lower()
                if another != 'y':
                    break

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        finally:
            clf.close()
            print("\nGoodbye!")

    def list_cards(self):
        """登録済みカード一覧を表示"""
        print("=" * 60)
        print("Registered Cards")
        print("=" * 60)

        if not self.cards:
            print("No cards registered yet.")
            return

        for i, (card_id, info) in enumerate(self.cards.items(), 1):
            if isinstance(info, dict):
                project_id = info.get('project_id', 'N/A')
                project_name = info.get('project_name', 'N/A')
            else:
                # 旧形式との互換性
                project_id = info
                project_name = 'N/A'

            print(f"\n{i}. Card ID: {card_id}")
            print(f"   Project ID: {project_id}")
            print(f"   Project Name: {project_name}")

        print(f"\nTotal: {len(self.cards)} card(s)")
        print("=" * 60)

    def delete_card(self):
        """カード登録を削除"""
        self.list_cards()

        if not self.cards:
            return

        card_id = input("\nEnter Card ID to delete: ").strip()

        if card_id in self.cards:
            info = self.cards[card_id]
            print(f"\nDeleting:")
            print(f"  Card ID: {card_id}")
            if isinstance(info, dict):
                print(f"  Project ID: {info.get('project_id')}")
                print(f"  Project Name: {info.get('project_name')}")

            confirm = input("\nAre you sure? (y/n): ").strip().lower()
            if confirm == 'y':
                del self.cards[card_id]
                self.save_mapping()
                print("✓ Deleted")
        else:
            print(f"Card ID '{card_id}' not found")


def main():
    """エントリーポイント"""
    load_dotenv()

    device_path = os.getenv('NFC_READER_PATH', '/dev/ttyUSB0')
    tool = CardRegistration(device_path)

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'list':
            tool.list_cards()
        elif command == 'delete':
            tool.delete_card()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python register_card.py [list|delete]")
    else:
        # デフォルト：カード登録
        tool.register_card()


if __name__ == '__main__':
    main()
