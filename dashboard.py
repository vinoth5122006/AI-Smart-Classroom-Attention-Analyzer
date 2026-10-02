"""
Module 6 - Teacher Analytics Dashboard
Pure GUI module. All computer vision processing is delegated to face_detection.py.
This module only displays pre-processed data received via a thread-safe queue.
"""

import time
import queue
import threading
import os
import datetime
import pandas as pd
import customtkinter as ctk
from PIL import Image, ImageDraw
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from modules.face_detection import run_face_detection_for_dashboard
from modules.attention_engine import AttentionEngine, StatisticsEngine


# ===================================================================
# ReportManager - Handles CSV and Excel report export
# ===================================================================
class ReportManager:
    """
    Handles file export of analytics reports to CSV and Excel format under the reports/ directory.
    """
    @staticmethod
    def export_report(stats_data):
        os.makedirs("reports", exist_ok=True)
        df = pd.DataFrame([stats_data])

        csv_path = "reports/session_report.csv"
        df.to_csv(csv_path, index=False)

        xlsx_path = "reports/session_report.xlsx"
        df.to_excel(xlsx_path, index=False)

        return csv_path, xlsx_path


# ===================================================================
# HeaderPanel - Title, date, and live clock
# ===================================================================
class HeaderPanel(ctk.CTkFrame):
    """
    Main header displaying project title, current date, time, and session indicators.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="#1C1C1E", corner_radius=15)

        self.title_label = ctk.CTkLabel(
            self,
            text=" AI Smart Classroom Analyzer",
            font=("Segoe UI", 24, "bold"),
            text_color="#0A84FF"
        )
        self.title_label.pack(side="left", padx=20, pady=15)

        self.time_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.time_frame.pack(side="right", padx=20, pady=15)

        self.date_lbl = ctk.CTkLabel(self.time_frame, text="", font=("Segoe UI", 14), text_color="#8E8E93")
        self.date_lbl.pack(side="left", padx=10)

        self.time_lbl = ctk.CTkLabel(self.time_frame, text="", font=("Segoe UI", 14, "bold"), text_color="#EBEBF5")
        self.time_lbl.pack(side="left", padx=10)

        self.update_time()

    def update_time(self):
        now = datetime.datetime.now()
        self.date_lbl.configure(text=now.strftime("%Y-%m-%d"))
        self.time_lbl.configure(text=now.strftime("%H:%M:%S"))
        self.after(1000, self.update_time)


# ===================================================================
# CameraPanel - Embeds the live camera feed from face_detection.py
# ===================================================================
class CameraPanel(ctk.CTkFrame):
    """
    Embeds the live OpenCV camera feed inside the CustomTkinter window.
    Does NOT perform any computer vision — only displays pre-processed RGB frames.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="#1C1C1E", corner_radius=15)

        self.title_label = ctk.CTkLabel(self, text="Live Camera Feed", font=("Segoe UI", 18, "bold"), text_color="white")
        self.title_label.pack(anchor="w", padx=20, pady=10)

        self.video_label = ctk.CTkLabel(self, text="", fg_color="#0F0F13", corner_radius=10)
        self.video_label.pack(expand=True, fill="both", padx=20, pady=(0, 20))

        self.show_placeholder()

    def show_placeholder(self):
        placeholder_image = Image.new("RGB", (640, 480), "#0F0F13")
        draw = ImageDraw.Draw(placeholder_image)
        draw.text((220, 230), "CAMERA INACTIVE\nClick 'Start Session' to begin.", fill="#8E8E93")
        self.photo = ctk.CTkImage(light_image=placeholder_image, size=(640, 480))
        self.video_label.configure(image=self.photo)

    def update_frame(self, rgb_frame):
        img = Image.fromarray(rgb_frame)
        self.photo = ctk.CTkImage(light_image=img, size=(640, 480))
        self.video_label.configure(image=self.photo)


