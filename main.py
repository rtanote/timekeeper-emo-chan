"""
Timekeeper Emo-chan - Main Application
NFCカードタップでToggl Trackのタイマーを制御し、BOCCO emoが反応するアプリ
"""

import os
import sqlite3
import signal
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

from pattern_learner import PatternLearner
from message_generator import MessageGenerator
from emo_scheduler import EmoScheduler

# ロガー設定
def setup_logger():
    """ロガーを設定"""
    logger = logging.getLogger('timekeeper')
    logger.setLevel(logging.DEBUG)

    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # ファイルハンドラー
    file_handler = logging.FileHandler('timekeeper.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # フォーマッター
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()


# BOCCO emo クライアント
try:
    from emo_platform import Client, Tokens, BizBasicClient, BizAdvancedClient
    EMO_PLATFORM_AVAILABLE = True
except ImportError:
    print("Warning: emo-platform-api-sdk not installed. BOCCO emo features will be disabled.")
    EMO_PLATFORM_AVAILABLE = False


class BoccoEmoClient:
    """BOCCO emo API クライアント"""

    def __init__(self, access_token: str = None, refresh_token: str = None,
                 api_key: str = None, room_id: str = None, account_type: str = "personal"):
        """
        Args:
            access_token: アクセストークン（個人アカウント用）
            refresh_token: リフレッシュトークン（個人アカウント用）
            api_key: APIキー（ビジネスアカウント用）
            room_id: ルームID
            account_type: アカウントタイプ ('personal', 'biz_basic', 'biz_advanced')
        """
        self.room_id = room_id
        self.account_type = account_type
        self.client = None
        self.room_client = None

        if not EMO_PLATFORM_AVAILABLE:
            print("[BOCCO emo] SDK not available, running in dummy mode")
            return

        try:
            # アカウントタイプに応じてクライアント初期化
            if account_type == "personal":
                if access_token and refresh_token:
                    self.client = Client(tokens=Tokens(
                        access_token=access_token,
                        refresh_token=refresh_token
                    ))
                else:
                    # 環境変数から読み込み
                    self.client = Client()

                # ルームクライアント作成
                if room_id:
                    self.room_client = self.client.create_room_client(room_id)
                else:
                    # ルームID未指定の場合は最初のルームを使用
                    room_ids = self.client.get_rooms_id()
                    if room_ids:
                        self.room_id = room_ids[0]
                        self.room_client = self.client.create_room_client(room_ids[0])

            elif account_type in ["biz_basic", "biz_advanced"]:
                if not api_key:
                    raise ValueError("API key is required for business accounts")

                if account_type == "biz_basic":
                    self.client = BizBasicClient()
                else:
                    self.client = BizAdvancedClient()

                if room_id:
                    self.room_client = self.client.create_room_client(api_key, room_id)
                else:
                    # ルームID未指定の場合は最初のルームを使用
                    room_ids = self.client.get_rooms_id(api_key)
                    if room_ids:
                        self.room_id = room_ids[0]
                        self.room_client = self.client.create_room_client(api_key, room_ids[0])

            print(f"[BOCCO emo] Initialized ({account_type}, room: {self.room_id})")

        except Exception as e:
            print(f"[BOCCO emo] Initialization error: {e}")
            print("[BOCCO emo] Running in dummy mode")

    def send_message(self, message: str):
        """
        メッセージを送信

        Args:
            message: 送信するテキストメッセージ
        """
        print(f"[BOCCO emo] {message}")

        if not self.room_client:
            print("[BOCCO emo] Room client not initialized, message not sent")
            return

        try:
            # send_msg()メソッドでテキストメッセージを送信
            response = self.room_client.send_msg(message)
            print(f"[BOCCO emo] Message sent successfully")
            return response

        except Exception as e:
            print(f"[BOCCO emo] Error sending message: {e}")


class TogglClient:
    """Toggl Track API v9 クライアント"""

    def __init__(self, api_token: str, workspace_id: str):
        """
        Args:
            api_token: Toggl Track API token
            workspace_id: Workspace ID
        """
        self.api_token = api_token
        self.workspace_id = workspace_id
        self.base_url = "https://api.track.toggl.com/api/v9"
        self.headers = {
            'content-type': 'application/json',
        }

        # Basic認証の設定（API tokenを使用）
        from base64 import b64encode
        # API tokenの場合はトークン:api_tokenの形式
        auth_str = f"{api_token}:api_token"
        b64_auth = b64encode(auth_str.encode()).decode("ascii")
        self.headers['Authorization'] = f'Basic {b64_auth}'

    def get_time_entries(self, start_date: datetime, end_date: datetime):
        """
        時間エントリーを取得

        Args:
            start_date: 開始日時（UTCタイムゾーン推奨）
            end_date: 終了日時（UTCタイムゾーン推奨）

        Returns:
            時間エントリーのリスト
        """
        import requests

        # ISO 8601形式に変換（タイムゾーン情報を含む）
        # Toggl APIはRFC3339形式を期待
        start_str = start_date.isoformat().replace('+00:00', 'Z')
        end_str = end_date.isoformat().replace('+00:00', 'Z')

        try:
            response = requests.get(
                f"{self.base_url}/me/time_entries",
                headers=self.headers,
                params={
                    'start_date': start_str,
                    'end_date': end_str
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[Toggl] Error fetching time entries: {e}")
            return []

    def get_current_timer(self):
        """
        現在稼働中のタイマーを取得

        Returns:
            現在のタイマー情報（dict）、またはNone
        """
        import requests

        try:
            response = requests.get(
                f"{self.base_url}/me/time_entries/current",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # 稼働中のタイマーがない場合はNoneを返す
            if not data or data.get('id') is None:
                return None

            return data
        except requests.exceptions.RequestException as e:
            print(f"[Toggl] Error getting current timer: {e}")
            return None

    def start_timer(self, project_id: str, description: str = ""):
        """
        タイマーを開始

        Args:
            project_id: プロジェクトID
            description: タイマーの説明（オプション）

        Returns:
            作成されたタイマー情報（dict）
        """
        import requests
        from datetime import timezone

        # UTC時刻を明示的に使用
        start_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        payload = {
            "workspace_id": int(self.workspace_id),
            "project_id": int(project_id) if project_id else None,
            "description": description,
            "created_with": "timekeeper-emo-chan",
            "duration": -1,  # -1 = running timer
            "start": start_time
        }

        try:
            response = requests.post(
                f"{self.base_url}/workspaces/{self.workspace_id}/time_entries",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            print(f"[Toggl] Timer started for project {project_id}")
            return data
        except requests.exceptions.RequestException as e:
            print(f"[Toggl] Error starting timer: {e}")
            raise

    def stop_timer(self, timer_id: int = None, retry_on_500: bool = True):
        """
        タイマーを停止

        Args:
            timer_id: タイマーID（指定しない場合は現在のタイマーを停止）
            retry_on_500: 500エラー時にリトライするか

        Returns:
            停止されたタイマー情報（dict）
        """
        import requests
        import time

        # timer_id未指定の場合は現在のタイマーを取得
        if timer_id is None:
            current = self.get_current_timer()
            if current is None:
                print("[Toggl] No running timer to stop")
                return None
            timer_id = current['id']

        max_retries = 3 if retry_on_500 else 1
        for attempt in range(max_retries):
            try:
                response = requests.patch(
                    f"{self.base_url}/workspaces/{self.workspace_id}/time_entries/{timer_id}/stop",
                    headers=self.headers,
                    timeout=10
                )

                # 500エラーの場合はリトライ
                if response.status_code == 500 and attempt < max_retries - 1:
                    print(f"[Toggl] 500 error on stop timer, retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(1)  # 1秒待ってリトライ
                    continue

                response.raise_for_status()
                data = response.json()
                print(f"[Toggl] Timer stopped")
                return data

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"[Toggl] Error stopping timer, retrying... (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(1)
                else:
                    print(f"[Toggl] Error stopping timer after {max_retries} attempts: {e}")
                    # 最後の試行でも失敗した場合は例外を投げずにNoneを返す
                    return None


class NFCReader:
    """NFC リーダー (Sony RC-S380)"""

    def __init__(self, device_path: str = None):
        """
        Args:
            device_path: NFCリーダーのデバイスパス（Noneの場合は環境変数から読み込む）
        """
        # 環境変数から読み込む（未指定の場合）
        if device_path is None:
            device_path = os.getenv('NFC_READER_PATH', 'usb')

        self.device_path = device_path
        self.clf = None
        self.should_stop = False  # 停止フラグ

        try:
            import nfc
            self.nfc_available = True
        except ImportError:
            logger.warning("nfcpy not installed, running in dummy mode")
            self.nfc_available = False
            return

        try:
            # NFCリーダーを初期化
            logger.info(f"Initializing NFC reader with path: {device_path}")
            self.clf = nfc.ContactlessFrontend(device_path)
            logger.info(f"NFC Reader initialized: {self.clf}")
        except Exception as e:
            logger.error(f"Failed to initialize NFC reader with path '{device_path}': {e}")

            # usb:VID:PID 形式の場合は 'usb' だけで再試行
            if ':' in device_path and device_path.startswith('usb'):
                logger.info("Retrying with generic 'usb' path...")
                try:
                    self.clf = nfc.ContactlessFrontend('usb')
                    logger.info(f"NFC Reader initialized with generic 'usb' path: {self.clf}")
                    self.device_path = 'usb'
                except Exception as e2:
                    logger.error(f"Failed to initialize with generic 'usb' path: {e2}")
                    logger.info("Running in dummy mode")
                    self.nfc_available = False
            else:
                logger.info("Running in dummy mode")
                self.nfc_available = False

    def read_card(self):
        """
        カードを読み取り（ブロッキング）

        Returns:
            カードID（16進数文字列）、またはNone
        """
        if not self.nfc_available or not self.clf:
            # ダミーモード：1秒待機してNoneを返す
            import time
            time.sleep(1)
            return None

        try:
            import nfc

            # カードを待機（ブロッキング）
            logger.debug("Waiting for NFC card...")
            tag = self.clf.connect(
                rdwr={
                    'on-connect': lambda tag: False  # 接続したら即座に切断
                },
                terminate=lambda: self.should_stop  # 停止フラグをチェック
            )

            if tag:
                # カードIDを16進数文字列に変換
                card_id = tag.identifier.hex()
                logger.info(f"Card detected: {card_id}")
                return card_id

        except KeyboardInterrupt:
            raise
        except (IOError, OSError) as e:
            # close()による強制終了の場合はログを出さずに終了
            if self.should_stop:
                logger.debug("NFC reader stopped")
                return None
            logger.error(f"IO error reading card: {e}")
            import time
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error reading card: {e}", exc_info=True)
            import time
            time.sleep(0.5)  # エラー時は少し待機

        return None

    def close(self):
        """NFCリーダーをクローズ"""
        # 停止フラグを設定してブロッキングを解除
        self.should_stop = True
        logger.info("NFC reader stop flag set")

        if self.clf:
            try:
                # clf.close()を呼んで強制的にconnect()を中断
                # これにより、ブロッキング中のconnect()が例外を投げて終了する
                self.clf.close()
                logger.info("NFC reader closed")
            except Exception as e:
                logger.error(f"Error closing NFC reader: {e}")
            finally:
                # clfをNoneに設定して、次回のread_card()がダミーモードになるようにする
                self.clf = None


class TimekeeperEmoApp:
    """Timekeeper Emo-chan メインアプリケーション"""

    def __init__(self):
        # 環境変数読み込み
        load_dotenv()

        # データベース初期化
        self.db = self._init_database()

        # クライアント初期化
        account_type = os.getenv('BOCCO_ACCOUNT_TYPE', 'personal')
        self.emo = BoccoEmoClient(
            access_token=os.getenv('BOCCO_ACCESS_TOKEN'),
            refresh_token=os.getenv('BOCCO_REFRESH_TOKEN'),
            api_key=os.getenv('BOCCO_API_KEY'),
            room_id=os.getenv('BOCCO_ROOM_ID'),
            account_type=account_type
        )

        self.toggl = TogglClient(
            api_token=os.getenv('TOGGL_API_TOKEN', ''),
            workspace_id=os.getenv('TOGGL_WORKSPACE_ID', '')
        )

        # NFCReaderは内部で環境変数を読み込む
        self.nfc = NFCReader()

        # コア機能初期化
        self.learner = PatternLearner(self.db, self.toggl)
        self.msg_gen = MessageGenerator(self.db)
        self.scheduler = EmoScheduler(
            self.db, self.emo, self.toggl,
            self.learner, self.msg_gen
        )

        # カードとプロジェクトのマッピング（要設定）
        self.card_projects = self._load_card_mapping()

        # デバウンス用：最後にタップしたカードIDと時刻
        self.last_card_tap = {}  # {card_id: timestamp}
        self.debounce_seconds = 3  # 同じカードを3秒以内に複数回タップした場合は無視

        # シグナルハンドラー設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _init_database(self) -> sqlite3.Connection:
        """データベースを初期化"""
        db_path = os.getenv('DATABASE_PATH', 'timekeeper.db')
        db = sqlite3.connect(db_path, check_same_thread=False)

        # スキーマ読み込み
        with open('schema.sql', 'r', encoding='utf-8') as f:
            db.executescript(f.read())

        print(f"Database initialized: {db_path}")
        return db

    def _load_card_mapping(self) -> dict:
        """
        NFCカードIDとTogglプロジェクトのマッピングを読み込み

        Returns:
            カードIDをキーとし、プロジェクトIDを値とする辞書
        """
        import json

        mapping_file = os.getenv('CARD_MAPPING_FILE', 'card_mapping.json')

        if not os.path.exists(mapping_file):
            print(f"! Card mapping file not found: {mapping_file}")
            print("  Run 'python register_card.py' to register cards")
            return {}

        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 新形式: {'card_id': {'project_id': 'xxx', 'project_name': 'yyy'}}
            # 旧形式: {'card_id': 'project_id'}
            # 両方サポート
            mapping = {}
            for card_id, info in data.items():
                if isinstance(info, dict):
                    mapping[card_id] = info.get('project_id')
                else:
                    mapping[card_id] = info

            print(f"[OK] Loaded {len(mapping)} card(s) from {mapping_file}")
            return mapping

        except Exception as e:
            print(f"[ERROR] Error loading card mapping: {e}")
            return {}

    def _signal_handler(self, signum, frame):
        """シグナルハンドラー（Ctrl+C など）"""
        print("\nShutting down gracefully...")
        self.shutdown()
        sys.exit(0)

    def start(self):
        """アプリケーション起動"""
        print("=" * 50)
        print("Timekeeper Emo-chan starting...")
        print("=" * 50)

        # 初回パターン学習
        print("\n[1/3] Learning work patterns from Toggl...")
        try:
            count = self.learner.fetch_and_store_history()
            if count > 0:
                self.learner.learn_project_patterns()
                print(f"[OK] Learned patterns from {count} entries")
            else:
                print("! No work history found. Pattern learning will be limited.")
        except Exception as e:
            print(f"[ERROR] Error during pattern learning: {e}")
            print("  Continuing without pattern learning...")

        # 定期チェック開始
        print("\n[2/3] Starting periodic scheduler...")
        self.scheduler.start()
        print("[OK] Scheduler started")

        # NFCリーダー監視（メインループ）
        print("\n[3/3] Starting NFC reader...")
        print("[OK] Ready! Waiting for NFC card tap...\n")
        print("=" * 50)

        self.nfc_loop()

    def nfc_loop(self):
        """NFCカード待ち受けループ（メインスレッド）"""
        while True:
            try:
                card_id = self.nfc.read_card()
                if card_id:
                    self.handle_nfc_tap(card_id)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in NFC loop: {e}")

    def handle_nfc_tap(self, card_id: str):
        """
        NFCカードタップ時の処理

        Args:
            card_id: カードID
        """
        import time

        print(f"\n[NFC] Card detected: {card_id}")

        # デバウンスチェック：同じカードを短時間に複数回タップした場合は無視
        current_time = time.time()
        if card_id in self.last_card_tap:
            time_since_last_tap = current_time - self.last_card_tap[card_id]
            if time_since_last_tap < self.debounce_seconds:
                print(f"[NFC] Debounce: Ignoring tap (last tap was {time_since_last_tap:.1f}s ago)")
                return

        # 最後のタップ時刻を更新
        self.last_card_tap[card_id] = current_time

        # カードIDからプロジェクトを取得
        project_id = self.card_projects.get(card_id)
        if not project_id:
            print(f"Unknown card: {card_id}")
            self.emo.send_message("このカード、登録されてないみたい...")
            return

        # 現在のタイマー状態を確認
        try:
            current_timer = self.toggl.get_current_timer()
        except Exception as e:
            print(f"Error getting timer: {e}")
            return

        # タイマーが動いていない → 開始
        if current_timer is None:
            self._start_timer(project_id)
        # 同じプロジェクトのタイマーが動いている → 停止
        elif current_timer.get('project_id') == int(project_id):
            self._stop_timer(current_timer)
        # 別のプロジェクトが動いている → 切り替え
        else:
            self._switch_timer(current_timer, project_id)

    def _start_timer(self, project_id: str):
        """タイマーを開始"""
        try:
            self.toggl.start_timer(project_id)

            # プロジェクト名を取得（優先順位: card_mapping.json > DB > デフォルト）
            project_name = self._get_project_name(project_id)

            # メッセージ送信
            message = self.msg_gen.get_random_message('timer_start', {
                'project_name': project_name
            })
            self.emo.send_message(message)
            self.msg_gen.record_notification('timer_start', project_id, message)

            logger.info(f"Timer started: {project_name}")

        except Exception as e:
            logger.error(f"Error starting timer: {e}")

    def _get_project_name(self, project_id: str) -> str:
        """
        プロジェクト名を取得

        Args:
            project_id: プロジェクトID

        Returns:
            プロジェクト名
        """
        import json

        # 1. card_mapping.jsonから取得を試みる
        try:
            mapping_file = os.getenv('CARD_MAPPING_FILE', 'card_mapping.json')
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # project_idに対応するカードを探す
                for card_id, info in data.items():
                    if isinstance(info, dict):
                        if info.get('project_id') == project_id:
                            project_name = info.get('project_name')
                            if project_name:
                                return project_name
        except Exception as e:
            logger.warning(f"Failed to get project name from card_mapping.json: {e}")

        # 2. データベースから取得を試みる
        try:
            project = self.db.execute("""
                SELECT project_name FROM project_patterns
                WHERE project_id = ?
            """, (project_id,)).fetchone()

            if project and project['project_name']:
                return project['project_name']
        except Exception as e:
            logger.warning(f"Failed to get project name from database: {e}")

        # 3. デフォルト値
        return f"プロジェクト{project_id}"

    def _stop_timer(self, current_timer: dict):
        """タイマーを停止"""
        try:
            result = self.toggl.stop_timer()

            # リトライしても停止できなかった場合
            if result is None:
                print("[WARNING] Failed to stop timer after retries, but continuing...")
                self.emo.send_message("タイマーの停止に失敗したかも...もう一度タッチしてみて？")
                return

            # 作業時間を計算
            from datetime import timezone
            start_time = datetime.fromisoformat(
                current_timer['start'].replace('Z', '+00:00')
            )
            # 両方の日時をタイムゾーン対応にする
            now_with_tz = datetime.now(timezone.utc)
            duration_minutes = int((now_with_tz - start_time).total_seconds() / 60)

            project_id = current_timer.get('project_id', '')
            project_name = current_timer.get('project_name', 'プロジェクト')

            # メッセージ送信
            message = self.msg_gen.get_random_message('timer_stop', {
                'project_name': project_name,
                'duration': duration_minutes
            })
            self.emo.send_message(message)
            self.msg_gen.record_notification('timer_stop', project_id, message)

            print(f"[OK] Timer stopped: {project_name} ({duration_minutes} min)")

        except Exception as e:
            print(f"Error stopping timer: {e}")

    def _switch_timer(self, current_timer: dict, new_project_id: str):
        """タイマーを切り替え"""
        print("Switching project...")
        self._stop_timer(current_timer)
        self._start_timer(new_project_id)

    def shutdown(self):
        """アプリケーション終了処理"""
        import threading
        import time

        print("Stopping scheduler...")
        self.scheduler.stop()

        print("Closing NFC reader...")
        # NFCリーダーのクローズを別スレッドで実行（タイムアウト付き）
        close_thread = threading.Thread(target=self.nfc.close, daemon=True)
        close_thread.start()
        close_thread.join(timeout=2.0)  # 最大2秒待つ

        if close_thread.is_alive():
            logger.warning("NFC reader close timed out, forcing exit")
            print("NFC reader close timed out")
        else:
            logger.info("NFC reader closed successfully")

        print("Closing database...")
        self.db.close()

        print("Goodbye!")


def main():
    """エントリーポイント"""
    app = TimekeeperEmoApp()
    try:
        app.start()
    except Exception as e:
        print(f"Fatal error: {e}")
        app.shutdown()
        sys.exit(1)


if __name__ == '__main__':
    main()
