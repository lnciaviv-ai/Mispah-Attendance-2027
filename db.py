#!/usr/bin/env python3
"""Database layer for Mispah School Daily Attendance System."""

import sqlite3
import hashlib
import os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attendance.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'teacher')),
        class_id INTEGER,
        FOREIGN KEY (class_id) REFERENCES classes(id)
    );

    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        teacher_name TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS learners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        gender TEXT NOT NULL CHECK(gender IN ('seun', 'dogter')),
        active INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (class_id) REFERENCES classes(id)
    );

    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attendance_date TEXT NOT NULL,  -- YYYY-MM-DD
        class_id INTEGER NOT NULL,
        learner_id INTEGER NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('present', 'absent')),
        marked_by INTEGER,
        marked_at TEXT,
        UNIQUE(attendance_date, learner_id),
        FOREIGN KEY (class_id) REFERENCES classes(id),
        FOREIGN KEY (learner_id) REFERENCES learners(id),
        FOREIGN KEY (marked_by) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS daily_signatures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attendance_date TEXT NOT NULL,
        class_id INTEGER NOT NULL,
        signed_by INTEGER,
        signed_at TEXT,
        UNIQUE(attendance_date, class_id),
        FOREIGN KEY (class_id) REFERENCES classes(id),
        FOREIGN KEY (signed_by) REFERENCES users(id)
    );
    """)

    # Seed classes (from the paper register)
    classes = [
        (1, "Multi-Graad 3", "Mev. RM Maree", 1),
        (2, "Multi-Graad 4.1", "Me. F Cupido", 2),
        (3, "Multi-Graad 4.2", "Me. BV Hess", 3),
        (4, "Multi-Graad 5.1", "Mnr. L Veroni", 4),
        (5, "Multi-Graad 5.2(A)", "Mnr. AA April", 5),
        (6, "Multi-Graad 5.2(B)", "Mnr. AL Fisher", 6),
        (7, "Multi-Graad 5.3", "Mev. SH Van Dyk", 7),
    ]
    for c in classes:
        cur.execute(
            "INSERT OR IGNORE INTO classes (id, name, teacher_name, sort_order) VALUES (?,?,?,?)",
            c,
        )

    # Seed users
    # Admin
    cur.execute(
        "INSERT OR IGNORE INTO users (username, password_hash, full_name, role, class_id) VALUES (?,?,?,?,?)",
        ("admin", hash_password("admin123"), "Administrator", "admin", None),
    )
    # Teachers (one per class) – password is the class short name for easy login
    teachers = [
        ("maree", "Mev. RM Maree", 1),
        ("cupido", "Me. F Cupido", 2),
        ("hess", "Me. BV Hess", 3),
        ("veroni", "Mnr. L Veroni", 4),
        ("april", "Mnr. AA April", 5),
        ("fisher", "Mnr. AL Fisher", 6),
        ("vandyk", "Mev. SH Van Dyk", 7),
    ]
    for username, full_name, class_id in teachers:
        cur.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, full_name, role, class_id) VALUES (?,?,?,?,?)",
            (username, hash_password("teacher123"), full_name, "teacher", class_id),
        )

    # Sample learners (realistic placeholders – admin can edit)
    sample_learners = [
        # Multi-Graad 3
        (1, "Jade", "G", "dogter"),
        (1, "Ronald", "K", "seun"),
        (1, "Damian", "M", "seun"),
        # Multi-Graad 4.1
        (2, "Cameron", "M", "seun"),
        (2, "Joshua", "C", "seun"),
        (2, "Dillon", "W", "seun"),
        (2, "Feralo", "D", "seun"),
        # Multi-Graad 4.2
        (3, "Damian", "J", "seun"),
        (3, "Muyo", "M", "seun"),
        (3, "Courtney", "T", "dogter"),
        # Multi-Graad 5.1
        (4, "Jade", "P", "dogter"),
        (4, "Putannes", "S", "dogter"),
        (4, "Adria", "A", "dogter"),
        # Multi-Graad 5.2(A)
        (5, "Liam", "B", "seun"),
        (5, "Ethan", "S", "seun"),
        (5, "Mia", "K", "dogter"),
        # Multi-Graad 5.2(B)
        (6, "Noah", "P", "seun"),
        (6, "Ava", "R", "dogter"),
        (6, "Oliver", "T", "seun"),
        # Multi-Graad 5.3
        (7, "Sophia", "L", "dogter"),
        (7, "Lucas", "M", "seun"),
        (7, "Emma", "J", "dogter"),
        (7, "James", "H", "seun"),
        (7, "Isabella", "V", "dogter"),
    ]
    for class_id, first, last, gender in sample_learners:
        cur.execute(
            """INSERT OR IGNORE INTO learners (class_id, first_name, last_name, gender)
               SELECT ?,?,?,? WHERE NOT EXISTS (
                   SELECT 1 FROM learners WHERE class_id=? AND first_name=? AND last_name=?
               )""",
            (class_id, first, last, gender, class_id, first, last),
        )

    conn.commit()
    conn.close()
    print("Database initialised:", DB_PATH)

# ---------- User helpers ----------
def authenticate(username: str, password: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE username=? AND password_hash=?",
        (username.strip().lower(), hash_password(password)),
    )
    user = cur.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

# ---------- Class helpers ----------
def get_all_classes():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM classes ORDER BY sort_order, name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_class(class_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM classes WHERE id=?", (class_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

# ---------- Learner helpers ----------
def get_learners_by_class(class_id: int, active_only: bool = True):
    conn = get_conn()
    cur = conn.cursor()
    if active_only:
        cur.execute(
            "SELECT * FROM learners WHERE class_id=? AND active=1 ORDER BY last_name, first_name",
            (class_id,),
        )
    else:
        cur.execute(
            "SELECT * FROM learners WHERE class_id=? ORDER BY last_name, first_name",
            (class_id,),
        )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_all_learners(active_only: bool = True):
    conn = get_conn()
    cur = conn.cursor()
    sql = """
        SELECT l.*, c.name AS class_name
        FROM learners l
        JOIN classes c ON c.id = l.class_id
    """
    if active_only:
        sql += " WHERE l.active=1"
    sql += " ORDER BY c.sort_order, l.last_name, l.first_name"
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def add_learner(class_id: int, first_name: str, last_name: str, gender: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO learners (class_id, first_name, last_name, gender) VALUES (?,?,?,?)",
        (class_id, first_name.strip(), last_name.strip(), gender),
    )
    conn.commit()
    lid = cur.lastrowid
    conn.close()
    return lid

def update_learner(learner_id: int, class_id: int, first_name: str, last_name: str, gender: str, active: int = 1):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """UPDATE learners SET class_id=?, first_name=?, last_name=?, gender=?, active=?
           WHERE id=?""",
        (class_id, first_name.strip(), last_name.strip(), gender, active, learner_id),
    )
    conn.commit()
    conn.close()

def deactivate_learner(learner_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE learners SET active=0 WHERE id=?", (learner_id,))
    conn.commit()
    conn.close()

# ---------- Attendance helpers ----------
def save_attendance(attendance_date: str, class_id: int, records: list, user_id: int):
    """
    records = list of dicts: {"learner_id": int, "status": "present"|"absent"}
    """
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    for rec in records:
        cur.execute(
            """INSERT INTO attendance (attendance_date, class_id, learner_id, status, marked_by, marked_at)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(attendance_date, learner_id)
               DO UPDATE SET status=excluded.status, marked_by=excluded.marked_by, marked_at=excluded.marked_at""",
            (attendance_date, class_id, rec["learner_id"], rec["status"], user_id, now),
        )
    # Mark as signed
    cur.execute(
        """INSERT INTO daily_signatures (attendance_date, class_id, signed_by, signed_at)
           VALUES (?,?,?,?)
           ON CONFLICT(attendance_date, class_id)
           DO UPDATE SET signed_by=excluded.signed_by, signed_at=excluded.signed_at""",
        (attendance_date, class_id, user_id, now),
    )
    conn.commit()
    conn.close()

def get_attendance_for_class(attendance_date: str, class_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT a.*, l.first_name, l.last_name, l.gender
           FROM attendance a
           JOIN learners l ON l.id = a.learner_id
           WHERE a.attendance_date=? AND a.class_id=?""",
        (attendance_date, class_id),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_full_daily_register(attendance_date: str):
    """Returns list of class summaries with counts and absent names – mirrors the paper form."""
    classes = get_all_classes()
    result = []
    conn = get_conn()
    cur = conn.cursor()

    for cls in classes:
        # Total active learners by gender
        cur.execute(
            """SELECT gender, COUNT(*) as cnt FROM learners
               WHERE class_id=? AND active=1 GROUP BY gender""",
            (cls["id"],),
        )
        gender_counts = {r["gender"]: r["cnt"] for r in cur.fetchall()}
        seuns_total = gender_counts.get("seun", 0)
        dogters_total = gender_counts.get("dogter", 0)

        # Attendance for the day
        cur.execute(
            """SELECT a.status, l.first_name, l.last_name, l.gender
               FROM attendance a
               JOIN learners l ON l.id = a.learner_id
               WHERE a.attendance_date=? AND a.class_id=? AND l.active=1""",
            (attendance_date, cls["id"]),
        )
        att_rows = cur.fetchall()

        present_seuns = present_dogters = 0
        absent_names = []
        marked = False
        for r in att_rows:
            marked = True
            if r["status"] == "present":
                if r["gender"] == "seun":
                    present_seuns += 1
                else:
                    present_dogters += 1
            else:
                absent_names.append(f"{r['first_name']} {r['last_name']}")

        # If nothing marked yet, treat as not submitted
        if not marked:
            seuns = dogters = total = None
            absent_names = []
            signed = False
        else:
            seuns = present_seuns
            dogters = present_dogters
            total = seuns + dogters
            # Signature
            cur.execute(
                "SELECT * FROM daily_signatures WHERE attendance_date=? AND class_id=?",
                (attendance_date, cls["id"]),
            )
            sig = cur.fetchone()
            signed = bool(sig)

        result.append({
            "class": cls,
            "seuns": seuns,
            "dogters": dogters,
            "totaal": total,
            "absent_names": absent_names,
            "signed": signed,
            "learners_total": seuns_total + dogters_total,
            "seuns_enrolled": seuns_total,
            "dogters_enrolled": dogters_total,
        })

    conn.close()
    return result

def get_class_attendance_detail(attendance_date: str, class_id: int):
    """Full list of learners + their status for a class on a date."""
    learners = get_learners_by_class(class_id)
    att = {a["learner_id"]: a["status"] for a in get_attendance_for_class(attendance_date, class_id)}
    for l in learners:
        l["status"] = att.get(l["id"], None)  # None = not yet marked
    return learners

if __name__ == "__main__":
    init_db()
    print("Done.")
