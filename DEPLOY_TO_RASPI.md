# Raspberry Piへのデプロイガイド

このガイドでは、Windows環境で開発したTimekeeper Emo-chanをRaspberry Piに転送して実行する手順を説明します。

## 前提条件

- Raspberry Pi 3以降（Raspberry Pi 4推奨）
- Raspberry Pi OSがインストール済み
- SSH接続が有効
- インターネット接続
- Sony RC-S380 NFCリーダー

## 1. ファイルの転送

### 方法A: Gitを使用（推奨）

```bash
# Raspberry Pi上で
cd ~
git clone <your-repository-url>
cd timekeeper-emo-chan
```

### 方法B: SCPで直接転送

```bash
# Windows側から実行（PowerShellまたはGit Bash）
scp -r d:/dev/timekeeper-emo-chan pi@<raspberry-pi-ip>:~/
```

### 方法C: 個別ファイル転送

必要最小限のファイル：
```bash
# 必須ファイル
main.py
pattern_learner.py
message_generator.py
emo_scheduler.py
schema.sql
requirements.txt
.env
card_mapping.json (カード登録後)

# ユーティリティ
register_card.py
get_bocco_rooms.py
test_app.py

# ドキュメント
README.md
SETUP.md

# systemd サービス
timekeeper-emo.service
```

## 2. Raspberry Piでのセットアップ

### システムアップデート

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 必要なシステムパッケージのインストール

```bash
# Python開発ツール
sudo apt-get install -y python3 python3-pip python3-venv

# NFC関連
sudo apt-get install -y libusb-1.0-0-dev python3-dev

# その他
sudo apt-get install -y git
```

### 仮想環境の作成

```bash
cd ~/timekeeper-emo-chan
python3 -m venv venv
source venv/bin/activate
```

### Python依存パッケージのインストール

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. 環境設定

### .envファイルの作成

```bash
cp .env.example .env
nano .env
```

以下の情報を設定：
```bash
# BOCCO emo
BOCCO_ACCOUNT_TYPE=personal
BOCCO_ACCESS_TOKEN=your_access_token
BOCCO_REFRESH_TOKEN=your_refresh_token
BOCCO_ROOM_ID=your_room_id

# Toggl Track
TOGGL_API_TOKEN=your_api_token
TOGGL_WORKSPACE_ID=your_workspace_id

# NFC Reader (Raspberry Piでは通常 usb)
NFC_READER_PATH=usb

# Database
DATABASE_PATH=timekeeper.db
```

### パーミッション設定

```bash
# ユーザーをdialoutグループに追加（NFCリーダーアクセス用）
sudo usermod -a -G dialout $USER

# 再ログインして反映
# または再起動
sudo reboot
```

## 4. NFCリーダーの確認

### リーダーの検出

```bash
# USB接続確認
lsusb | grep Sony

# 期待される出力例：
# Bus 001 Device 004: ID 054c:06c3 Sony Corp. RC-S380

# nfcpyでの確認
python3 -c "import nfc; print(nfc.ContactlessFrontend('usb'))"
```

### テストスクリプト実行

```bash
source venv/bin/activate
python test_app.py
```

## 5. カードの登録

```bash
source venv/bin/activate
python register_card.py
```

カードをタップして、Toggl TrackのプロジェクトIDと紐付けます。

## 6. アプリケーションの起動

### 手動起動（テスト用）

```bash
source venv/bin/activate
python main.py
```

Ctrl+Cで停止できます。

### systemdサービスとして起動（本番用）

```bash
# サービスファイルのコピー
sudo cp timekeeper-emo.service /etc/systemd/system/

# サービスファイルの編集（必要に応じてパスを調整）
sudo nano /etc/systemd/system/timekeeper-emo.service

# サービスの有効化と起動
sudo systemctl daemon-reload
sudo systemctl enable timekeeper-emo.service
sudo systemctl start timekeeper-emo.service

# ステータス確認
sudo systemctl status timekeeper-emo.service

# ログ確認
journalctl -u timekeeper-emo.service -f
```

## 7. トラブルシューティング

### NFCリーダーが認識されない

```bash
# USB接続確認
lsusb | grep Sony

# パーミッション確認
groups
# dialout グループが含まれているか確認

# 再ログインまたは再起動
sudo reboot
```

### 依存パッケージのエラー

```bash
# システムパッケージの再インストール
sudo apt-get install --reinstall libusb-1.0-0-dev python3-dev

# Python パッケージの再インストール
pip install -r requirements.txt --force-reinstall
```

### BOCCO emo接続エラー

```bash
# Room ID確認
python get_bocco_rooms.py

# トークンの再取得
# https://platform-api.bocco.me/api-docs/ でログイン
```

### Toggl Track API エラー

```bash
# APIトークン確認
# https://track.toggl.com/profile

# Workspace ID確認
# Toggl Trackのブラウザ版でURLから確認
```

## 8. 起動確認

1. NFCカードをタップ
2. Toggl Trackでタイマーが開始されることを確認
3. BOCCO emoからメッセージが聞こえることを確認
4. もう一度タップしてタイマー停止

## ファイル構成（Raspberry Pi上）

```
~/timekeeper-emo-chan/
├── venv/                    # 仮想環境
├── main.py                  # メインアプリ
├── pattern_learner.py
├── message_generator.py
├── emo_scheduler.py
├── register_card.py
├── get_bocco_rooms.py
├── test_app.py
├── schema.sql
├── requirements.txt
├── timekeeper-emo.service
├── .env                     # 設定ファイル（転送後に編集）
├── card_mapping.json        # カード登録後に作成される
└── timekeeper.db           # 実行時に作成される
```

## 便利なコマンド

```bash
# サービスの再起動
sudo systemctl restart timekeeper-emo.service

# サービスの停止
sudo systemctl stop timekeeper-emo.service

# ログのリアルタイム表示
journalctl -u timekeeper-emo.service -f

# カードマッピングの確認
cat card_mapping.json

# Room IDの確認
python get_bocco_rooms.py
```

## 注意事項

- `.env`ファイルにはAPIトークンなどの機密情報が含まれるため、Gitにコミットしないこと
- `card_mapping.json`も同様に機密情報を含む可能性があります
- systemdサービスとして実行する場合、パスは絶対パスで指定してください

## サポート

問題が発生した場合：
1. ログを確認: `journalctl -u timekeeper-emo.service -n 50`
2. 手動実行でエラー確認: `python main.py`
3. README.mdのTroubleshootingセクションを参照

以上でRaspberry Piでの実行準備が完了です！
