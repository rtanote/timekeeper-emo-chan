#!/usr/bin/env python3
"""
USB Device Lister
接続されているUSBデバイスを一覧表示します
"""

print("=" * 70)
print("USB Device Lister")
print("=" * 70)

try:
    import usb.core
    import usb.util

    # すべてのUSBデバイスを検索
    devices = usb.core.find(find_all=True)

    device_list = list(devices)

    if not device_list:
        print("\n[WARNING] No USB devices found")
        print("\nThis might mean:")
        print("  1. No USB devices connected")
        print("  2. libusb backend not installed")
        print("  3. Permission issues")
    else:
        print(f"\n[OK] Found {len(device_list)} USB device(s):\n")

        for i, dev in enumerate(device_list, 1):
            print(f"[Device {i}]")
            print(f"  Vendor ID: 0x{dev.idVendor:04x}")
            print(f"  Product ID: 0x{dev.idProduct:04x}")

            # Sony RC-S380の検出 (VID: 0x054c, PID: 0x06c3)
            if dev.idVendor == 0x054c and dev.idProduct == 0x06c3:
                print(f"  >>> THIS IS SONY RC-S380! <<<")

            try:
                print(f"  Manufacturer: {usb.util.get_string(dev, dev.iManufacturer)}")
            except:
                print(f"  Manufacturer: (unable to read)")

            try:
                print(f"  Product: {usb.util.get_string(dev, dev.iProduct)}")
            except:
                print(f"  Product: (unable to read)")

            print(f"  Bus: {dev.bus}")
            print(f"  Address: {dev.address}")
            print()

except ImportError:
    print("\n[ERROR] pyusb is not installed")
    print("Install it with: pip install pyusb")
    print("\nNote: Windows also requires a libusb backend:")
    print("  Option 1: Install libusb-win32")
    print("  Option 2: Install WinUSB driver using Zadig")
    print("  See: https://github.com/libusb/libusb/wiki/Windows")

except Exception as e:
    print(f"\n[ERROR] {e}")
    print("\nPossible solutions:")
    print("  1. Install libusb-win32 or WinUSB driver")
    print("  2. Use Zadig tool to install WinUSB driver for RC-S380")
    print("  3. Check Windows Device Manager for the device")

print("=" * 70)
