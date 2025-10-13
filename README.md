# Time Keeper Emo-chan

Timekeeper Emo-chan is a project that connects a Sony RC-S380 NFC reader, a Raspberry Pi, and a BOCCO emo robot to Toggl Track.
By simply tapping an NFC card, you can start or stop your work timer — and Emo expresses it through cheerful words and lively reactions.
It turns ordinary time tracking into a friendly, interactive experience.

## Features

### Core Features
- **NFC Card Integration**: Simply tap your NFC card to start/stop time tracking
- **Toggl Track Sync**: Automatically creates and manages time entries in Toggl Track
- **BOCCO emo Reactions**: Get cheerful feedback and animated reactions from your BOCCO emo robot
- **Raspberry Pi Based**: Runs on Raspberry Pi for low-power, always-on operation
- **Easy Setup**: Simple configuration with environment variables

### Smart Notifications (NEW!)
Emo-chan learns your work patterns and provides contextual encouragement:

- **Procrastination Detection**: If you haven't started work at your usual time, Emo will gently remind you
  - "そろそろ〇〇プロジェクトやったほうがよいんじゃない？"

- **Unusual Time Detection**: Working at different times than usual triggers supportive messages
  - Morning work: "あれ、今日は朝やるんだ！がんばって！"
  - Late night work: "今日は夜やるんだね！無理しないでね！"

- **Deep Night Praise**: Working late into the night gets you extra encouragement
  - "深夜までお疲れさま！無理しすぎないでね！"

- **Pattern Learning**: Analyzes your past 14 days of work history
  - Distinguishes between weekdays, weekends, and Japanese holidays (including Obon and New Year)
  - Learns typical work hours for each project
  - Automatically updates patterns daily

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd timekeeper-emo-chan
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your API credentials:
```bash
# BOCCO emo API Configuration
BOCCO_ACCOUNT_TYPE=personal  # 'personal', 'biz_basic', or 'biz_advanced'

# For personal accounts
BOCCO_ACCESS_TOKEN=your_access_token
BOCCO_REFRESH_TOKEN=your_refresh_token

# For business accounts (comment out if using personal)
# BOCCO_API_KEY=your_api_key

# Room ID (optional - will use first room if not specified)
BOCCO_ROOM_ID=your_room_id

# Toggl Track API
TOGGL_API_TOKEN=your_toggl_api_token
TOGGL_WORKSPACE_ID=your_workspace_id
TOGGL_PROJECT_ID=your_project_id  # Optional

# NFC Configuration
NFC_READER_PATH=/dev/ttyUSB0  # Adjust for your system

# Database (Optional)
DATABASE_PATH=timekeeper.db  # SQLite database file path
```

You can also copy `.env.example` as a template:
```bash
cp .env.example .env
# Then edit .env with your credentials
```

## Configuration

### Getting API Credentials

**BOCCO emo:**

