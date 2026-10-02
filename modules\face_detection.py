import cv2
import mediapipe as mp
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
try:
    from scipy.spatial import distance as dist
    def euclidean_dist(a, b):
        return dist.euclidean(a, b)
except ImportError:
    import math
    def euclidean_dist(a, b):
        return math.dist(a, b)
import queue
from modules.phone_detector import PhoneDetector
from modules.attention_engine import AttentionEngine, StudentFeatures

@dataclass
class FrameData:
    frame: Any
    fps: float
    face_detected: bool
    head_direction: str
    eye_status: str
    blink_count: int
    phone_detected: bool
    attention_score: float
    behavior: str
    analysis: Dict[str, Any]
    timestamp: float

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def eye_aspect_ratio(landmarks, eye):
    p1 = landmarks[eye[0]]
    p2 = landmarks[eye[1]]
    p3 = landmarks[eye[2]]
    p4 = landmarks[eye[3]]
    p5 = landmarks[eye[4]]
    p6 = landmarks[eye[5]]

    A = euclidean_dist((p2.x, p2.y), (p6.x, p6.y))
    B = euclidean_dist((p3.x, p3.y), (p5.x, p5.y))
    C = euclidean_dist((p1.x, p1.y), (p4.x, p4.y))

    return (A + B) / (2.0 * C)

def get_head_direction(face_landmarks):
    nose = face_landmarks.landmark[1]
    left_face = face_landmarks.landmark[234]
    right_face = face_landmarks.landmark[454]
    forehead = face_landmarks.landmark[10]
    chin = face_landmarks.landmark[152]

    x_center = (left_face.x + right_face.x) / 2
    y_center = (forehead.y + chin.y) / 2

    dx = nose.x - x_center
    dy = nose.y - y_center

    if dx > 0.05:
        return "RIGHT"
    elif dx < -0.05:
        return "LEFT"
    elif dy > 0.05:
        return "DOWN"
    elif dy < -0.05:
        return "UP"
    else:
        return "FORWARD"

class VisionProcessor:
    def __init__(self, attention_engine=None):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.phone_detector = PhoneDetector()
        self.attention_engine = attention_engine if attention_engine else AttentionEngine()
        self.cap = None
        self.face_mesh = None
        self.prev_time = 0
        self.blink_count = 0
        self.closed_frames = 0
        self.EAR_THRESHOLD = 0.22
        self.CONSEC_FRAMES = 3
        self.frame_count = 0
        self.phone_detected = False

    def initialize(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Cannot open webcam.")
            return False
        
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.prev_time = time.time()
        return True

    def process_frame(self, draw_landmarks=True) -> Optional[FrameData]:
        if not self.cap or not self.cap.isOpened():
            return None

        success, frame = self.cap.read()
        if not success:
            return None

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        self.frame_count += 1
        if self.frame_count % 5 == 0:
            self.phone_detected = self.phone_detector.detect_phone(frame)

        face_detected = False
        direction = "NONE"
        eye_status = "CLOSED"

        results = self.face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            face_detected = True
            for face_landmarks in results.multi_face_landmarks:
                direction = get_head_direction(face_landmarks)
                landmarks = face_landmarks.landmark
                
                leftEAR = eye_aspect_ratio(landmarks, LEFT_EYE)
                rightEAR = eye_aspect_ratio(landmarks, RIGHT_EYE)
                ear = (leftEAR + rightEAR) / 2

                if ear < self.EAR_THRESHOLD:
                    self.closed_frames += 1
                else:
                    if self.closed_frames >= self.CONSEC_FRAMES:
                        self.blink_count += 1
                    self.closed_frames = 0

                if self.closed_frames >= self.CONSEC_FRAMES:
                    eye_status = "CLOSED"
                else:
                    eye_status = "OPEN"

                if draw_landmarks:
                    self.mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                    )
                    self.mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
                    )
                    self.mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_IRISES,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_iris_connections_style()
                    )

        timestamp = time.time()
        features = StudentFeatures(
            head_direction=direction,
            eye_status=eye_status,
            phone_detected=self.phone_detected,
            blink_count=self.blink_count,
            face_detected=face_detected,
            timestamp=timestamp
        )
        analysis = self.attention_engine.analyze(features)

        current_time = time.time()
        fps = 1 / (current_time - self.prev_time) if self.prev_time != 0 else 0
        self.prev_time = current_time

        return FrameData(
            frame=frame,
            fps=fps,
            face_detected=face_detected,
            head_direction=direction,
            eye_status=eye_status,
            blink_count=self.blink_count,
            phone_detected=self.phone_detected,
            attention_score=analysis["attention_score"],
            behavior=analysis["current_behavior"],
            analysis=analysis,
            timestamp=timestamp
        )

    def release(self):
        if self.cap:
            self.cap.release()
        if self.face_mesh:
            self.face_mesh.close()

