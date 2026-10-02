# Synapse AI &bull; Smart Classroom Attention Telemetry & Analytics (v3.0 Enterprise)

A production-ready Computer Vision and Behavioral Intelligence platform designed to monitor and analyze student attention levels across physical, hybrid, and remote classrooms in real-time.

It leverages **browser-side facial mesh telemetry, gaze vector estimation, ocular aperture tracking, and rule-based temporal state machines** to compute individual and cohort attention metrics, detect drowsiness or phone distractions, and generate executive academic assessment reports.

---

## Key Features & Architectural Highlights

* **Cinematic YouTube-Style Intro Splash:** Fluid branding animation on first launch, smoothly transitioning into a modern SaaS landing showcase.
* **Admin / Instructor Portal & Authentication:**
  * Secure HMAC-SHA256 session token authentication (`admin` / `smartclass2026`).
  * Real-time Multi-Student Classroom Matrix with individual animated SVG attention dials and webcam thumbnails.
  * Classroom Seating Engagement Heatmap (2D visual grid).
  * Synthesized Web Audio chime alerts for prolonged eye closures or unauthorized phone distractions.
* **Distraction-Free Student Portal (`/join`):**
  * One-click classroom join link generation (e.g. `http://localhost:8000/join?room=CS-101`).
  * In-browser MediaPipe FaceMesh runs at the edge; video is processed on the student's device and never broadcasted publicly, keeping student privacy intact while streaming only behavioral telemetry to the teacher.
  * **Students only see a clean, focused screen without distracting charts or attention percentages.**
* **Zero Server GPU Lag:** Facial telemetry runs client-side inside each student's browser canvas, making server hosting 100% free and lightweight on CPU.
* **Multi-Format Export & Archival:**
  * Instant download of ISO-8601 compliant **Executive Assessment Reports (PDF)** with university styling.
  * Structured Excel Workbooks (`.xls`) and Raw Telemetry Datasets (`.csv`).
* **Persistent SQLite Database:**
  * Automatically archives classroom sessions, attendance rosters, student performance summaries, and chronological audit logs into `data/classroom_analyzer.db`.
* **Theme Engine & Accessibility:**
  * Dark Mode (Deep OLED Navy) and High-Contrast Light Mode with instant toggle and `localStorage` persistence.
  * Full Keyboard Shortcut navigation (`Space` to Start/Stop, `1-5` for tabs, `T` for theme, `C` to copy link, `?` for shortcuts).
* **DevOps & Cloud-Ready:**
  * Multi-stage `Dockerfile` with dynamic cloud port detection (`$PORT`), readiness probes (`/api/ready`), and GitHub Actions CI/CD workflow.

---

## Quick Start (Local)

### 1. Install Dependencies
```bash
pip install -r requirements-web.txt
```
*(For local desktop GUI mode including YOLO phone detection, run: `pip install -r requirements.txt`)*

### 2. Launch the Application
```bash
python app.py
```
*Or directly via:*
```bash
python web_app.py
```

- **Instructor Dashboard:** [http://localhost:8000](http://localhost:8000)
- **Student Join Link:** [http://localhost:8000/join?room=CS-101](http://localhost:8000/join?room=CS-101)
- **Default Admin Credentials:** Username: `admin` | Password: `smartclass2026`

---



## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Space` | Start / Stop active session recording |
| `1` - `5` | Switch between Dashboard views (Landing, Classroom, Analytics, Roster, Config) |
| `T` | Toggle Dark / Light theme |
| `C` | Copy student classroom join link to clipboard |
| `?` | Open keyboard shortcuts help modal |
| `Esc` | Close any active modal dialog |

---


```