# ===================================================================
# LiveInfoPanel - Displays real-time student metrics
# ===================================================================
class LiveInfoPanel(ctk.CTkFrame):
    """
    Displays current student behavior, attention levels, head poses, and other details.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="#1C1C1E", corner_radius=15)

        self.title_label = ctk.CTkLabel(self, text="Live Student Info", font=("Segoe UI", 18, "bold"), text_color="white")
        self.title_label.pack(anchor="w", padx=20, pady=10)

        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        fields = [
            ("Behavior", "ATTENTIVE", "behavior", "#FF453A"),
            ("Attention", "100%", "attention", "#30D158"),
            ("Head Direction", "FORWARD", "head", "#0A84FF"),
            ("Eye Status", "OPEN", "eyes", "#30D158"),
            ("Phone Status", "NOT DETECTED", "phone", "#30D158"),
            ("Blink Count", "0", "blinks", "#0A84FF"),
            ("Average Attention", "100%", "avg_att", "#30D158"),
            ("Session Time", "00:00:00", "session_time", "#FF9F0A"),
            ("Current FPS", "0.0", "fps", "#30D158")
        ]

        self.labels = {}
        for i, (label, val, key, color) in enumerate(fields):
            row_frame = ctk.CTkFrame(self.info_frame, fg_color="#2C2C2E", corner_radius=8)
            row_frame.pack(fill="x", pady=3)

            lbl = ctk.CTkLabel(row_frame, text=label, font=("Segoe UI", 12), text_color="#8E8E93")
            lbl.pack(side="left", padx=15, pady=5)

            val_lbl = ctk.CTkLabel(row_frame, text=val, font=("Segoe UI", 14, "bold"), text_color=color)
            val_lbl.pack(side="right", padx=15, pady=5)

            self.labels[key] = val_lbl

    def update_info(self, data):
        for key, val in data.items():
            if key in self.labels:
                self.labels[key].configure(text=str(val))
                if key == "phone":
                    if val == "DETECTED":
                        self.labels[key].configure(text_color="#FF453A")
                    else:
                        self.labels[key].configure(text_color="#30D158")
                elif key == "eyes":
                    if val == "CLOSED":
                        self.labels[key].configure(text_color="#FF453A")
                    else:
                        self.labels[key].configure(text_color="#30D158")
                elif key == "behavior":
                    if val == "ATTENTIVE":
                        self.labels[key].configure(text_color="#30D158")
                    elif val in ["USING_PHONE", "DROWSY", "ABSENT"]:
                        self.labels[key].configure(text_color="#FF453A")
                    else:
                        self.labels[key].configure(text_color="#FF9F0A")


# ===================================================================
# GraphPanel - Real-time Attention Score vs Time chart
# ===================================================================
class GraphPanel(ctk.CTkFrame):
    """
    Displays a real-time plot of student Attention Score vs Time using Matplotlib.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="#1C1C1E", corner_radius=15)

        self.title_label = ctk.CTkLabel(self, text="Attention Trend Analysis", font=("Segoe UI", 18, "bold"), text_color="white")
        self.title_label.pack(anchor="w", padx=20, pady=5)

        self.fig = Figure(figsize=(5, 2.5), dpi=100, facecolor='#1C1C1E')
        self.ax = self.fig.add_subplot(111)
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.x_data = []
        self.y_data = []

    def _style_axes(self):
        self.ax.set_facecolor('#1C1C1E')
        self.ax.spines['bottom'].set_color('#2C2C2E')
        self.ax.spines['top'].set_color('#1C1C1E')
        self.ax.spines['right'].set_color('#1C1C1E')
        self.ax.spines['left'].set_color('#2C2C2E')
        self.ax.tick_params(axis='x', colors='#8E8E93')
        self.ax.tick_params(axis='y', colors='#8E8E93')
        self.ax.set_ylim(0, 105)

    def update_graph(self, attention_score):
        self.y_data.append(attention_score)
        self.x_data.append(len(self.y_data))

        if len(self.y_data) > 60:
            self.y_data.pop(0)
            self.x_data.pop(0)

        self.ax.clear()
        self._style_axes()

        self.ax.plot(self.x_data, self.y_data, color='#0A84FF', linewidth=2)
        self.canvas.draw()

    def reset(self):
        self.x_data = []
        self.y_data = []
        self.ax.clear()
        self._style_axes()
        self.canvas.draw()


