# Raspberry Pi転送チェックリスト

## 転送前の確認

### ✅ 必須ファイル（必ず転送）
- [x] main.py
- [x] pattern_learner.py
- [x] message_generator.py
- [x] emo_scheduler.py
- [x] schema.sql
- [x] requirements.txt
- [x] .env
- [x] card_mapping.json（あれば）

### ✅ ユーティリティスクリプト
- [x] register_card.py
- [x] get_bocco_rooms.py
- [x] test_app.py
- [x] test_bocco_message.py

### ✅ ドキュメント
- [x] README.md
- [x] SETUP.md
- [x] DEPLOY_TO_RASPI.md

### ✅ システムファイル
- [x] timekeeper-emo.service

## 転送方法の選択

### 方法1: SCP（シンプル）

Windows PowerShellまたはGit Bashから：
```bash
scp -r d:/dev/timekeeper-emo-chan pi@<raspberry-pi-ip>:~/
```

### 方法2: Git（推奨）

```bash
# 1. Windowsでリポジトリ作成（まだの場合）
cd d:/dev/timekeeper-emo-chan
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main

# 2. Raspberry Piでクローン
ssh pi@<raspberry-pi-ip>
git clone <your-repo-url>
cd timekeeper-emo-chan
```

### 方法3: rsync（差分転送）

```bash
rsync -avz --exclude='__pycache__' --exclude='*.db' \
  d:/dev/timekeeper-emo-chan/ pi@<raspberry-pi-ip>:~/timekeeper-emo-chan/
```

## Raspberry Pi上での初期セットアップ

```bash
# SSH接続
ssh pi@<raspberry-pi-ip>

# プロジェクトディレクトリへ移動
cd ~/timekeeper-emo-chan

# システムパッケージ更新
sudo apt-get update
sudo apt-get upgrade -y

# 必要なパッケージインストール
sudo apt-get install -y python3 python3-pip python3-venv
sudo apt-get install -y libusb-1.0-0-dev python3-dev

# 仮想環境作成
python3 -m venv venv

# 仮想環境アクティベート
source venv/bin/activate

# Python パッケージインストール
pip install --upgrade pip
pip install -r requirements.txt

# ユーザー権限設定
sudo usermod -a -G dialout $USER

# 再ログイン（権限反映のため）
exit
```

## .envファイルの設定確認

Raspberry Pi上で：
```bash
cd ~/timekeeper-emo-chan
nano .env
```

以下を確認・修正：
```bash
# NFCリーダーのパスをRaspberry Pi用に変更
NFC_READER_PATH=usb

# その他の設定は既に入っているはず
BOCCO_ACCESS_TOKEN=...
BOCCO_REFRESH_TOKEN=...
TOGGL_API_TOKEN=...
```

## 動作確認

```bash
# 1. 基本テスト
source venv/bin/activate
python test_app.py

# 2. BOCCO emoテスト
python test_bocco_message.py

# 3. NFCリーダー確認
lsusb | grep Sony

# 4. アプリ起動テスト
python main.py
# Ctrl+Cで停止
```

## カード登録

```bash
source venv/bin/activate
python register_card.py
```

## systemdサービス設定

```bash
# サービスファイルのコピー
sudo cp timekeeper-emo.service /etc/systemd/system/

# パス確認・編集
sudo nano /etc/systemd/system/timekeeper-emo.service
# WorkingDirectory=/home/pi/timekeeper-emo-chan
# ExecStart=/home/pi/timekeeper-emo-chan/venv/bin/python /home/pi/timekeeper-emo-chan/main.py

# サービス有効化
sudo systemctl daemon-reload
sudo systemctl enable timekeeper-emo.service
sudo systemctl start timekeeper-emo.service

# ステータス確認
sudo systemctl status timekeeper-emo.service
```

## 完了確認

- [ ] NFCリーダーが認識される（lsusb）
- [ ] test_app.pyが正常に動作
- [ ] test_bocco_message.pyでメッセージ送信成功
- [ ] カード登録が完了
- [ ] main.pyが起動する
- [ ] NFCカードタップでTogglタイマーが動作
- [ ] BOCCO emoがメッセージを話す
- [ ] systemdサービスが起動する

全て完了したら、Timekeeper Emo-chanの運用開始です！🎉

## トラブルシューティング

問題が起きたら：
1. ログ確認: `journalctl -u timekeeper-emo.service -n 50`
2. 手動実行: `python main.py`（詳細エラー確認）
3. DEPLOY_TO_RASPI.mdのトラブルシューティング参照
