# Setup Guide - Timekeeper Emo-chan

This guide will walk you through setting up Timekeeper Emo-chan on your Raspberry Pi.

## Prerequisites

- Raspberry Pi 3 or later (Raspberry Pi 4 recommended)
- Sony RC-S380 NFC reader connected via USB
- BOCCO emo robot connected to Wi-Fi
- Active Toggl Track account with work history

## Step 1: System Setup

```bash
# Update your system
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y python3 python3-pip python3-venv
sudo apt-get install -y libusb-1.0-0-dev python3-dev

# Add your user to dialout group (for NFC reader access)
sudo usermod -a -G dialout $USER

# Log out and log back in for group changes to take effect
```

## Step 2: Clone Repository

```bash
cd ~
git clone <repository-url>
cd timekeeper-emo-chan
```

## Step 3: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 5: Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

Fill in your API credentials:

### Getting BOCCO emo Credentials
1. Open BOCCO emo app on your phone
2. Go to Settings > API
3. Generate API Key
4. Note your Room ID

### Getting Toggl Track Credentials
1. Log in to https://track.toggl.com/
2. Go to Profile Settings
3. Scroll down to find "API Token"
4. Copy your API token
5. Note your Workspace ID (visible in URL when on workspace page)

### NFC Reader Path
```bash
# Find your NFC reader device
lsusb | grep Sony

# Check device path (usually /dev/ttyUSB0)
ls -l /dev/ttyUSB*
```

## Step 6: Test Run

```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Run the application
python main.py
```

You should see:
```
==================================================
Timekeeper Emo-chan starting...
==================================================

[1/3] Learning work patterns from Toggl...
✓ Learned patterns from X entries

[2/3] Starting periodic scheduler...
✓ Scheduler started

[3/3] Starting NFC reader...
✓ Ready! Waiting for NFC card tap...

==================================================
```

## Step 7: Register NFC Cards

Create a card registration script:

```bash
nano register_card.py
```

Add basic card registration logic (TODO: implement full registration script).

For now, manually edit `main.py` to add card mappings:

```python
def _load_card_mapping(self) -> dict:
    return {
        'YOUR_CARD_ID_1': 'YOUR_PROJECT_ID_1',
        'YOUR_CARD_ID_2': 'YOUR_PROJECT_ID_2',
    }
```

## Step 8: Run as System Service (Optional)

Create a systemd service for auto-start:

```bash
sudo nano /etc/systemd/system/timekeeper-emo.service
```

Add the following content:

```ini
[Unit]
Description=Timekeeper Emo-chan
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/timekeeper-emo-chan
Environment="PATH=/home/pi/timekeeper-emo-chan/venv/bin"
ExecStart=/home/pi/timekeeper-emo-chan/venv/bin/python /home/pi/timekeeper-emo-chan/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable timekeeper-emo.service

# Start service
sudo systemctl start timekeeper-emo.service

# Check status
sudo systemctl status timekeeper-emo.service

# View logs
journalctl -u timekeeper-emo.service -f
```

## Step 9: Verify Pattern Learning

After running for a few days:

```bash
# Check database
sqlite3 timekeeper.db "SELECT * FROM project_patterns;"

# Check notification history
sqlite3 timekeeper.db "SELECT * FROM notification_history ORDER BY notified_at DESC LIMIT 10;"

# Check work history
sqlite3 timekeeper.db "SELECT COUNT(*) as count FROM work_history;"
```

## Troubleshooting

### NFC Reader Not Working
```bash
# Check USB connection
lsusb | grep Sony

# Check permissions
ls -l /dev/ttyUSB0

# If permission denied:
sudo chmod 666 /dev/ttyUSB0
# Or add user to dialout group (already done in Step 1)
```

### Python Import Errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### BOCCO emo Not Responding
- Check Wi-Fi connection
- Verify API key in `.env`
- Test with BOCCO emo mobile app

### Toggl API Errors
- Verify API token is correct
- Check workspace ID matches your account
- Ensure you have time entries in the past 14 days

## Next Steps

1. **Test NFC card taps** - Verify timer start/stop works
2. **Wait for pattern learning** - System needs a few days of data
3. **Monitor notifications** - Check if Emo-chan sends contextual messages
4. **Customize messages** - Edit `message_generator.py` to add your own messages

## Support

If you encounter issues:
1. Check the logs: `journalctl -u timekeeper-emo.service -f`
2. Review the main README.md troubleshooting section
3. Create an issue on GitHub

Enjoy your smart time tracking with Emo-chan! 🎉
