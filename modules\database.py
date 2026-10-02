"""
Database Module for AI Smart Classroom Attention Analyzer.
Provides lightweight, reliable SQLite storage for classroom sessions, student roster telemetry,
attendance history, and audit logs.
"""

import os
import sqlite3
import datetime
import json
from typing import List, Dict, Any, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "classroom_analyzer.db")

def init_db():
    """Initializes tables if they do not exist."""
    os.makedirs(DB_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Classrooms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classrooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                instructor_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_uuid TEXT UNIQUE NOT NULL,
                room_code TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_seconds INTEGER DEFAULT 0,
                avg_attention REAL DEFAULT 0.0,
                max_attention REAL DEFAULT 0.0,
                min_attention REAL DEFAULT 0.0,
                total_students INTEGER DEFAULT 0,
                drowsiness_count INTEGER DEFAULT 0,
                phone_usage_count INTEGER DEFAULT 0,
                state_changes INTEGER DEFAULT 0,
                metrics_json TEXT
            )
        """)
        
        # Student attendance and final metrics record
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_uuid TEXT NOT NULL,
                room_code TEXT NOT NULL,
                student_id TEXT NOT NULL,
                student_name TEXT NOT NULL,
                desk_position TEXT,
                avg_attention REAL DEFAULT 0.0,
                drowsiness_count INTEGER DEFAULT 0,
                phone_usage_count INTEGER DEFAULT 0,
                blink_count INTEGER DEFAULT 0,
                final_status TEXT DEFAULT 'Attentive',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                left_at TIMESTAMP
            )
        """)
        
        # Audit logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_uuid TEXT,
                room_code TEXT NOT NULL,
                student_id TEXT,
                student_name TEXT,
                timestamp TEXT NOT NULL,
                old_state TEXT,
                new_state TEXT,
                behavior TEXT,
                score INTEGER,
                confidence INTEGER,
                reason TEXT
            )
        """)
        
        conn.commit()

# Ensure database tables exist on module import
init_db()

def get_or_create_classroom(room_code: str, title: str = "General Lecture", instructor: str = "Lead Instructor") -> Dict[str, Any]:
    """Retrieves or creates a classroom record."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM classrooms WHERE room_code = ?", (room_code,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        
        cursor.execute(
            "INSERT INTO classrooms (room_code, title, instructor_name) VALUES (?, ?, ?)",
            (room_code, title, instructor)
        )
        conn.commit()
        cursor.execute("SELECT * FROM classrooms WHERE room_code = ?", (room_code,))
        return dict(cursor.fetchone())

def list_classrooms() -> List[Dict[str, Any]]:
    """Lists all active classrooms."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM classrooms ORDER BY created_at DESC")
        return [dict(r) for r in cursor.fetchall()]

def save_session_record(session_data: Dict[str, Any]) -> int:
    """Saves completed session analytics record."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sessions (
                session_uuid, room_code, start_time, end_time, duration_seconds,
                avg_attention, max_attention, min_attention, total_students,
                drowsiness_count, phone_usage_count, state_changes, metrics_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_data.get("session_uuid"),
            session_data.get("room_code", "DEFAULT"),
            session_data.get("start_time"),
            session_data.get("end_time"),
            session_data.get("duration_seconds", 0),
            session_data.get("avg_attention", 0.0),
            session_data.get("max_attention", 0.0),
            session_data.get("min_attention", 0.0),
            session_data.get("total_students", 1),
            session_data.get("drowsiness_count", 0),
            session_data.get("phone_usage_count", 0),
            session_data.get("state_changes", 0),
            json.dumps(session_data.get("metrics", {}))
        ))
        conn.commit()
        return cursor.lastrowid

def record_student_session(student_data: Dict[str, Any]):
    """Records individual student performance in a session."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO student_records (
                session_uuid, room_code, student_id, student_name, desk_position,
                avg_attention, drowsiness_count, phone_usage_count, blink_count, final_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_data.get("session_uuid", "CURRENT"),
            student_data.get("room_code", "DEFAULT"),
            student_data.get("student_id", "STU-000"),
            student_data.get("student_name", "Anonymous Student"),
            student_data.get("desk_position", "A-01"),
            student_data.get("avg_attention", 0.0),
            student_data.get("drowsiness_count", 0),
            student_data.get("phone_usage_count", 0),
            student_data.get("blink_count", 0),
            student_data.get("final_status", "Attentive")
        ))
        conn.commit()

def record_audit_event(event: Dict[str, Any]):
    """Persists behavioral transition audit event."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (
                session_uuid, room_code, student_id, student_name, timestamp,
                old_state, new_state, behavior, score, confidence, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.get("session_uuid", "LIVE"),
            event.get("room_code", "DEFAULT"),
            event.get("student_id", "STU-001"),
            event.get("student_name", "Student"),
            event.get("timestamp", datetime.datetime.now().strftime("%H:%M:%S")),
            event.get("old_state", "INITIAL"),
            event.get("new_state", "ATTENTIVE"),
            event.get("behavior", "ATTENTIVE"),
            int(event.get("score", 100)),
            int(event.get("confidence", 95)),
            event.get("reason", "")
        ))
        conn.commit()

def get_recent_audit_logs(room_code: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves recent chronological audit records."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if room_code:
            cursor.execute(
                "SELECT * FROM audit_logs WHERE room_code = ? ORDER BY id DESC LIMIT ?",
                (room_code, limit)
            )
        else:
            cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]

def get_sessions_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Returns list of past session reports."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]
