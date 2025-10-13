"""
Pattern Learner - 作業パターンの学習モジュール
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

try:
    import jpholiday
except ImportError:
    print("Warning: jpholiday not installed. Holiday detection will be limited.")
    jpholiday = None


class PatternLearner:
    """作業パターンを学習するクラス"""

    def __init__(self, db_connection: sqlite3.Connection, toggl_client=None):
        """
        Args:
            db_connection: SQLite データベース接続
            toggl_client: Toggl API クライアント
        """
        self.db = db_connection
        self.db.row_factory = sqlite3.Row
        self.toggl = toggl_client
        self.learning_period_days = 14
        self.pattern_threshold = 0.8  # 80%以上の頻度で「通常パターン」

    def is_holiday(self, date: datetime) -> bool:
        """
        日本の祝日、お盆、正月を判定

        Args:
            date: 判定する日付

        Returns:
            祝日・休日の場合True
        """
        # jpholiday ライブラリで祝日判定
        if jpholiday and jpholiday.is_holiday(date):
            return True

        # お盆: 8月13-16日
        if date.month == 8 and 13 <= date.day <= 16:
            return True

        # 正月: 12月29日-1月3日
        if (date.month == 12 and date.day >= 29) or \
           (date.month == 1 and date.day <= 3):
            return True

        return False

    def categorize_day(self, date: datetime) -> str:
        """
        日付を平日/休日に分類

        Args:
            date: 分類する日付

        Returns:
            'weekday', 'weekend', 'holiday' のいずれか
        """
        if date.weekday() >= 5:  # 土日
            return 'weekend'
        if self.is_holiday(date):
            return 'holiday'
        return 'weekday'

    def fetch_and_store_history(self) -> int:
        """
        Toggl APIから過去14日間のデータを取得してDBに保存

        Returns:
            保存したエントリー数
        """
        if not self.toggl:
            print("Warning: Toggl client not provided")
            return 0

        from datetime import timezone

        # タイムゾーン情報を持った日時を使用
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=self.learning_period_days)

        print(f"Fetching work history from {start_date.date()} to {end_date.date()}...")

        # Toggl API呼び出し
        try:
            entries = self.toggl.get_time_entries(start_date, end_date)
        except Exception as e:
            print(f"Error fetching from Toggl API: {e}")
            return 0

        # 既存データをクリア（再学習）
        self.db.execute("""
            DELETE FROM work_history
            WHERE start_time >= datetime(?, '-14 days')
        """, (end_date.isoformat(),))

        count = 0
        for entry in entries:
            if not entry.get('start'):
                continue

            start = datetime.fromisoformat(entry['start'].replace('Z', '+00:00'))
            end = None
            if entry.get('stop'):
                end = datetime.fromisoformat(entry['stop'].replace('Z', '+00:00'))

            day_category = self.categorize_day(start)
            duration = entry.get('duration', 0)
            if duration > 0:
                duration_minutes = duration // 60
            else:
                duration_minutes = 0

            self.db.execute("""
                INSERT INTO work_history
                (project_id, project_name, start_time, end_time,
                 duration_minutes, day_of_week, is_weekend, is_holiday, hour_of_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(entry.get('project_id', 'unknown')),
                entry.get('project_name', entry.get('description', 'Untitled')),
                start.isoformat(),
                end.isoformat() if end else None,
                duration_minutes,
                start.weekday(),
                1 if day_category == 'weekend' else 0,
                1 if day_category == 'holiday' else 0,
                start.hour
            ))
            count += 1

        self.db.commit()
        print(f"Stored {count} work history entries")
        return count

    def learn_project_patterns(self) -> Dict[str, dict]:
        """
        プロジェクトごとのパターンを学習

        Returns:
            プロジェクトIDをキーとした学習結果の辞書
        """
        print("Learning project patterns...")

        # 平日のパターンを取得
        weekday_data = self._learn_day_type_patterns(is_weekend=False)

        # 休日のパターンを取得
        weekend_data = self._learn_day_type_patterns(is_weekend=True)

        # 結果をマージしてDBに保存
        all_projects = set(weekday_data.keys()) | set(weekend_data.keys())
        results = {}

        for project_id in all_projects:
            weekday = weekday_data.get(project_id, {})
            weekend = weekend_data.get(project_id, {})

            project_name = weekday.get('name') or weekend.get('name', 'Unknown')
            weekday_hours = weekday.get('typical_hours', [])
            weekend_hours = weekend.get('typical_hours', [])
            weekday_avg = weekday.get('avg_duration', 0)
            weekend_avg = weekend.get('avg_duration', 0)

            # 最終作業日時を取得
            last_worked = self.db.execute("""
                SELECT MAX(start_time) as last_time
                FROM work_history
                WHERE project_id = ?
            """, (project_id,)).fetchone()

            last_worked_at = last_worked['last_time'] if last_worked else None

            # DBに保存
            self.db.execute("""
                INSERT OR REPLACE INTO project_patterns
                (project_id, project_name, weekday_typical_hours, weekend_typical_hours,
                 weekday_avg_duration_minutes, weekend_avg_duration_minutes,
                 last_worked_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                project_id,
                project_name,
                json.dumps(sorted(weekday_hours)),
                json.dumps(sorted(weekend_hours)),
                weekday_avg,
                weekend_avg,
                last_worked_at
            ))

            results[project_id] = {
                'name': project_name,
                'weekday_hours': weekday_hours,
                'weekend_hours': weekend_hours,
                'weekday_avg': weekday_avg,
                'weekend_avg': weekend_avg
            }

        self.db.commit()
        print(f"Learned patterns for {len(results)} projects")
        return results

    def _learn_day_type_patterns(self, is_weekend: bool) -> Dict[str, dict]:
        """
        平日または休日のパターンを学習（内部メソッド）

        Args:
            is_weekend: True=休日/祝日, False=平日

        Returns:
            プロジェクトごとのパターン辞書
        """
        # 時間帯ごとの作業頻度を取得
        rows = self.db.execute("""
            SELECT
                project_id,
                project_name,
                hour_of_day,
                COUNT(*) as frequency,
                AVG(duration_minutes) as avg_duration
            FROM work_history
            WHERE (is_weekend = 1 OR is_holiday = 1) = ?
                AND start_time >= datetime('now', '-14 days')
            GROUP BY project_id, hour_of_day
        """, (1 if is_weekend else 0,)).fetchall()

        # プロジェクトごとに集計
        project_data = {}
        for row in rows:
            pid = row['project_id']
            if pid not in project_data:
                project_data[pid] = {
                    'name': row['project_name'],
                    'hours': {},
                    'total_entries': 0,
                    'durations': []
                }

            project_data[pid]['hours'][row['hour_of_day']] = row['frequency']
            project_data[pid]['total_entries'] += row['frequency']
            project_data[pid]['durations'].append(row['avg_duration'])

        # 各プロジェクトで頻度の高い時間帯を抽出
        results = {}
        for pid, data in project_data.items():
            # データが少なすぎる場合はスキップ（3回未満）
            if data['total_entries'] < 3:
                continue

            # 平均以上の頻度の時間帯を「typical hours」とする
            avg_frequency = data['total_entries'] / len(data['hours'])
            threshold = avg_frequency * self.pattern_threshold

            typical_hours = [
                hour for hour, freq in data['hours'].items()
                if freq >= threshold
            ]

            # 平均作業時間を計算
            avg_duration = int(sum(data['durations']) / len(data['durations']))

            results[pid] = {
                'name': data['name'],
                'typical_hours': typical_hours,
                'avg_duration': avg_duration
            }

        return results

    def get_expected_project_at_time(self, check_time: datetime) -> Optional[Dict]:
        """
        指定時刻に通常作業しているはずのプロジェクトを取得

        Args:
            check_time: チェックする時刻

        Returns:
            プロジェクト情報の辞書、または None
        """
        day_type = self.categorize_day(check_time)
        is_weekend = 1 if day_type in ['weekend', 'holiday'] else 0

        # 該当時刻が典型的な作業時間に含まれるプロジェクトを検索
        hour_field = 'weekend_typical_hours' if is_weekend else 'weekday_typical_hours'

        projects = self.db.execute(f"""
            SELECT project_id, project_name, {hour_field} as typical_hours
            FROM project_patterns
            WHERE {hour_field} LIKE ?
        """, (f'%{check_time.hour}%',)).fetchall()

        if not projects:
            return None

        # 複数ある場合は最も最近作業したものを選択
        for project in projects:
            hours = json.loads(project['typical_hours'])
            if check_time.hour in hours:
                return {
                    'project_id': project['project_id'],
                    'project_name': project['project_name'],
                    'typical_hours': hours
                }

        return None
