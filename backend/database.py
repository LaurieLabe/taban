import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "taban.db")


def get_db():
    """获取数据库连接。每次调用返回新连接，调用方负责关闭。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """建表，仅在首次启动时调用。"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname      TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            avatar        TEXT DEFAULT '',
            bio           TEXT DEFAULT '',
            card_image    TEXT DEFAULT '',
            personality   TEXT,
            interests     TEXT,
            topics        TEXT,
            consumption   TEXT,
            life_rhythm   TEXT,
            distance      TEXT DEFAULT 'city',
            empathy       INTEGER DEFAULT 50,
            agency        INTEGER DEFAULT 50,
            energy        INTEGER DEFAULT 50,
            sensitivity   INTEGER DEFAULT 50,
            openness      INTEGER DEFAULT 50,
            birth_date    TEXT DEFAULT '',
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id      INTEGER NOT NULL,
            title           TEXT NOT NULL,
            description     TEXT DEFAULT '',
            location        TEXT NOT NULL,
            event_date      TEXT NOT NULL,
            event_duration  TEXT DEFAULT '2小时',
            max_participants INTEGER DEFAULT 5,
            category        TEXT DEFAULT '',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creator_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id  INTEGER NOT NULL,
            to_user_id    INTEGER NOT NULL,
            content       TEXT NOT NULL,
            context_type  TEXT DEFAULT 'person',
            context_id    INTEGER,
            is_read       INTEGER DEFAULT 0,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user_id) REFERENCES users(id),
            FOREIGN KEY (to_user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS likes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id  INTEGER NOT NULL,
            to_user_id    INTEGER NOT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user_id) REFERENCES users(id),
            FOREIGN KEY (to_user_id) REFERENCES users(id),
            UNIQUE(from_user_id, to_user_id)
        );

        CREATE TABLE IF NOT EXISTS event_participants (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id      INTEGER NOT NULL,
            user_id       INTEGER NOT NULL,
            status        TEXT DEFAULT 'pending',
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES events(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(event_id, user_id)
        );
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    # 删除旧数据库重新建表（开发阶段）
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    print("数据库初始化完成")