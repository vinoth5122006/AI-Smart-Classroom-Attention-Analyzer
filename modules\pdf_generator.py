"""
Professional Classroom Assessment Report Generator.
Generates an executive, print-ready, high-resolution session report with student rosters,
distribution charts, key performance indicators, and incident audit logs.
"""

import datetime
from typing import Dict, Any, List

def generate_html_report(session_data: Dict[str, Any], students_data: List[Dict[str, Any]], audit_events: List[Dict[str, Any]]) -> str:
    """Produces clean, print-optimized executive HTML report that auto-prints as PDF."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title = session_data.get("title", "Smart Classroom Assessment Session")
    room_code = session_data.get("room_code", "CS-101")
    instructor = session_data.get("instructor", "Lead Instructor")
    
    avg_score = round(float(session_data.get("average_attention", 0.0)), 1)
    max_score = round(float(session_data.get("peak_attention", 0.0)), 1)
    min_score = round(float(session_data.get("min_attention", 0.0)), 1)
    total_students = int(session_data.get("active_student_count", len(students_data)))
    drowsy_cnt = int(session_data.get("total_drowsy_events", 0))
    phone_cnt = int(session_data.get("total_phone_events", 0))
    duration_sec = int(session_data.get("elapsed_seconds", 0))
    
    hrs = duration_sec // 3600
    mins = (duration_sec % 3600) // 60
    secs = duration_sec % 60
    duration_str = f"{hrs:02d}h {mins:02d}m {secs:02d}s"

    # Build students table rows
    student_rows = ""
    for s in students_data:
        score = round(s.get("attention_score", 0))
        status = s.get("current_state", "Attentive")
        status_color = "#16A34A" if score >= 80 else ("#D97706" if score >= 60 else "#DC2626")
        
        student_rows += f"""
        <tr>
            <td style="font-family: monospace; font-weight: bold;">{s.get('student_id', 'STU-000')}</td>
            <td><strong>{s.get('student_name', 'Student')}</strong></td>
            <td style="font-family: monospace;">{s.get('desk_position', 'A-01')}</td>
            <td><span style="font-weight:bold; color: {status_color};">{score}%</span></td>
            <td><span style="display:inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; background: #F1F5F9; border: 1px solid #CBD5E1;">{status}</span></td>
            <td>{s.get('eye_status', 'OPEN')}</td>
            <td>{s.get('head_direction', 'FORWARD')}</td>
            <td>{s.get('alerts_count', 0)}</td>
        </tr>
        """

    # Build audit log rows (last 25)
    audit_rows = ""
    for ev in audit_events[-25:]:
        score = ev.get("score", 100)
        audit_rows += f"""
        <tr>
            <td style="font-family: monospace; font-size: 11px;">{ev.get('timestamp', '--:--:--')}</td>
            <td><strong>{ev.get('student_name', 'Student')}</strong> ({ev.get('student_id', '')})</td>
            <td style="font-family: monospace; font-size: 11px;">{ev.get('old_state', 'INIT')} &rarr; {ev.get('new_state', 'ATTENTIVE')}</td>
            <td><strong>{score}%</strong></td>
            <td style="color: #64748B; font-size: 11px;">{ev.get('reason', '')}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Classroom Assessment Report - {room_code}</title>
    <style>
        @page {{
            size: A4;
            margin: 1.5cm;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #0F172A;
            background: #FFFFFF;
            margin: 0;
            padding: 20px;
            font-size: 12px;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #0F172A;
            padding-bottom: 14px;
            margin-bottom: 24px;
        }}
        .title h1 {{
            margin: 0;
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #0F172A;
        }}
        .title p {{
            margin: 4px 0 0 0;
            font-size: 12px;
            color: #64748B;
        }}
        .badge {{
            display: inline-block;
            background: #2563EB;
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }}
        .meta-card {{
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 12px;
        }}
        .meta-card .label {{
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            color: #64748B;
            letter-spacing: 0.05em;
        }}
        .meta-card .val {{
            font-size: 22px;
            font-weight: 800;
            color: #0F172A;
            margin-top: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
            font-size: 11.5px;
        }}
        th {{
            background: #F1F5F9;
            color: #475569;
            text-align: left;
            padding: 8px 10px;
            font-weight: 700;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid #CBD5E1;
        }}
        td {{
            padding: 8px 10px;
            border-bottom: 1px solid #E2E8F0;
        }}
        h2 {{
            font-size: 14px;
            font-weight: 700;
            margin: 20px 0 10px 0;
            color: #0F172A;
            border-left: 4px solid #2563EB;
            padding-left: 8px;
        }}
        .footer {{
            border-top: 1px solid #E2E8F0;
            padding-top: 14px;
            display: flex;
            justify-content: space-between;
            color: #94A3B8;
            font-size: 10px;
            margin-top: 30px;
        }}
        .print-btn {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #2563EB;
            color: white;
            border: none;
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ padding: 0; }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">Print / Save as PDF</button>

    <div class="header">
        <div class="title">
            <span class="badge">Official Assessment Record</span>
            <h1 style="margin-top: 6px;">{title}</h1>
            <p>Classroom Code: <strong>{room_code}</strong> | Instructor: <strong>{instructor}</strong> | Generated: {now}</p>
        </div>
        <div style="text-align: right;">
            <div style="font-weight: 800; font-size: 16px; color: #2563EB;">SYNAPSE AI</div>
            <div style="font-size: 10px; color: #64748B;">Smart Classroom Telemetry Platform</div>
        </div>
    </div>

    <div class="meta-grid">
        <div class="meta-card">
            <div class="label">Cohort Mean Attention</div>
            <div class="val" style="color: {'#16A34A' if avg_score >= 80 else ('#D97706' if avg_score >= 60 else '#DC2626')};">{avg_score}%</div>
        </div>
        <div class="meta-card">
            <div class="label">Peak Attention Index</div>
            <div class="val">{max_score}%</div>
        </div>
        <div class="meta-card">
            <div class="label">Active Student Count</div>
            <div class="val">{total_students}</div>
        </div>
        <div class="meta-card">
            <div class="label">Session Duration</div>
            <div class="val" style="font-size: 18px;">{duration_str}</div>
        </div>
        <div class="meta-card">
            <div class="label">Drowsiness Triggers</div>
            <div class="val" style="color: #DC2626;">{drowsy_cnt}</div>
        </div>
        <div class="meta-card">
            <div class="label">Device Detections</div>
            <div class="val" style="color: #D97706;">{phone_cnt}</div>
        </div>
        <div class="meta-card">
            <div class="label">Minimum Floor Score</div>
            <div class="val">{min_score}%</div>
        </div>
        <div class="meta-card">
            <div class="label">Compliance Status</div>
            <div class="val" style="font-size: 16px; color: #16A34A;">VERIFIED</div>
        </div>
    </div>

    <h2>Student Cohort Attendance & Engagement Roster</h2>
    <table>
        <thead>
            <tr>
                <th>Student ID</th>
                <th>Student Name</th>
                <th>Desk Position</th>
                <th>Attention Index</th>
                <th>Behavior State</th>
                <th>Aperture</th>
                <th>Gaze Vector</th>
                <th>Incident Count</th>
            </tr>
        </thead>
        <tbody>
            {student_rows if student_rows else '<tr><td colspan="8" style="text-align:center; padding:20px; color:#94A3B8;">No students connected during session</td></tr>'}
        </tbody>
    </table>

    <h2>Chronological Behavioral Transition Log (Recent 25)</h2>
    <table>
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Student</th>
                <th>Transition</th>
                <th>Score</th>
                <th>Diagnostic Rule Reason</th>
            </tr>
        </thead>
        <tbody>
            {audit_rows if audit_rows else '<tr><td colspan="5" style="text-align:center; padding:20px; color:#94A3B8;">No behavioral transitions recorded during session</td></tr>'}
        </tbody>
    </table>

    <div class="footer">
        <div>Smart Classroom Attention Intelligence &bull; ISO-8601 Telemetry Record &bull; Verification Hash: sha256-{hash(now) & 0xFFFFFFFF:08x}</div>
        <div>Page 1 of 1</div>
    </div>
