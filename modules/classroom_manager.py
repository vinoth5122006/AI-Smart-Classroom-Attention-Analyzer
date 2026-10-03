"""
Multi-Student Classroom Real-Time Telemetry Manager.
Brokers WebSocket connections, maintains room state, isolates student attention engines,
and aggregates live classroom telemetry for admin consoles.
"""

import time
import datetime
import asyncio
from typing import Dict, List, Any, Optional, Set
from fastapi import WebSocket

from modules.attention_engine import AttentionEngine, StudentFeatures, Config
from modules.database import record_audit_event, record_student_session, save_session_record
from modules.logger import logger

class StudentSession:
    """Represents a connected student in a classroom."""
    def __init__(self, student_id: str, student_name: str, desk_position: str = "A-01", room_code: str = "DEFAULT"):
        self.student_id = student_id
        self.student_name = student_name
        self.desk_position = desk_position
        self.room_code = room_code
        self.joined_at = time.time()
        self.last_seen = time.time()
        self.websocket: Optional[WebSocket] = None
        
        # Dedicated Attention Engine instance for this student
        self.engine = AttentionEngine()
        self.last_analysis: Dict[str, Any] = {
            "attention_score": 100.0,
            "current_state": "ATTENTIVE",
            "current_behavior": "ATTENTIVE",
            "confidence": 95.0,
            "reason": "Facing instructional axis with focused gaze.",
            "head_direction": "FORWARD",
            "eye_status": "OPEN",
            "blink_count": 0,
            "phone_detected": False,
        }
        self.alerts_count = 0
        self.last_recorded_state = "INITIAL"
        self.last_frame_thumbnail: Optional[str] = None # Base64 thumbnail for admin preview (optional)

    def process_telemetry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes an incoming telemetry frame from the student's device."""
        self.last_seen = time.time()
        
        features = StudentFeatures(
            head_direction=data.get("head_direction", "FORWARD"),
            eye_status=data.get("eye_status", "OPEN"),
            phone_detected=data.get("phone_detected", False),
            blink_count=data.get("blink_count", 0),
            face_detected=data.get("face_detected", True),
            timestamp=data.get("timestamp", time.time())
        )
        
        analysis = self.engine.analyze(features)
        current_state = analysis["current_state"]
        
        # Store thumbnail if provided
        if "thumbnail" in data and data["thumbnail"]:
            self.last_frame_thumbnail = data["thumbnail"]
            
        # Detect state transition for audit event
        transition_event = None
        if self.last_recorded_state != current_state:
            transition_event = {
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                "student_id": self.student_id,
                "student_name": self.student_name,
                "desk_position": self.desk_position,
                "room_code": self.room_code,
                "old_state": self.last_recorded_state or "INITIAL",
                "new_state": current_state,
                "behavior": analysis["current_behavior"],
                "score": round(analysis["attention_score"]),
                "confidence": round(analysis["confidence"]),
                "reason": analysis["reason"]
            }
            if current_state in ["DROWSY", "USING_PHONE", "ABSENT"]:
                self.alerts_count += 1
            self.last_recorded_state = current_state

        self.last_analysis = {
            "student_id": self.student_id,
            "student_name": self.student_name,
            "desk_position": self.desk_position,
            "attention_score": round(analysis["attention_score"]),
            "current_state": current_state,
            "current_behavior": analysis["current_behavior"],
            "confidence": round(analysis["confidence"]),
            "reason": analysis["reason"],
            "behavior_duration": round(analysis["behavior_duration"], 1),
            "head_direction": features.head_direction,
            "eye_status": features.eye_status,
            "blink_count": features.blink_count,
            "phone_detected": features.phone_detected,
            "face_detected": features.face_detected,
            "alerts_count": self.alerts_count,
            "last_seen": self.last_seen,
            "thumbnail": self.last_frame_thumbnail,
            "stats": analysis["session_statistics"]
        }
        
        return {
            "analysis": self.last_analysis,
            "transition_event": transition_event
        }


