try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

class PhoneDetector:

    def __init__(self):
        self.model = None
        if YOLO is not None:
            try:
                print("Loading YOLO Model...")
                self.model = YOLO("yolov8n.pt")
                print("YOLO Loaded Successfully!")
            except Exception as e:
                print(f"Warning: Could not load YOLO model: {e}")
        else:
            print("Note: Ultralytics not installed. Phone detection will default to False.")

    def detect_phone(self, frame):
        if self.model is None:
            return False

        results = self.model(frame, verbose=False)

        phone_detected = False

        for result in results:

            for box in result.boxes:

                cls = int(box.cls[0])

                name = self.model.names[cls]

                if name == "cell phone":
                    phone_detected = True

        return phone_detected