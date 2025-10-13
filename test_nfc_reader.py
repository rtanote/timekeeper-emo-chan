#!/usr/bin/env python3
"""
NFC Reader Detection Test
"""

print("=" * 60)
print("NFC Reader Detection Test")
print("=" * 60)

try:
    import nfc
    print("\n[OK] nfcpy is installed")
except ImportError:
    print("\n[ERROR] nfcpy is not installed")
    print("Install it with: pip install nfcpy")
    exit(1)

# デバイスを検出
print("\n[1/2] Searching for NFC readers...")
print("Trying different device paths...\n")

# Windowsでよく使われるデバイスパス
device_paths = [
    'usb',  # 自動検出
    'usb:054c',  # Sony製品のベンダーID
    'usb:054c:06c3',  # RC-S380のプロダクトID
    'COM3',
    'COM4',
    'COM5',
]

found = False
for path in device_paths:
    try:
        print(f"  Trying: {path}... ", end='')
        clf = nfc.ContactlessFrontend(path)
        if clf:
            print("[OK] Found!")
            print(f"\n[SUCCESS] NFC Reader detected!")
            print(f"  Device: {clf}")
            print(f"  Path: {path}")

            # デバイス情報を表示
            print(f"\n  Device capabilities:")
            print(f"    {clf}")

            clf.close()
            found = True

            print("\n[2/2] Ready to read cards!")
            print("=" * 60)
            print("\nYou can now:")
            print("  1. Register cards: python register_card.py")
            print("  2. Run the app: python main.py")
            print("\nUpdate your .env file with:")
            print(f"  NFC_READER_PATH={path}")
            print("=" * 60)
            break
    except Exception as e:
        print(f"[FAILED] {str(e)[:50]}")
        continue

if not found:
    print("\n[ERROR] No NFC reader found")
    print("\nTroubleshooting:")
    print("  1. Check if the reader is connected via USB")
    print("  2. Check Device Manager for COM port number")
    print("  3. Try different paths: usb, COM3, COM4, etc.")
    print("  4. Make sure Sony RC-S380 drivers are installed")
