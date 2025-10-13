"""
Message Generator - コンテキストに応じたメッセージ生成モジュール
"""

import sqlite3
from typing import Dict, Optional


class MessageGenerator:
    """BOCCO emoに送信するメッセージを生成するクラス"""

    def __init__(self, db_connection: sqlite3.Connection):
        """
        Args:
            db_connection: SQLite データベース接続
        """
        self.db = db_connection
        self.db.row_factory = sqlite3.Row
        self._initialize_templates()

    def _initialize_templates(self):
        """初回起動時にメッセージテンプレートを登録"""
        templates = [
            # サボり検知
            ('sabori_reminder', 'そろそろ{project_name}やったほうがよいんじゃない？'),
            ('sabori_reminder', '{project_name}、今日はまだだよね？始めようか！'),
            ('sabori_reminder', 'いつもの時間だよ！{project_name}、やる？'),
            ('sabori_reminder', '{project_name}の時間だよ～！準備はいい？'),
            ('sabori_reminder', 'あれ、{project_name}忘れてない？大丈夫？'),
            ('sabori_reminder', '{project_name}、そろそろ始める時間だと思うんだけど...'),
            ('sabori_reminder', '今日も{project_name}、がんばろうね！'),
            ('sabori_reminder', '{project_name}のこと、覚えてる？そろそろだよ！'),

            # 朝早い開始
            ('early_start', 'あれ、今日は朝やるんだ！がんばって！'),
            ('early_start', 'おはよう！今日は早いね。応援してるよ！'),
            ('early_start', '朝活いいね！{project_name}、ファイト！'),
            ('early_start', 'いつもより早いね！すごい、頑張ってね！'),
            ('early_start', '早起きえらい！今日もいい一日になりそうだね！'),
            ('early_start', 'わあ、朝から{project_name}！やる気満々だね！'),
            ('early_start', 'おはよう！朝から{project_name}、素敵だね！'),

            # 遅い時間の作業
            ('late_work', '今日は夜やるんだね！無理しないでね！'),
            ('late_work', '夜型になってるね。体調には気をつけて！'),
            ('late_work', '遅い時間だけど、がんばってね！'),
            ('late_work', 'いつもと違う時間だね。集中できてる？'),
            ('late_work', '夜の{project_name}もいいね。無理は禁物だよ！'),
            ('late_work', 'こんな時間に{project_name}！締め切り近いのかな？'),

            # 深夜のねぎらい
            ('deep_night_praise', 'こんな時間までお疲れさま！もう少しだね！'),
            ('deep_night_praise', '夜遅くまでがんばったね！ゆっくり休んでね！'),
            ('deep_night_praise', 'お疲れさま！今日も一日よくがんばったね！'),
            ('deep_night_praise', '深夜までお疲れさま！無理しすぎないでね！'),
            ('deep_night_praise', 'すごい集中力！でもそろそろ休もう？'),
            ('deep_night_praise', '今日も一日お疲れさま！ゆっくり休んでね！'),
            ('deep_night_praise', '{project_name}、こんな時間まで！本当にお疲れさま！'),
            ('deep_night_praise', '深夜の作業、お疲れさま！明日もがんばろうね！'),

            # タイマー開始時（通常時）
            ('timer_start', 'よーし、{project_name}始めよう！'),
            ('timer_start', '{project_name}スタート！がんばって！'),
            ('timer_start', 'いってらっしゃい！{project_name}、ファイト！'),
            ('timer_start', '{project_name}の時間だね！応援してるよ！'),
            ('timer_start', 'さあ、{project_name}始めましょ！'),

            # タイマー停止時（通常時）
            ('timer_stop', 'お疲れさま！{duration}分間、よくがんばったね！'),
            ('timer_stop', '{duration}分間、集中できた？お疲れさま！'),
            ('timer_stop', 'おつかれー！{duration}分、すごいね！'),
            ('timer_stop', '{project_name}終了！{duration}分間お疲れさまでした！'),
            ('timer_stop', 'よくやった！{duration}分間がんばったね！'),
        ]

        for category, message in templates:
            try:
                self.db.execute("""
                    INSERT INTO message_templates (category, message_template)
                    VALUES (?, ?)
                """, (category, message))
            except sqlite3.IntegrityError:
                # 既に存在する場合はスキップ
                pass

        self.db.commit()

    def get_random_message(self, category: str, context: Optional[Dict] = None) -> str:
        """
        カテゴリからランダムにメッセージを選択

        Args:
            category: メッセージカテゴリ
                - 'sabori_reminder': サボり検知
                - 'early_start': 朝早い開始
                - 'late_work': 遅い時間の作業
                - 'deep_night_praise': 深夜のねぎらい
                - 'timer_start': タイマー開始
                - 'timer_stop': タイマー停止
            context: メッセージに埋め込む変数の辞書
                - project_name: プロジェクト名
                - duration: 作業時間（分）
                - minutes_late: 遅れ時間（分）

        Returns:
            生成されたメッセージ文字列
        """
        if context is None:
            context = {}

        # テンプレートをランダムに取得
        result = self.db.execute("""
            SELECT message_template FROM message_templates
            WHERE category = ?
            ORDER BY RANDOM()
            LIMIT 1
        """, (category,)).fetchone()

        if not result:
            # デフォルトメッセージ
            return "がんばって！"

        template = result['message_template']

        # プレースホルダーを置換
        try:
            message = template.format(**context)
        except KeyError as e:
            # プレースホルダーが足りない場合はそのまま返す
            print(f"Warning: Missing placeholder {e} in template")
            message = template

        return message

    def record_notification(self, category: str, project_id: Optional[str], message: str):
        """
        通知履歴を記録

        Args:
            category: メッセージカテゴリ
            project_id: プロジェクトID（省略可）
            message: 送信したメッセージ
        """
        self.db.execute("""
            INSERT INTO notification_history (category, project_id, message)
            VALUES (?, ?, ?)
        """, (category, project_id, message))
        self.db.commit()

    def has_recent_notification(self, category: str, minutes: int = 60,
                                project_id: Optional[str] = None) -> bool:
        """
        最近同じカテゴリの通知を送信したかチェック

        Args:
            category: メッセージカテゴリ
            minutes: チェックする時間範囲（分）
            project_id: プロジェクトID（指定した場合はプロジェクト単位でチェック）

        Returns:
            最近通知している場合True
        """
        if project_id:
            result = self.db.execute("""
                SELECT COUNT(*) as count FROM notification_history
                WHERE category = ? AND project_id = ?
                    AND notified_at >= datetime('now', ? || ' minutes')
            """, (category, project_id, -minutes)).fetchone()
        else:
            result = self.db.execute("""
                SELECT COUNT(*) as count FROM notification_history
                WHERE category = ?
                    AND notified_at >= datetime('now', ? || ' minutes')
            """, (category, -minutes)).fetchone()

        return result['count'] > 0

    def cleanup_old_notifications(self, days: int = 7):
        """
        古い通知履歴を削除

        Args:
            days: 保持する日数
        """
        self.db.execute("""
            DELETE FROM notification_history
            WHERE notified_at < datetime('now', ? || ' days')
        """, (-days,))
        self.db.commit()

    def add_custom_message(self, category: str, message_template: str):
        """
        カスタムメッセージテンプレートを追加

        Args:
            category: メッセージカテゴリ
            message_template: メッセージテンプレート文字列
        """
        try:
            self.db.execute("""
                INSERT INTO message_templates (category, message_template)
                VALUES (?, ?)
            """, (category, message_template))
            self.db.commit()
            print(f"Added custom message to category '{category}'")
        except sqlite3.IntegrityError:
            print(f"Message already exists in category '{category}'")
