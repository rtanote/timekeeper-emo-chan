#!/usr/bin/env python3
"""
Serial Port Detection Tool
COMポートを検出してNFCリーダーを探します
"""

import serial.tools.list_ports

print("=" * 60)
print("Serial Port Detection Tool")
print("=" * 60)

print("\nSearching for serial ports...")

ports = list(serial.tools.list_ports.comports())

if not ports:
    print("\n[WARNING] No serial ports found")
    print("\nPossible reasons:")
    print("  1. NFC reader is not connected")
    print("  2. USB drivers are not installed")
    print("  3. Device is not recognized by Windows")
else:
    print(f"\n[OK] Found {len(ports)} serial port(s):\n")

    for i, port in enumerate(ports, 1):
        print(f"[Port {i}]")
        print(f"  Device: {port.device}")
        print(f"  Name: {port.name}")
        print(f"  Description: {port.description}")
        print(f"  Manufacturer: {port.manufacturer}")
        print(f"  VID:PID: {port.vid}:{port.pid}" if port.vid else "  VID:PID: N/A")
        print(f"  Serial Number: {port.serial_number}")

        # Sony RC-S380の検出
        if port.vid == 0x054c and port.pid == 0x06c3:
            print(f"\n  >>> THIS IS SONY RC-S380! <<<")
            print(f"\n  Update your .env file:")
            print(f"  NFC_READER_PATH={port.device}")

        print()

print("=" * 60)
print("\nNext steps:")
print("  1. If you see a Sony device, update .env with the device path")
print("  2. If no ports found, check Device Manager (devmgmt.msc)")
print("  3. Make sure RC-S380 drivers are installed")
print("  4. Try unplugging and replugging the USB cable")
print("=" * 60)