# ===================================================================
# ControlPanel - Session control buttons
# ===================================================================
class ControlPanel(ctk.CTkFrame):
    """
    Houses control buttons for starting, stopping, resetting, and exporting data.
    """
    def __init__(self, parent, callbacks, **kwargs):
        super().__init__(parent, **kwargs)
        self.callbacks = callbacks
        self.configure(fg_color="#1C1C1E", corner_radius=15)

        self.start_btn = ctk.CTkButton(self, text=" Start Session", command=self.callbacks["start"], fg_color="#30D158", hover_color="#28B84D", text_color="white", font=("Segoe UI", 14, "bold"), corner_radius=20)
        self.start_btn.pack(side="left", padx=15, pady=15)

        self.stop_btn = ctk.CTkButton(self, text=" Stop Session", command=self.callbacks["stop"], fg_color="#FF453A", hover_color="#E03A30", text_color="white", font=("Segoe UI", 14, "bold"), state="disabled", corner_radius=20)
        self.stop_btn.pack(side="left", padx=15, pady=15)

        self.reset_btn = ctk.CTkButton(self, text=" Reset Statistics", command=self.callbacks["reset"], fg_color="#FF9F0A", hover_color="#E08B08", text_color="white", font=("Segoe UI", 14, "bold"), corner_radius=20)
        self.reset_btn.pack(side="left", padx=15, pady=15)

        self.csv_btn = ctk.CTkButton(self, text=" Export CSV", command=self.callbacks["export_csv"], fg_color="#0A84FF", hover_color="#0974DF", text_color="white", font=("Segoe UI", 14, "bold"), corner_radius=20)
        self.csv_btn.pack(side="left", padx=15, pady=15)

        self.excel_btn = ctk.CTkButton(self, text=" Export Excel", command=self.callbacks["export_excel"], fg_color="#5E5CE6", hover_color="#5250D0", text_color="white", font=("Segoe UI", 14, "bold"), corner_radius=20)
        self.excel_btn.pack(side="left", padx=15, pady=15)

        self.exit_btn = ctk.CTkButton(self, text=" Exit", command=self.callbacks["exit"], fg_color="#8E8E93", hover_color="#7A7A7F", text_color="white", font=("Segoe UI", 14, "bold"), corner_radius=20)
        self.exit_btn.pack(side="left", padx=15, pady=15)

    def set_running_state(self, is_running):
        if is_running:
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        else:
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")