This project uses the official [emo-platform-api-python](https://github.com/YUKAI/emo-platform-api-python) SDK.

**For Personal Accounts:**
1. Install the BOCCO emo mobile app and create an account
2. Get your access token and refresh token:
   - Access the [BOCCO emo Platform API documentation](https://platform-api.bocco.me/api-docs/#overview--%E7%AE%A1%E7%90%86%E7%94%BB%E9%9D%A2%E3%81%AB%E3%83%AD%E3%82%B0%E3%82%A4%E3%83%B3%E3%81%99%E3%82%8B) and log in with your BOCCO account to obtain these tokens

3. Get your Room ID:
   ```bash
   # Set tokens in .env first, then run:
   pip install emo-platform-api-sdk
   python get_bocco_rooms.py
   ```
   This will display all available rooms and their IDs.

4. Set the following environment variables:
   ```bash
   BOCCO_ACCOUNT_TYPE=personal
   BOCCO_ACCESS_TOKEN=your_access_token
   BOCCO_REFRESH_TOKEN=your_refresh_token
   BOCCO_ROOM_ID=your_room_id  # Optional - uses first room if not specified
   ```

**For Business Accounts:**
1. Register for a BOCCO emo Business account
2. Get your API key from the business portal
3. Get your Room ID:
   ```bash
   # Set API key in .env first, then run:
   pip install emo-platform-api-sdk
   python get_bocco_rooms.py
   ```
4. Set the following environment variables:
   ```bash
   BOCCO_ACCOUNT_TYPE=biz_basic  # or biz_advanced
   BOCCO_API_KEY=your_api_key
   BOCCO_ROOM_ID=your_room_id
   ```

**Toggl Track:**
1. Log in to [Toggl Track](https://track.toggl.com/)
2. Go to Profile Settings
3. Find your API token at the bottom of the page
4. Note your Workspace ID from the URL or API

### NFC Card Setup

Register your NFC cards by running the card registration script:
```bash
python register_card.py
```
This will prompt you to tap cards and assign them to specific Toggl Track projects or tasks.

## Usage

### Starting the Application

Run the main script on your Raspberry Pi:
```bash
python main.py
```

For running as a background service:
```bash
# Create a systemd service
sudo nano /etc/systemd/system/timekeeper-emo.service

# Enable and start the service
sudo systemctl enable timekeeper-emo.service
sudo systemctl start timekeeper-emo.service
```

### How It Works

1. **Starting a Timer**: Tap your registered NFC card on the RC-S380 reader
   - The system creates a new time entry in Toggl Track
   - BOCCO emo responds with an encouraging message like "Let's get started!"

2. **Stopping a Timer**: Tap the same card again
   - The system stops the current time entry
   - BOCCO emo congratulates you with a message like "Great work!"

3. **Multiple Projects**: Use different NFC cards for different projects
   - Each card can be associated with a specific Toggl project
   - Switch between projects seamlessly by tapping different cards

### Example Workflow

```
[Tap Card A] → "Starting work on Project Alpha!"
... work for 2 hours ...
[Tap Card A] → "You worked for 2 hours! Well done!"

[Tap Card B] → "Starting work on Project Beta!"
... work for 1 hour ...
[Tap Card B] → "You worked for 1 hour! Take a break!"
```

### Smart Notification Examples

After the system learns your work patterns (typically takes a few days), Emo-chan will provide contextual notifications:

**Scenario 1: Procrastination Reminder**
```
You usually work on "Project Alpha" at 2:00 PM on weekdays
Current time: 2:30 PM, no timer running
→ Emo: "そろそろProject Alphaやったほうがよいんじゃない？"
```

**Scenario 2: Early Morning Work**
```
You usually work on "Project Beta" at 2:00-5:00 PM
You start working at 8:00 AM (30+ minutes earlier than usual for morning projects)
→ Emo: "あれ、今日は朝やるんだ！がんばって！"
```

**Scenario 3: Late Night Work**
```
You usually work on "Project Gamma" at 2:00-5:00 PM
You start working at 10:00 PM (2+ hours later than usual)
→ Emo: "今日は夜やるんだね！無理しないでね！"
```

**Scenario 4: Deep Night Praise**
```
Working past 10:00 PM
→ Emo: "深夜までお疲れさま！無理しすぎないでね！"
```

**Note**:
- Notifications are sent at most once per hour to avoid being intrusive
- The system automatically detects vacations (no work for 3+ days) and pauses notifications
- Weekend and holiday patterns are learned separately from weekday patterns

## Requirements

### Hardware/Service
- **Sony RC-S380** - NFC reader/writer (FeliCa, MIFARE compatible)
- **Raspberry Pi** - Board computer (Raspberry Pi 3 or later recommended)
  - Tested on Raspberry Pi 4 Model B
  - Requires USB port for NFC reader
- **BOCCO emo** - Communication robot by YUKAI Engineering
  - Requires Wi-Fi connection
- **Toggl Track** - Time management web service
  - Free or paid account supported

### Software
- **Python 3.8+** (Python 3.10 or later recommended)
- **nfcpy** - Python library for NFC communication
- **python-dotenv** - Environment variable management
- **requests** - HTTP library for API calls
- **jpholiday** - Japanese holiday detection (for smart notifications)
- **python-dateutil** - Date/time utilities
- **SQLite3** - Built-in with Python (for pattern learning database)
- **Additional dependencies** - See [requirements.txt](requirements.txt)

### Accounts
- **BOCCO emo account** - Register at [BOCCO emo website](https://emo.bocco.me/)
- **Toggl Track account** - Sign up at [Toggl Track](https://track.toggl.com/)

### Operating System
- **Raspberry Pi OS** (formerly Raspbian) - Recommended
- **Ubuntu for Raspberry Pi** - Also supported
- Any Linux distribution with Python 3.8+ support

## Troubleshooting

### NFC Reader Not Detected
```bash
# Check if the reader is connected
lsusb | grep Sony

# Check permissions
sudo chmod 666 /dev/ttyUSB0
```

### BOCCO emo Not Responding
- Verify your API key and Room ID in the `.env` file
- Check that BOCCO emo is connected to Wi-Fi
- Test the connection with the BOCCO emo mobile app

### Toggl Track API Errors
- Ensure your API token is correct
- Check that the Workspace ID and Project ID exist
- Verify you have permission to create time entries in the workspace

### Dependencies Installation Issues
```bash
# If nfcpy installation fails, install system dependencies first
sudo apt-get update
sudo apt-get install python3-dev libusb-1.0-0-dev

# Then retry
pip install -r requirements.txt
```

### Permission Denied for NFC Reader
Add your user to the dialout group:
```bash
sudo usermod -a -G dialout $USER
# Log out and log back in for changes to take effect
```

### Smart Notifications Not Working
```bash
# Check if pattern learning completed successfully
# Look for "Learning work patterns..." in the logs

# Verify database exists and has data
ls -lh timekeeper.db

# Check notification history
sqlite3 timekeeper.db "SELECT * FROM notification_history ORDER BY notified_at DESC LIMIT 10;"

# Manually trigger pattern update
# Add this to your Python shell:
# from pattern_learner import PatternLearner
# learner.force_pattern_update()
```

**Common issues:**
- **Not enough data**: Pattern learning requires at least 3 work sessions per project over 14 days
- **No Toggl history**: Ensure you have time entries in Toggl Track for the past 14 days
- **Vacation detected**: If no work for 3+ days, notifications are paused automatically

## Architecture

### Project Structure

```
timekeeper-emo-chan/
├── main.py                  # Main application entry point
├── pattern_learner.py       # Work pattern learning module
├── message_generator.py     # Context-aware message generation
├── emo_scheduler.py         # Periodic check and notification scheduler
├── register_card.py         # NFC card registration tool
├── get_bocco_rooms.py       # BOCCO emo room ID retrieval tool
├── test_app.py             # Test script for components
├── schema.sql              # Database schema
├── requirements.txt        # Python dependencies
├── timekeeper-emo.service  # systemd service file
├── .env                    # Configuration (not in repo)
├── card_mapping.json       # Card-to-project mapping (created by register_card.py)
└── timekeeper.db           # SQLite database (created at runtime)
```

### How It Works

1. **Main Thread**: NFC card reader loop (blocking, waits for card taps)
2. **Background Thread 1**: Periodic checker (runs every 1 hour)
   - Checks if you're working when you should be
   - Detects unusual work times
   - Sends contextual notifications via BOCCO emo
3. **Background Thread 2**: Pattern updater (runs every 24 hours)
   - Fetches latest work history from Toggl Track
   - Re-learns work patterns
   - Updates SQLite database

### Database Schema

The application uses SQLite to store:
- **work_history**: Cached time entries from Toggl (14 days)
- **project_patterns**: Learned work patterns for each project
- **message_templates**: Message variations for different contexts
- **notification_history**: Sent notifications to avoid duplicates

See [schema.sql](schema.sql) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests (if available)
pytest
```

## License

MIT License