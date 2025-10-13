"""
Emo Scheduler - 定期的な作業状況チェックと通知モジュール
"""

import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict

from pattern_learner import PatternLearner
from message_generator import MessageGenerator


class EmoScheduler:
    """定期的に作業状況をチェックしてBOCCO emoに通知するクラス"""

    def __init__(self, db_connection: sqlite3.Connection,
                 emo_client, toggl_client, pattern_learner: PatternLearner,
                 message_generator: MessageGenerator):
        """
        Args:
            db_connection: SQLite データベース接続
            emo_client: BOCCO emo API クライアント
            toggl_client: Toggl Track API クライアント
            pattern_learner: PatternLearner インスタンス
            message_generator: MessageGenerator インスタンス
        """
        self.db = db_connection
        self.db.row_factory = sqlite3.Row
        self.emo = emo_client
        self.toggl = toggl_client
        self.learner = pattern_learner
        self.msg_gen = message_generator

        # 設定
        self.check_interval = 3600  # 1時間 = 3600秒
        self.morning_threshold_minutes = 30  # 朝型プロジェクトの判定閾値
        self.other_threshold_hours = 2  # その他プロジェクトの判定閾値
        self.deep_night_hour = 22  # 深夜判定の開始時刻
        self.pattern_update_interval = 24 * 3600  # 24時間ごとにパターン更新

        # スレッド管理
        self.running = False
        self.check_thread = None
        self.update_thread = None
        self.last_pattern_update = datetime.now()

    def start(self):
        """バックグラウンドスレッドで定期チェック開始"""
        if self.running:
            print("Scheduler is already running")
            return

        self.running = True

        # 定期チェックスレッド
        self.check_thread = threading.Thread(target=self._periodic_check, daemon=True)
        self.check_thread.start()

        # パターン更新スレッド
        self.update_thread = threading.Thread(target=self._periodic_pattern_update, daemon=True)
        self.update_thread.start()

        print(f"Scheduler started (check interval: {self.check_interval}s)")

    def stop(self):
        """スレッドを停止"""
        self.running = False
        print("Scheduler stopped")

    def _periodic_check(self):
        """1時間ごとにチェック（バックグラウンドスレッド）"""
        while self.running:
            try:
                self.check_and_notify()
            except Exception as e:
                print(f"Error in periodic check: {e}")

            time.sleep(self.check_interval)

    def _periodic_pattern_update(self):
        """24時間ごとにパターンを再学習（バックグラウンドスレッド）"""
        while self.running:
            time.sleep(self.pattern_update_interval)

            try:
                print("Updating work patterns...")
                self.learner.fetch_and_store_history()
                self.learner.learn_project_patterns()
                self.last_pattern_update = datetime.now()
                print("Pattern update completed")
            except Exception as e:
                print(f"Error in pattern update: {e}")

    def check_and_notify(self):
        """現在の状況をチェックして通知"""
        now = datetime.now()

        # 休暇中の可能性をチェック
        if self._is_on_vacation():
            print("Appears to be on vacation, skipping notifications")
            return

        # 現在のタイマー状態を取得
        try:
            current_timer = self.toggl.get_current_timer()
        except Exception as e:
            print(f"Error getting current timer: {e}")
            return

        # 平日/休日/祝日判定
        day_type = self.learner.categorize_day(now)

        # ケース1: 何も作業していない → サボり検知
        if current_timer is None:
            self._check_for_sabori(now, day_type)

        # ケース2: 作業中 → いつもと違う時間かチェック
        else:
            self._check_unusual_time(current_timer, now, day_type)

    def _is_on_vacation(self) -> bool:
        """
        休暇中かどうかを判定（3日以上作業がない場合）

        Returns:
            休暇中と判定される場合True
        """
        result = self.db.execute("""
            SELECT MAX(start_time) as last_time FROM work_history
        """).fetchone()

        if not result or not result['last_time']:
            return False

        last_work_time = datetime.fromisoformat(result['last_time'])
        days_since = (datetime.now() - last_work_time).days

        return days_since >= 3

    def _check_for_sabori(self, now: datetime, day_type: str):
        """
        サボり検知

        Args:
            now: 現在時刻
            day_type: 日タイプ ('weekday', 'weekend', 'holiday')
        """
        # 現在時刻に通常作業しているはずのプロジェクトを検索
        expected_project = self.learner.get_expected_project_at_time(now)

        if not expected_project:
            return  # 該当なし

        project_id = expected_project['project_id']
        project_name = expected_project['project_name']

        # 過去1時間以内に同じ通知をしていないかチェック
        if self.msg_gen.has_recent_notification('sabori_reminder', minutes=60):
            return

        # メッセージを生成して送信
        message = self.msg_gen.get_random_message('sabori_reminder', {
            'project_name': project_name
        })

        print(f"[Sabori Check] {message}")

        try:
            self.emo.send_message(message)
            self.msg_gen.record_notification('sabori_reminder', project_id, message)
        except Exception as e:
            print(f"Error sending message to BOCCO emo: {e}")

    def _check_unusual_time(self, current_timer: Dict, now: datetime, day_type: str):
        """
        いつもと違う時間の検知

        Args:
            current_timer: Togglの現在のタイマー情報
            now: 現在時刻
            day_type: 日タイプ
        """
        project_id = current_timer.get('project_id')
        if not project_id:
            return

        # プロジェクトの通常パターンを取得
        pattern = self.db.execute("""
            SELECT * FROM project_patterns
            WHERE project_id = ?
        """, (str(project_id),)).fetchone()

        if not pattern:
            return  # パターン未学習

        # 平日/休日で適切なパターンを選択
        hour_field = 'weekend_typical_hours' if day_type in ['weekend', 'holiday'] \
            else 'weekday_typical_hours'

        typical_hours_json = pattern[hour_field]
        if not typical_hours_json:
            return

        typical_hours = json.loads(typical_hours_json)
        if not typical_hours:
            return

        # 現在の時刻が通常パターンに含まれていれば何もしない
        if now.hour in typical_hours:
            return

        # 時間差を計算
        min_typical = min(typical_hours)
        max_typical = max(typical_hours)
        project_name = pattern['project_name']

        category = None
        timer_start = current_timer.get('start')

        # このセッション内で既に通知済みかチェック
        if timer_start:
            if self.msg_gen.has_recent_notification('early_start', minutes=9999,
                                                     project_id=str(project_id)):
                return
            if self.msg_gen.has_recent_notification('late_work', minutes=9999,
                                                     project_id=str(project_id)):
                return
            if self.msg_gen.has_recent_notification('deep_night_praise', minutes=9999,
                                                     project_id=str(project_id)):
                return

        # 朝型プロジェクト（通常9時以前に開始）の場合：30分単位で判定
        if min_typical <= 9:
            time_diff_minutes = (min_typical * 60) - (now.hour * 60 + now.minute)
            if time_diff_minutes >= self.morning_threshold_minutes:
                category = 'early_start'

        # その他のプロジェクト：2時間単位で判定
        if category is None:
            if now.hour < min_typical - self.other_threshold_hours:
                category = 'early_start'
            elif now.hour > max_typical + self.other_threshold_hours:
                # 深夜作業
                if now.hour >= self.deep_night_hour:
                    category = 'deep_night_praise'
                else:
                    category = 'late_work'

        if category is None:
            return  # 通常範囲内

        # メッセージを生成して送信
        message = self.msg_gen.get_random_message(category, {
            'project_name': project_name
        })

        print(f"[Unusual Time Check - {category}] {message}")

        try:
            self.emo.send_message(message)
            self.msg_gen.record_notification(category, str(project_id), message)
        except Exception as e:
            print(f"Error sending message to BOCCO emo: {e}")

    def force_pattern_update(self):
        """パターンを強制的に再学習"""
        print("Force updating patterns...")
        try:
            self.learner.fetch_and_store_history()
            self.learner.learn_project_patterns()
            self.last_pattern_update = datetime.now()
            print("Pattern update completed")
        except Exception as e:
            print(f"Error in pattern update: {e}")

    def get_status(self) -> Dict:
        """
        スケジューラーの状態を取得

        Returns:
            状態情報の辞書
        """
        return {
            'running': self.running,
            'check_interval_seconds': self.check_interval,
            'last_pattern_update': self.last_pattern_update.isoformat(),
            'on_vacation': self._is_on_vacation()
        }