# ===================================================================
# StatisticsPanel - Bottom statistics cards grid
# ===================================================================
class StatisticsPanel(ctk.CTkFrame):
    """
    Bottom section grid displaying 13 cards with rounded corners.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="#1C1C1E", corner_radius=15)

        self.title_label = ctk.CTkLabel(self, text="Detailed Analytics Metrics", font=("Segoe UI", 18, "bold"), text_color="white")
        self.title_label.pack(anchor="w", padx=20, pady=10)

        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.cards = {}

        metrics = [
            ("Average Attention", "0%", "avg_att"),
            ("Maximum Attention", "0%", "max_att"),
            ("Minimum Attention", "0%", "min_att"),
            ("Phone Usage Count", "0", "phone_cnt"),
            ("Phone Usage Duration", "0s", "phone_dur"),
            ("Blink Count", "0", "blink_cnt"),
            ("Taking Notes Duration", "0s", "notes_dur"),
            ("Reading Duration", "0s", "reading_dur"),
            ("Looking Left Duration", "0s", "left_dur"),
            ("Looking Right Duration", "0s", "right_dur"),
            ("Looking Up Duration", "0s", "up_dur"),
            ("Drowsiness Count", "0", "drowsy_cnt"),
            ("Behavior Changes", "0", "changes_cnt")
        ]

        for i, (label, val, key) in enumerate(metrics):
            row = i // 5
            col = i % 5

            card = ctk.CTkFrame(self.grid_frame, fg_color="#2C2C2E", corner_radius=12, height=85)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            card.grid_propagate(False)

            lbl = ctk.CTkLabel(card, text=label, font=("Segoe UI", 12), text_color="#8E8E93")
            lbl.pack(pady=(12, 2))

            val_lbl = ctk.CTkLabel(card, text=val, font=("Segoe UI", 22, "bold"), text_color="#0A84FF")
            val_lbl.pack(pady=2)

            self.cards[key] = val_lbl

        for col in range(5):
            self.grid_frame.grid_columnconfigure(col, weight=1)

    def update_stats(self, stats):
        for key, val in stats.items():
            if key in self.cards:
                self.cards[key].configure(text=str(val))


# ===================================================================
# DashboardApp - Main application controller
# ===================================================================
class DashboardApp(ctk.CTk):
    """
    Main application orchestrating header, camera, statistics, controls, graphs, and threads.
    All computer vision is delegated to face_detection.py via a background thread.
    This class only consumes pre-processed data from a thread-safe queue.
    """
    def __init__(self):
        super().__init__()
        self.title("AI-Based Smart Classroom Attention Analyzer Dashboard")
        self.geometry("1450x900")
        self.configure(fg_color="#0F0F13")

        # Single shared AttentionEngine instance — passed to face_detection.py
        self.attention_engine = AttentionEngine()
        self.data_queue = queue.Queue(maxsize=5)
        self.stop_event = threading.Event()
        self.camera_thread = None

        self.session_active = False
        self.session_start_time = None
        self.total_attention_score = 0.0
        self.processed_frames_count = 0

        # Header Panel
        self.header = HeaderPanel(self)
        self.header.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="ew")

        # Camera Feed Panel
        self.camera_panel = CameraPanel(self)
        self.camera_panel.grid(row=1, column=0, padx=(15, 10), pady=10, sticky="nsew")

        # Right Frame
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=1, column=1, padx=(10, 15), pady=10, sticky="nsew")

        self.live_info = LiveInfoPanel(self.right_frame)
        self.live_info.pack(fill="x", pady=(0, 10))

        self.graph_panel = GraphPanel(self.right_frame)
        self.graph_panel.pack(fill="both", expand=True)

        # Bottom Frame
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, columnspan=2, padx=15, pady=(10, 15), sticky="ew")

        callbacks = {
            "start": self.start_session,
            "stop": self.stop_session,
            "reset": self.reset_statistics,
            "export_csv": self.export_csv,
            "export_excel": self.export_excel,
            "exit": self.exit_app
        }

        self.control_panel = ControlPanel(self.bottom_frame, callbacks)
        self.control_panel.pack(fill="x", pady=(0, 10))

        self.stats_panel = StatisticsPanel(self.bottom_frame)
        self.stats_panel.pack(fill="both", expand=True)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

        # Start GUI polling loop
        self.update_gui_loop()

    # -----------------------------------
    # Session Control Methods
    # -----------------------------------
    def start_session(self):
        if not self.session_active:
            self.session_active = True
            self.session_start_time = time.time()
            self.stop_event.clear()

            # Start the camera pipeline from face_detection.py in a background thread
            self.camera_thread = threading.Thread(
                target=run_face_detection_for_dashboard,
                args=(self.data_queue, self.attention_engine, self.stop_event),
                daemon=True
            )
            self.camera_thread.start()
            self.control_panel.set_running_state(True)
            print("Session started.")

    def stop_session(self):
        if self.session_active:
            self.session_active = False
            self.stop_event.set()
            if self.camera_thread:
                self.camera_thread.join(timeout=5)
                self.camera_thread = None
            self.control_panel.set_running_state(False)
            self.camera_panel.show_placeholder()

            # Auto-save report on session stop
            self.auto_export_reports()
            print("Session stopped.")

    def reset_statistics(self):
        self.total_attention_score = 0.0
        self.processed_frames_count = 0
        if self.session_active:
            self.session_start_time = time.time()

        # Reset the statistics engine inside the shared AttentionEngine
        self.attention_engine.statistics_engine = StatisticsEngine()

        self.graph_panel.reset()

        self.stats_panel.update_stats({
            "avg_att": "0%",
            "max_att": "0%",
            "min_att": "0%",
            "phone_cnt": "0",
            "phone_dur": "0s",
            "blink_cnt": "0",
            "notes_dur": "0s",
            "reading_dur": "0s",
            "left_dur": "0s",
            "right_dur": "0s",
            "up_dur": "0s",
            "drowsy_cnt": "0",
            "changes_cnt": "0"
        })

        self.live_info.update_info({
            "behavior": "ATTENTIVE",
            "attention": "100%",
            "head": "FORWARD",
            "eyes": "OPEN",
            "phone": "NOT DETECTED",
            "blinks": "0",
            "avg_att": "100%",
            "session_time": "00:00:00",
            "fps": "0.0"
        })
        print("Statistics reset.")

    # -----------------------------------
    # Report Export Methods
    # -----------------------------------
    def get_current_stats_data(self):
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")

        start_time_str = "00:00:00"
        if self.session_start_time:
            start_time_str = datetime.datetime.fromtimestamp(self.session_start_time).strftime("%H:%M:%S")
        end_time_str = now.strftime("%H:%M:%S")

        elapsed_seconds = 0
        if self.session_start_time:
            elapsed_seconds = int(time.time() - self.session_start_time)
        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60
        session_duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        avg_att = 0
        if self.processed_frames_count > 0:
            avg_att = int(self.total_attention_score / self.processed_frames_count)

        stats_engine = self.attention_engine.statistics_engine
        max_att = int(stats_engine.max_attention)
        min_att = int(stats_engine.min_attention) if stats_engine.min_attention != 100.0 else 0
        blink_count = int(stats_engine.blink_count)
        phone_usage_count = int(stats_engine.phone_usage_count)
        phone_usage_duration = int(stats_engine.state_durations.get("USING_PHONE", 0.0))
        reading_duration = int(stats_engine.state_durations.get("READING", 0.0))
        taking_notes_duration = int(stats_engine.state_durations.get("TAKING_NOTES", 0.0))
        looking_left_duration = int(stats_engine.state_durations.get("LOOKING_LEFT", 0.0))
        looking_right_duration = int(stats_engine.state_durations.get("LOOKING_RIGHT", 0.0))
        looking_up_duration = int(stats_engine.state_durations.get("LOOKING_UP", 0.0))
        drowsiness_count = int(stats_engine.drowsiness_count)
        behavior_transition_count = int(stats_engine.state_changes)

        return {
            "Date": date_str,
            "Start Time": start_time_str,
            "End Time": end_time_str,
            "Session Duration": session_duration_str,
            "Average Attention": f"{avg_att}%",
            "Maximum Attention": f"{max_att}%",
            "Minimum Attention": f"{min_att}%",
            "Blink Count": blink_count,
            "Phone Usage Count": phone_usage_count,
            "Phone Usage Duration": f"{phone_usage_duration}s",
            "Reading Duration": f"{reading_duration}s",
            "Taking Notes Duration": f"{taking_notes_duration}s",
            "Looking Left Duration": f"{looking_left_duration}s",
            "Looking Right Duration": f"{looking_right_duration}s",
            "Looking Up Duration": f"{looking_up_duration}s",
            "Drowsiness Count": drowsiness_count,
            "Behavior Transition Count": behavior_transition_count
        }

    def auto_export_reports(self):
        stats_data = self.get_current_stats_data()
        ReportManager.export_report(stats_data)

    def export_csv(self):
        stats_data = self.get_current_stats_data()
        csv_path, _ = ReportManager.export_report(stats_data)
        self.show_popup("Export Successful", f"Report successfully saved to:\n{csv_path}")

    def export_excel(self):
        stats_data = self.get_current_stats_data()
        _, xlsx_path = ReportManager.export_report(stats_data)
        self.show_popup("Export Successful", f"Report successfully saved to:\n{xlsx_path}")

    def show_popup(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("400x180")
        popup.grab_set()

        lbl = ctk.CTkLabel(popup, text=message, font=("Segoe UI", 12), justify="center")
        lbl.pack(pady=30, padx=20)

        btn = ctk.CTkButton(popup, text="OK", width=100, command=popup.destroy)
        btn.pack(pady=10)

    def exit_app(self):
        self.stop_session()
        self.destroy()

    # -----------------------------------
    # GUI Polling Loop - Consumes queue data from face_detection.py
    # -----------------------------------
    def update_gui_loop(self):
        latest_data = None
        frames_processed = 0

        while not self.data_queue.empty() and frames_processed < 5:
            try:
                data = self.data_queue.get_nowait()
                latest_data = data
                frames_processed += 1

                if self.session_active and data.analysis is not None:
                    self.total_attention_score += data.attention_score
                    self.processed_frames_count += 1
            except queue.Empty:
                break

        if latest_data is not None:
            self.camera_panel.update_frame(latest_data.frame)

            if self.session_active and latest_data.analysis is not None:
                # Update Graph once per tick
                self.graph_panel.update_graph(latest_data.attention_score)

                avg_att_score = self.total_attention_score / self.processed_frames_count

                elapsed_seconds = int(time.time() - self.session_start_time)
                hours = elapsed_seconds // 3600
                minutes = (elapsed_seconds % 3600) // 60
                seconds = elapsed_seconds % 60
                session_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                self.live_info.update_info({
                    "behavior": latest_data.behavior,
                    "attention": f"{int(latest_data.attention_score)}%",
                    "head": latest_data.head_direction,
                    "eyes": latest_data.eye_status,
                    "phone": "DETECTED" if latest_data.phone_detected else "NOT DETECTED",
                    "blinks": latest_data.blink_count,
                    "avg_att": f"{int(avg_att_score)}%",
                    "session_time": session_time_str,
                    "fps": f"{latest_data.fps:.1f}"
                })

                stats_engine = self.attention_engine.statistics_engine
                max_att = int(stats_engine.max_attention)
                min_att = int(stats_engine.min_attention) if stats_engine.min_attention != 100.0 else 0
                phone_cnt = int(stats_engine.phone_usage_count)
                phone_dur = int(stats_engine.state_durations.get("USING_PHONE", 0.0))
                notes_dur = int(stats_engine.state_durations.get("TAKING_NOTES", 0.0))
                reading_dur = int(stats_engine.state_durations.get("READING", 0.0))
                left_dur = int(stats_engine.state_durations.get("LOOKING_LEFT", 0.0))
                right_dur = int(stats_engine.state_durations.get("LOOKING_RIGHT", 0.0))
                up_dur = int(stats_engine.state_durations.get("LOOKING_UP", 0.0))
                drowsy_cnt = int(stats_engine.drowsiness_count)
                changes_cnt = int(stats_engine.state_changes)

                self.stats_panel.update_stats({
                    "avg_att": f"{int(avg_att_score)}%",
                    "max_att": f"{max_att}%",
                    "min_att": f"{min_att}%",
                    "phone_cnt": str(phone_cnt),
                    "phone_dur": f"{phone_dur}s",
                    "blink_cnt": str(latest_data.blink_count),
                    "notes_dur": f"{notes_dur}s",
                    "reading_dur": f"{reading_dur}s",
                    "left_dur": f"{left_dur}s",
                    "right_dur": f"{right_dur}s",
                    "up_dur": f"{up_dur}s",
                    "drowsy_cnt": str(drowsy_cnt),
                    "changes_cnt": str(changes_cnt)
                })

        self.after(15, self.update_gui_loop)


# ===================================================================
# Entry Point - Called from app.py
# ===================================================================
def run_dashboard():
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("green")
    app = DashboardApp()
    app.mainloop()
