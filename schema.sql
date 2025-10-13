-- Timekeeper Emo-chan Database Schema

-- 作業履歴の記録（Toggl APIから取得したデータをキャッシュ）
CREATE TABLE IF NOT EXISTS work_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    project_name TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_minutes INTEGER,
    day_of_week INTEGER,  -- 0=月, 6=日
    is_weekend BOOLEAN DEFAULT 0,
    is_holiday BOOLEAN DEFAULT 0,
    hour_of_day INTEGER,  -- 0-23
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- プロジェクトごとの学習パターン
CREATE TABLE IF NOT EXISTS project_patterns (
    project_id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    -- 平日のパターン (JSON配列: [9, 10, 14, 15, 16])
    weekday_typical_hours TEXT,
    -- 休日のパターン
    weekend_typical_hours TEXT,
    -- 平日の平均作業時間
    weekday_avg_duration_minutes INTEGER,
    -- 休日の平均作業時間
    weekend_avg_duration_minutes INTEGER,
    -- 最終作業日時
    last_worked_at DATETIME,
    -- 更新日時
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- メッセージテンプレート
CREATE TABLE IF NOT EXISTS message_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,  -- 'sabori_reminder', 'early_start', 'late_work', 'deep_night_praise'
    message_template TEXT NOT NULL,
    -- {project_name}, {minutes_late}, {time_diff} などのプレースホルダーを含む
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, message_template)
);

-- 通知履歴（同じメッセージを連発しないため）
CREATE TABLE IF NOT EXISTS notification_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    project_id TEXT,
    message TEXT NOT NULL,
    notified_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_work_history_project_time
    ON work_history(project_id, start_time);

CREATE INDEX IF NOT EXISTS idx_work_history_day_type
    ON work_history(is_weekend, is_holiday, hour_of_day);

CREATE INDEX IF NOT EXISTS idx_notification_history_category
    ON notification_history(category, notified_at);