def run_face_detection():
    processor = VisionProcessor()
    if not processor.initialize():
        return

    session_start_time = time.time()
    total_attention_score = 0.0
    processed_frames_count = 0

    print("Starting Smart Classroom Attention Analyzer...")
    print("Press Q to quit.")

    while True:
        try:
            frame_data = processor.process_frame(draw_landmarks=True)
            if frame_data is None:
                break
            
            frame = frame_data.frame
            
            # Text overlays
            cv2.putText(frame, f"Head : {frame_data.head_direction}", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.putText(frame, f"Blinks : {frame_data.blink_count}", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            
            eye_color = (0, 0, 255) if frame_data.eye_status == "CLOSED" else (0, 255, 0)
            cv2.putText(frame, f"Eyes : {frame_data.eye_status}", (20, 210), cv2.FONT_HERSHEY_SIMPLEX, 1, eye_color, 2)
            
            if processor.closed_frames > 20:
                cv2.putText(frame, "DROWSINESS ALERT!", (20, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

            cv2.putText(frame, f"FPS : {int(frame_data.fps)}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            phone_text = "DETECTED" if frame_data.phone_detected else "NOT DETECTED"
            phone_color = (0, 0, 255) if frame_data.phone_detected else (0, 255, 0)
            cv2.putText(frame, f"Phone : {phone_text}", (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 1, phone_color, 2)
            
            cv2.putText(frame, f"Behavior : {frame_data.behavior}", (20, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
            cv2.putText(frame, f"Attention : {int(frame_data.attention_score)}%", (20, 290), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            elapsed_seconds = int(time.time() - session_start_time)
            hours = elapsed_seconds // 3600
            minutes = (elapsed_seconds % 3600) // 60
            seconds = elapsed_seconds % 60
            session_str = f"Session : {hours:02d}:{minutes:02d}:{seconds:02d}"
            cv2.putText(frame, session_str, (20, 330), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            total_attention_score += frame_data.attention_score
            processed_frames_count += 1
            average_attention_score = total_attention_score / processed_frames_count
            cv2.putText(frame, f"Average : {int(average_attention_score)}%", (20, 370), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow("Smart Classroom Attention Analyzer", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except Exception as e:
            print("ERROR:", e)
            import traceback
            traceback.print_exc()
            break

    processor.release()
    cv2.destroyAllWindows()
    print("Camera closed successfully.")

def run_face_detection_for_dashboard(data_queue, attention_engine, stop_event):
    processor = VisionProcessor(attention_engine=attention_engine)
    if not processor.initialize():
        return

    print("Dashboard camera pipeline started.")

    while not stop_event.is_set():
        try:
            frame_data = processor.process_frame(draw_landmarks=True)
            if frame_data is None:
                break
            
            display_frame = cv2.cvtColor(frame_data.frame, cv2.COLOR_BGR2RGB)
            display_frame = cv2.resize(display_frame, (640, 480))
            frame_data.frame = display_frame
            
            if data_queue.full():
                try:
                    data_queue.get_nowait()
                except queue.Empty:
                    pass
            data_queue.put(frame_data)
            
        except Exception as e:
            print("ERROR in dashboard camera pipeline:", e)
            import traceback
            traceback.print_exc()
            break

    processor.release()
    print("Dashboard camera pipeline stopped.")
