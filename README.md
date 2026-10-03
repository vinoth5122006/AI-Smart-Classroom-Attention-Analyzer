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

## How the Multi-Student Classroom Works

```
                        +-------------------------------------------------------+
                        | STUDENT DEVICES |
                        | (Laptops, Tablets, Phones via /join?room=CS-101) |
                        +-------------------------------------------------------+
                                   | |
           MediaPipe Edge Mesh | | MediaPipe Edge Mesh
           (Local Camera Sensor) | | (Local Camera Sensor)
                                   v v
                        [WebSocket: /ws/student/CS-101/STU-1] [WebSocket: /ws/student/CS-101/STU-2]
                                   \ /
                                    \ /
                                     v v
                        +-------------------------------------------------------+
                        | FASTAPI CLASSROOM ENGINE |
                        | - Per-Student Attention Engine State Machine |
                        | - Aggregated Cohort Telemetry Broker |
                        | - SQLite Session & Audit Persistence |
                        +-------------------------------------------------------+
                                                   |
                                     WebSocket: /ws/admin/CS-101
                                                   |
                                                   v
                        +-------------------------------------------------------+
                        | INSTRUCTOR CONSOLE |
                        | - Live Student Roster Cards with Attention Dials |
                        | - Classroom Seating Heatmap Visualizer |
                        | - Audio Chime Alerts for Drowsiness & Phone Usage |
                        | - One-Click PDF, Excel, and CSV Report Generator |
                        +-------------------------------------------------------+
```

1. **Instructor launches the console:** Navigates to `http://localhost:8000`, copies the student invite link or displays the room code (`CS-101`).
2. **Students open the invite link:** In any standard web browser (Chrome, Edge, Safari, Firefox). Students enter their name and desk identifier.
3. **Edge AI Activation:** The student's browser requests webcam access and runs MediaPipe FaceMesh locally. Only numerical telemetry (gaze vector, ocular openness, blink frequency) is streamed over WebSocket.
4. **Instructor Observability:** The instructor's dashboard updates in real time, displaying student cards with animated dials, classroom seating heatmap, and behavioral classification.
5. **Session Finalization:** Clicking "Stop Session" commits attendance records and telemetry to SQLite and enables instant download of executive PDF reports.

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

## Cloud Deployment Guide

### Option 1: Hugging Face Spaces (100% Free Docker Hosting)
1. Fork or push this repository to GitHub.
2. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click **Create new Space**.
3. Choose **Docker** as Space SDK (Blank).
4. Connect your repo. Hugging Face automatically detects the `Dockerfile` on port `7860`.

### Option 2: Render (Free Web Service)
1. In [Render Dashboard](https://dashboard.render.com), click **New +** &rarr; **Web Service**.
2. Select your repository. Environment: **Docker**.
3. Render automatically provisions HTTPS and binds `$PORT`.

### Option 3: Google Cloud Run / AWS App Runner / Railway
```bash
docker build -t synapse-ai-classroom .
docker run -p 8000:7860 synapse-ai-classroom
```

---

## Repository Structure

```text
AI-Smart-Classroom-Attention-Analyzer/
├── app.py # Master launcher (supports Web and Desktop GUI)
├── web_app.py # Enterprise FastAPI + WebSockets application server
├── dashboard.py # Desktop GUI module (CustomTkinter)
├── Dockerfile # Multi-stage production container configuration
├── render.yaml # 1-click cloud deployment specification
├── requirements-web.txt # Lightweight cloud dependencies
├── requirements.txt # Full local dependencies (including YOLO / PyTorch)
├── .env.example # Environment variables template
├── .github/
│ └── workflows/deploy.yml # CI/CD automated lint, test, and container build
├── templates/
│ ├── index.html # Flagship Console: Splash intro, landing page, multi-student matrix
│ └── student.html # Distraction-free student portal
├── modules/
│ ├── __init__.py # Package initializer
│ ├── attention_engine.py # Behavior intelligence state machine & scoring engine
│ ├── classroom_manager.py # Multi-student room broker & real-time telemetry registry
│ ├── database.py # SQLite persistence for sessions, attendance, and audit logs
│ ├── auth.py # Admin HMAC-SHA256 session token authentication
│ ├── pdf_generator.py # Executive assessment report generator (PDF/Print)
│ ├── logger.py # Structured JSON & console logger
│ ├── face_detection.py # Desktop OpenCV/MediaPipe pipeline
│ └── phone_detector.py # YOLOv8 object detector for phone usage
└── data/ # Directory for SQLite database (created automatically)
```