class ClassroomRoom:
    """Represents a virtual classroom with multiple student streams and admin consoles."""
    def __init__(self, room_code: str, title: str = "General Lecture", instructor: str = "Lead Instructor"):
        self.room_code = room_code
        self.title = title
        self.instructor = instructor
        self.created_at = time.time()
        self.is_session_active = False
        self.session_start_time: Optional[float] = None
        self.session_uuid = f"sess_{room_code}_{int(time.time())}"
        
        self.students: Dict[str, StudentSession] = {}
        self.admin_websockets: Set[WebSocket] = set()
        self.monitor_websockets: Dict[str, Set[WebSocket]] = {}
        self.audit_events: List[Dict[str, Any]] = []

    def register_monitor_ws(self, student_id: str, ws: WebSocket):
        if student_id not in self.monitor_websockets:
            self.monitor_websockets[student_id] = set()
        self.monitor_websockets[student_id].add(ws)

    def unregister_monitor_ws(self, student_id: str, ws: WebSocket):
        if student_id in self.monitor_websockets:
            self.monitor_websockets[student_id].discard(ws)
            if not self.monitor_websockets[student_id]:
                del self.monitor_websockets[student_id]

    async def broadcast_to_student_monitors(self, student_id: str, payload: Dict[str, Any]):
        sockets = self.monitor_websockets.get(student_id)
        if not sockets:
            return
        text = None
        disconnected = []
        for ws in sockets:
            try:
                if text is None:
                    import json
                    text = json.dumps(payload)
                await ws.send_text(text)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            sockets.discard(ws)

    def start_session(self):
        """Starts recording a classroom session."""
        self.is_session_active = True
        self.session_start_time = time.time()
        self.session_uuid = f"sess_{self.room_code}_{int(time.time())}"
        self.audit_events.clear()

    def stop_session(self) -> Dict[str, Any]:
        """Stops the active session and aggregates summary for persistent storage."""
        self.is_session_active = False
        elapsed = int(time.time() - (self.session_start_time or time.time()))
        summary = self.get_classroom_summary()
        
        record = {
            "session_uuid": self.session_uuid,
            "room_code": self.room_code,
            "start_time": datetime.datetime.fromtimestamp(self.session_start_time or time.time()).strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": elapsed,
            "avg_attention": summary["average_attention"],
            "max_attention": summary["peak_attention"],
            "min_attention": summary["min_attention"],
            "total_students": len(self.students),
            "drowsiness_count": summary["total_drowsy_events"],
            "phone_usage_count": summary["total_phone_events"],
            "state_changes": len(self.audit_events),
            "metrics": summary
        }
        
        # Save session to DB
        try:
            save_session_record(record)
            for stu in self.students.values():
                record_student_session({
                    "session_uuid": self.session_uuid,
                    "room_code": self.room_code,
                    "student_id": stu.student_id,
                    "student_name": stu.student_name,
                    "desk_position": stu.desk_position,
                    "avg_attention": stu.last_analysis.get("attention_score", 0),
                    "drowsiness_count": stu.alerts_count,
                    "phone_usage_count": int(stu.last_analysis.get("phone_detected", False)),
                    "blink_count": stu.last_analysis.get("blink_count", 0),
                    "final_status": stu.last_analysis.get("current_state", "Attentive")
                })
        except Exception as e:
            logger.error(f"Error saving session record to DB: {e}")
            
        return record

    def get_or_create_student(self, student_id: str, student_name: str, desk_position: str = "A-01") -> StudentSession:
        if student_id not in self.students:
            self.students[student_id] = StudentSession(student_id, student_name, desk_position, self.room_code)
        else:
            self.students[student_id].student_name = student_name
            self.students[student_id].desk_position = desk_position
        return self.students[student_id]

    def remove_student(self, student_id: str):
        if student_id in self.students:
            del self.students[student_id]

    def get_classroom_summary(self) -> Dict[str, Any]:
        """Calculates real-time aggregated metrics across all active students."""
        now = time.time()
        active_students = [
            s for s in self.students.values()
            if (now - s.last_seen) < 15 # Seen in last 15 seconds
        ]
        
        if not active_students:
            return {
                "active_student_count": 0,
                "total_roster_count": len(self.students),
                "average_attention": 0.0,
                "peak_attention": 0.0,
                "min_attention": 0.0,
                "state_breakdown": {},
                "total_drowsy_events": 0,
                "total_phone_events": 0,
                "total_alerts": 0,
                "durations": {},
                "elapsed_seconds": int(now - (self.session_start_time or now)) if self.is_session_active else 0
            }
            
        scores = [s.last_analysis["attention_score"] for s in active_students]
        avg_score = round(sum(scores) / len(scores), 1)
        max_score = round(max(scores), 1)
        min_score = round(min(scores), 1)
        
        state_counts: Dict[str, int] = {}
        total_drowsy = 0
        total_phone = 0
        total_alerts = 0
        
        # Aggregated durations
        combined_durations: Dict[str, float] = {}
        
        for s in active_students:
            st = s.last_analysis.get("current_state", "ATTENTIVE")
            state_counts[st] = state_counts.get(st, 0) + 1
            
            stats = s.last_analysis.get("stats", {})
            total_drowsy += stats.get("drowsiness_count", 0)
            total_phone += stats.get("phone_usage_count", 0)
            total_alerts += s.alerts_count
            
            dur = stats.get("state_durations", {})
            for k, v in dur.items():
                combined_durations[k] = combined_durations.get(k, 0.0) + v

        return {
            "active_student_count": len(active_students),
            "total_roster_count": len(self.students),
            "average_attention": avg_score,
            "peak_attention": max_score,
            "min_attention": min_score,
            "state_breakdown": state_counts,
            "total_drowsy_events": total_drowsy,
            "total_phone_events": total_phone,
            "total_alerts": total_alerts,
            "durations": combined_durations,
            "elapsed_seconds": int(now - (self.session_start_time or now)) if self.is_session_active else 0
        }

    async def broadcast_to_admins(self, payload: Dict[str, Any]):
        """Transmits live telemetry to all connected admin consoles."""
        if not self.admin_websockets:
            return
            
        text = None
        disconnected = []
        for ws in self.admin_websockets:
            try:
                if text is None:
                    import json
                    text = json.dumps(payload)
                await ws.send_text(text)
            except Exception:
                disconnected.append(ws)
                
        for ws in disconnected:
            self.admin_websockets.discard(ws)


class ClassroomManager:
    """Singleton registry managing all virtual classrooms in the platform."""
    def __init__(self):
        self.rooms: Dict[str, ClassroomRoom] = {}
        # Pre-seed a default flagship classroom
        self.get_or_create_room("CS-101", title="Computer Science: AI & Deep Learning", instructor="Prof. Elena Vance")

    def get_or_create_room(self, room_code: str, title: str = "General Lecture", instructor: str = "Lead Instructor") -> ClassroomRoom:
        code = room_code.strip().upper()
        if code not in self.rooms:
            self.rooms[code] = ClassroomRoom(code, title, instructor)
        return self.rooms[code]

    def get_room(self, room_code: str) -> Optional[ClassroomRoom]:
        return self.rooms.get(room_code.strip().upper())

    def list_rooms(self) -> List[Dict[str, Any]]:
        return [
            {
                "room_code": r.room_code,
                "title": r.title,
                "instructor": r.instructor,
                "active_students": len(r.students),
                "is_active": r.is_session_active
            }
            for r in self.rooms.values()
        ]

classroom_manager = ClassroomManager()