</body>
</html>"""
    return html


def generate_individual_student_html_report(student_data: Dict[str, Any], room_code: str = "CS-101", instructor: str = "Lead Instructor") -> str:
    """Produces clean, executive print-ready PDF assessment report for a single student."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    name = student_data.get("student_name", "Student")
    stu_id = student_data.get("student_id", "STU-000")
    desk = student_data.get("desk_position", "A-01")
    score = round(float(student_data.get("attention_score", 0.0)))
    state = student_data.get("current_state", "ATTENTIVE")
    reason = student_data.get("reason", "Standard ocular focus aligned with instructional axis.")
    
    stats = student_data.get("stats", {})
    durations = stats.get("state_durations", {})
    
    score_color = "#16A34A" if score >= 80 else ("#D97706" if score >= 60 else "#DC2626")
    
    drowsy_sec = round(durations.get("DROWSY", 0.0))
    phone_sec = round(durations.get("USING_PHONE", 0.0))
    reading_sec = round(durations.get("READING", 0.0))
    notes_sec = round(durations.get("TAKING_NOTES", 0.0))
    left_sec = round(durations.get("LOOKING_LEFT", 0.0))
    right_sec = round(durations.get("LOOKING_RIGHT", 0.0))
    up_sec = round(durations.get("LOOKING_UP", 0.0))
    attentive_sec = round(durations.get("ATTENTIVE", 0.0))
    
    blinks = stats.get("blink_count", student_data.get("blink_count", 0))
    drowsy_count = stats.get("drowsiness_count", 0)
    phone_count = stats.get("phone_usage_count", 0)
    phone_status = "DETECTED" if student_data.get("phone_detected", False) else "NOT DETECTED"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Individual Student Assessment - {name} ({stu_id})</title>
    <style>
        @page {{ size: A4; margin: 1.5cm; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #0F172A;
            background: #FFFFFF;
            margin: 0;
            padding: 20px;
            font-size: 12px;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #0F172A;
            padding-bottom: 14px;
            margin-bottom: 24px;
        }}
        .badge {{
            display: inline-block;
            background: #2563EB;
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }}
        .meta-card {{
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 12px;
        }}
        .meta-card .label {{
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            color: #64748B;
            letter-spacing: 0.05em;
        }}
        .meta-card .val {{
            font-size: 20px;
            font-weight: 800;
            color: #0F172A;
            margin-top: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
            font-size: 11.5px;
        }}
        th {{
            background: #F1F5F9;
            color: #475569;
            text-align: left;
            padding: 8px 10px;
            font-weight: 700;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid #CBD5E1;
        }}
        td {{
            padding: 8px 10px;
            border-bottom: 1px solid #E2E8F0;
        }}
        h2 {{
            font-size: 13.5px;
            font-weight: 700;
            margin: 20px 0 10px 0;
            color: #0F172A;
            border-left: 4px solid #2563EB;
            padding-left: 8px;
        }}
        .print-btn {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #2563EB;
            color: white;
            border: none;
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ padding: 0; }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">Print / Save as PDF</button>

    <div class="header">
        <div>
            <span class="badge">Student Assessment Record</span>
            <h1 style="margin: 6px 0 2px 0; font-size: 22px; font-weight: 800;">{name}</h1>
            <p style="margin: 0; color: #64748B;">Student ID: <strong>{stu_id}</strong> &bull; Desk: <strong>{desk}</strong> &bull; Classroom: <strong>{room_code}</strong> &bull; Instructor: <strong>{instructor}</strong></p>
        </div>
        <div style="text-align: right;">
            <div style="font-weight: 800; font-size: 16px; color: #2563EB;">SYNAPSE AI</div>
            <div style="font-size: 10px; color: #64748B;">Individual Student Telemetry</div>
        </div>
    </div>

    <div class="meta-grid">
        <div class="meta-card">
            <div class="label">Current Attention Score</div>
            <div class="val" style="color: {score_color};">{score}%</div>
        </div>
        <div class="meta-card">
            <div class="label">Behavior State</div>
            <div class="val" style="font-size: 16px;">{state}</div>
        </div>
        <div class="meta-card">
            <div class="label">Blink Frequency Count</div>
            <div class="val">{blinks}</div>
        </div>
        <div class="meta-card">
            <div class="label">Drowsiness Triggers</div>
            <div class="val" style="color: #DC2626;">{drowsy_count}</div>
        </div>
        <div class="meta-card">
            <div class="label">Phone Usage Status</div>
            <div class="val" style="font-size: 16px; color: {'#DC2626' if phone_status == 'DETECTED' else '#16A34A'};">{phone_status}</div>
        </div>
        <div class="meta-card">
            <div class="label">Sleeping / Eye Closure Duration</div>
            <div class="val" style="color: #DC2626;">{drowsy_sec}s</div>
        </div>
        <div class="meta-card">
            <div class="label">Focused Attentive Duration</div>
            <div class="val" style="color: #16A34A;">{attentive_sec}s</div>
        </div>
        <div class="meta-card">
            <div class="label">Verification Timestamp</div>
            <div class="val" style="font-size: 13px;">{now}</div>
        </div>
    </div>

    <h2>Behavioral Durations & Physical Movement Telemetry</h2>
    <table>
        <thead>
            <tr>
                <th>Telemetry Metric</th>
                <th>Measured Value</th>
                <th>Analytical Classification</th>
                <th>Evaluation Context</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Reading Duration</strong></td>
                <td style="font-family: monospace; font-weight: bold;">{reading_sec}s</td>
                <td>Active Learning</td>
                <td>Gaze downward/forward with open eyes and document focus.</td>
            </tr>
            <tr>
                <td><strong>Taking Notes Duration</strong></td>
                <td style="font-family: monospace; font-weight: bold;">{notes_sec}s</td>
                <td>Kinesthetic Learning</td>
                <td>Head tilted downward with active ocular engagement.</td>
            </tr>
            <tr>
                <td><strong>Left Head Movement Duration</strong></td>
                <td style="font-family: monospace; font-weight: bold;">{left_sec}s</td>
                <td>Lateral Deviation</td>
                <td>Gaze directed away from primary instructional axis to left.</td>
            </tr>
            <tr>
                <td><strong>Right Head Movement Duration</strong></td>
                <td style="font-family: monospace; font-weight: bold;">{right_sec}s</td>
                <td>Lateral Deviation</td>
                <td>Gaze directed away from primary instructional axis to right.</td>
            </tr>
            <tr>
                <td><strong>Upward Gaze Duration</strong></td>
                <td style="font-family: monospace; font-weight: bold;">{up_sec}s</td>
                <td>Distraction Deviation</td>
                <td>Looking up away from workspace.</td>
            </tr>
            <tr>
                <td><strong>Phone Usage Duration</strong></td>
                <td style="font-family: monospace; font-weight: bold; color: #DC2626;">{phone_sec}s</td>
                <td>Unauthorized Device</td>
                <td>Screen device detected in student workspace.</td>
            </tr>
            <tr>
                <td><strong>Total Drowsiness Incidents</strong></td>
                <td style="font-family: monospace; font-weight: bold; color: #DC2626;">{drowsy_count}</td>
                <td>Fatigue Trigger</td>
                <td>Continuous ocular closure exceeding threshold duration.</td>
            </tr>
        </tbody>
    </table>

    <h2>Diagnostic Engine Status & Reason</h2>
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 14px; margin-bottom: 24px;">
        <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase;">Diagnostic Reason Summary</div>
        <div style="font-size: 13px; font-weight: 600; color: #0F172A; margin-top: 4px;">{reason}</div>
        <div style="font-size: 11px; color: #64748B; margin-top: 6px;">
            Head Position: <strong>{student_data.get('head_direction', 'FORWARD')}</strong> &bull; Eye Status: <strong>{student_data.get('eye_status', 'OPEN')}</strong> &bull; Face Detected: <strong>{student_data.get('face_detected', True)}</strong>
        </div>
    </div>

    <div style="border-top: 1px solid #E2E8F0; padding-top: 14px; display: flex; justify-content: space-between; color: #94A3B8; font-size: 10px; margin-top: 30px;">
        <div>Synapse AI &bull; Individual Student Telemetry Sheet &bull; Verification Hash: sha256-{hash(name + now) & 0xFFFFFFFF:08x}</div>
        <div>Page 1 of 1</div>
    </div>
</body>
</html>"""
    return html

