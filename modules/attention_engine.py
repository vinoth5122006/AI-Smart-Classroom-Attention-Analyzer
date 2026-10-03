"""
Behavior Intelligence Engine for Smart Classroom Attention Analyzer.
This module coordinates rules, states, scoring, confidence, and session statistics.
"""

import time

class Config:
    """
    Central configuration class for thresholds, timeouts, and scoring weights.
    """
    def __init__(self):
        # Time-based thresholds in seconds for behavior state transitions
        self.timeouts = {
            "ABSENT": 2.0, # Continuous lack of face for 2s triggers ABSENT state
            "USING_PHONE": 1.0, # Continuous phone presence for 1s triggers USING_PHONE
            "DROWSY": 1.5, # Continuous closed eyes for 1.5s triggers DROWSY state
            "LOOKING_LEFT": 1.0, # Continuous left gaze for 1s triggers LOOKING_LEFT
            "LOOKING_RIGHT": 1.0, # Continuous right gaze for 1s triggers LOOKING_RIGHT
            "LOOKING_UP": 1.0, # Continuous upward gaze for 1s triggers LOOKING_UP
            "TAKING_NOTES": 1.5, # Continuous downward head + open eyes triggers TAKING_NOTES
            "READING": 1.5, # Continuous forward/slightly down gaze triggers READING
            "ATTENTIVE": 0.5, # Continuous forward attention for 0.5s restores ATTENTIVE state
        }
        
        # Scoring weights for dynamic attention evaluation factors
        self.weights = {
            "forward_direction": 40,
            "eyes_open": 30,
            "face_present": 20,
            "phone_not_detected": 10,
        }
        
        # Base scores associated with each behavior state
        self.state_base_scores = {
            "ATTENTIVE": 100.0,
            "TAKING_NOTES": 85.0,
            "READING": 90.0,
            "LOOKING_LEFT": 50.0,
            "LOOKING_RIGHT": 50.0,
            "LOOKING_UP": 40.0,
            "USING_PHONE": 10.0,
            "DROWSY": 15.0,
            "ABSENT": 0.0,
            "UNKNOWN": 50.0,
        }


class StudentFeatures:
    """
    Data container representing the features extracted from a single video frame.
    """
    def __init__(self, head_direction, eye_status, phone_detected, blink_count, face_detected, timestamp):
        self.head_direction = head_direction # e.g., "FORWARD", "LEFT", "RIGHT", "UP", "DOWN", "NONE"
        self.eye_status = eye_status # e.g., "OPEN", "CLOSED"
        self.phone_detected = phone_detected # True if YOLO detects a phone
        self.blink_count = blink_count # Cumulative blink count
        self.face_detected = face_detected # True if a face is detected
        self.timestamp = timestamp # System time in seconds


class BaseRule:
    """
    Abstract base class defining the contract for all behavior rules.
    """
    def evaluate(self, features, history) -> bool:
        """Determines if the rule criteria are met for the current state."""
        raise NotImplementedError
        
    def confidence(self, features, history) -> float:
        """Returns the confidence value (0.0 to 1.0) of this rule selection."""
        raise NotImplementedError
        
    def reason(self, features, history) -> str:
        """Provides a natural-language reason explaining why the rule triggered."""
        raise NotImplementedError


class AbsentRule(BaseRule):
    def evaluate(self, features, history):
        return not features.face_detected

    def confidence(self, features, history):
        return 1.0 if not features.face_detected else 0.0

    def reason(self, features, history):
        return "Student is absent from the frame."


class PhoneRule(BaseRule):
    def evaluate(self, features, history):
        return features.face_detected and features.phone_detected

    def confidence(self, features, history):
        return 1.0 if features.phone_detected else 0.0

    def reason(self, features, history):
        return "Cell phone usage detected."


class DrowsyRule(BaseRule):
    def evaluate(self, features, history):
        return features.face_detected and features.eye_status == "CLOSED"

    def confidence(self, features, history):
        return 0.95 if features.eye_status == "CLOSED" else 0.0

    def reason(self, features, history):
        return "Student's eyes are closed, indicating drowsiness."


class LookingLeftRule(BaseRule):
    def evaluate(self, features, history):
        return features.face_detected and features.head_direction == "LEFT"

    def confidence(self, features, history):
        return 0.90 if features.head_direction == "LEFT" else 0.0

    def reason(self, features, history):
        return "Head turned to the left."


class LookingRightRule(BaseRule):
    def evaluate(self, features, history):
        return features.face_detected and features.head_direction == "RIGHT"

    def confidence(self, features, history):
        return 0.90 if features.head_direction == "RIGHT" else 0.0

    def reason(self, features, history):
        return "Head turned to the right."


class LookingUpRule(BaseRule):
    def evaluate(self, features, history):
        return features.face_detected and features.head_direction == "UP"

    def confidence(self, features, history):
        return 0.85 if features.head_direction == "UP" else 0.0

    def reason(self, features, history):
        return "Looking upwards away from learning area."


class TakingNotesRule(BaseRule):
    def evaluate(self, features, history):
        return (features.face_detected and 
                features.head_direction == "DOWN" and 
                features.eye_status == "OPEN" and 
                not features.phone_detected)

    def confidence(self, features, history):
        return 0.95 if self.evaluate(features, history) else 0.0

    def reason(self, features, history):
        return "Head tilted down with eyes open, indicating active writing."


class ReadingRule(BaseRule):
    def evaluate(self, features, history):
        # Reading rule triggers if head is forward/slightly down, eyes open, no phone.
        # This rule competes with ForwardRule but evaluates with a slightly lower confidence
        # priority to prefer pure attention by default unless customized.
        return (features.face_detected and 
                features.head_direction in ["FORWARD", "DOWN"] and 
                features.eye_status == "OPEN" and 
                not features.phone_detected)

    def confidence(self, features, history):
        return 0.80 if self.evaluate(features, history) else 0.0

    def reason(self, features, history):
        return "Gaze positioned forward/down with eyes open, reading documents."


class ForwardRule(BaseRule):
    def evaluate(self, features, history):
        return (features.face_detected and 
                features.head_direction == "FORWARD" and 
                features.eye_status == "OPEN" and 
                not features.phone_detected)

    def confidence(self, features, history):
        return 0.95 if self.evaluate(features, history) else 0.0

    def reason(self, features, history):
        return "Facing forward with eyes open, attending to the front."


class RuleEngine:
    """
    Manages the evaluation of active rules and aggregates behavior evidence.
    """
    def __init__(self):
        self.rules = [
            AbsentRule(),
            PhoneRule(),
            DrowsyRule(),
            LookingLeftRule(),
            LookingRightRule(),
            LookingUpRule(),
            TakingNotesRule(),
            ReadingRule(),
            ForwardRule()
        ]

    def evaluate_all(self, features, history):
        """
        Evaluates all rules.
        Returns a list of tuples: (behavior_name, is_active, confidence, reason)
        """
        evidence = []
        for rule in self.rules:
            class_name = rule.__class__.__name__
            behavior = class_name.replace("Rule", "").upper()
            if behavior == "FORWARD":
                behavior = "ATTENTIVE"
            elif behavior == "PHONE":
                behavior = "USING_PHONE"
            elif behavior == "LOOKINGLEFT":
                behavior = "LOOKING_LEFT"
            elif behavior == "LOOKINGRIGHT":
                behavior = "LOOKING_RIGHT"
            elif behavior == "LOOKINGUP":
                behavior = "LOOKING_UP"
            elif behavior == "TAKINGNOTES":
                behavior = "TAKING_NOTES"
                
            is_active = rule.evaluate(features, history)
            conf = rule.confidence(features, history) if is_active else 0.0
            reason = rule.reason(features, history) if is_active else ""
            evidence.append((behavior, is_active, conf, reason))
        return evidence


class StateEngine:
    """
    Manages behavioral state transitions and timing configurations.
    """
    def __init__(self, config):
        self.config = config
        self.current_state = "UNKNOWN"
        self.state_start_time = None
        self.state_history = []
        
        # State transition tracking variables
        self.tracking_state = None
        self.tracking_start_time = None

    def update_state(self, candidate_behavior, timestamp):
        """
        Applies transition timers. State changes only occur if the candidate behavior
        is continuously detected for its configured timeout duration.
        """
        if self.state_start_time is None:
            self.state_start_time = timestamp
            self.current_state = candidate_behavior
            return self.current_state

        # If candidate behavior matches our current state, cancel any pending transition
        if candidate_behavior == self.current_state:
            self.tracking_state = None
            self.tracking_start_time = None
            return self.current_state

        # If the candidate behavior matches the transition candidate we are tracking
        if candidate_behavior == self.tracking_state:
            elapsed = timestamp - self.tracking_start_time
            required_duration = self.config.timeouts.get(candidate_behavior, 3.0)
            
            if elapsed >= required_duration:
                # Timer complete: Transition the state
                old_state = self.current_state
                self.current_state = candidate_behavior
                self.state_start_time = timestamp
                self.state_history.append((timestamp, old_state, candidate_behavior))
                
                # Reset transition tracker
                self.tracking_state = None
                self.tracking_start_time = None
        else:
            # Start tracking a new transition candidate
            self.tracking_state = candidate_behavior
            self.tracking_start_time = timestamp

        return self.current_state


class ScoreEngine:
    """
    Computes an attention score from 0 to 100 based on state and features.
    """
    def __init__(self, config):
        self.config = config

    def calculate_score(self, features, state):
        """
        Weighted attention score calculation based on current state and physical factors.
        """
        if not features.face_detected or state == "ABSENT":
            return 0.0

        # Base score from state mapping
        base_score = self.config.state_base_scores.get(state, 50.0)

        # Dynamic sensor calculation
        factor_score = 0.0
        total_weight = sum(self.config.weights.values())

        if features.face_detected:
            factor_score += (self.config.weights["face_present"] / total_weight) * 100.0
            
            if features.head_direction == "FORWARD":
                factor_score += (self.config.weights["forward_direction"] / total_weight) * 100.0
                
            if features.eye_status == "OPEN":
                factor_score += (self.config.weights["eyes_open"] / total_weight) * 100.0
                
            if not features.phone_detected:
                factor_score += (self.config.weights["phone_not_detected"] / total_weight) * 100.0

        # Balanced formula: 60% state behavior score, 40% raw physical parameters score
        final_score = 0.6 * base_score + 0.4 * factor_score
        return float(max(0.0, min(100.0, final_score)))


class ConfidenceEngine:
    """
    Determines behavior classification confidence values.
    """
    def __init__(self, config):
        self.config = config

    def calculate_confidence(self, behavior, rule_evidence):
        """
        Extracts confidence details directly from matching evaluated rule evidence.
        """
        for behavior_name, is_active, conf, reason in rule_evidence:
            if behavior_name == behavior:
                return float(conf * 100.0)
        return 50.0


class StatisticsEngine:
    """
    Tracks session duration, behavior duration statistics, and telemetry counters.
    """
    def __init__(self):
        self.start_time = None
        self.last_update_time = None
        
        # Statistical scores
        self.total_attention_sum = 0.0
        self.attention_count = 0
        self.min_attention = 100.0
        self.max_attention = 0.0
        
        # Telemetry counters
        self.blink_count = 0
        self.phone_usage_count = 0
        self.drowsiness_count = 0
        self.state_changes = 0
        
        # State duration tracking dict
        self.state_durations = {
            "ATTENTIVE": 0.0,
            "TAKING_NOTES": 0.0,
            "READING": 0.0,
            "LOOKING_LEFT": 0.0,
            "LOOKING_RIGHT": 0.0,
            "LOOKING_UP": 0.0,
            "USING_PHONE": 0.0,
            "DROWSY": 0.0,
            "ABSENT": 0.0,
            "UNKNOWN": 0.0,
        }
        
        self.previous_phone_state = False
        self.previous_drowsy_state = False
        self.previous_state = None
        self.last_head_direction = "FORWARD"
        self.last_eye_status = "OPEN"
        self.last_phone_detected = False

    def update(self, current_state, score, features):
        """Updates internal statistics using frame timestamps and features."""
        timestamp = features.timestamp
        self.last_head_direction = features.head_direction
        self.last_eye_status = features.eye_status
        self.last_phone_detected = features.phone_detected

        if self.start_time is None:
            self.start_time = timestamp
            self.last_update_time = timestamp
            self.min_attention = score
            self.max_attention = score
            self.previous_state = current_state
            return

        # Keep state transitions count
        if current_state != self.previous_state:
            self.state_changes += 1
            self.previous_state = current_state

        # Calculate time step
        dt = timestamp - self.last_update_time
        if dt > 0:
            if current_state in self.state_durations:
                self.state_durations[current_state] += dt
            else:
                self.state_durations[current_state] = dt
            self.last_update_time = timestamp

        # Score stats
        self.total_attention_sum += score
        self.attention_count += 1
        self.min_attention = min(self.min_attention, score)
        self.max_attention = max(self.max_attention, score)

        # Blinks
        self.blink_count = features.blink_count

        # Phone usage count trigger
        if features.phone_detected and not self.previous_phone_state:
            self.phone_usage_count += 1
        self.previous_phone_state = features.phone_detected

        # Drowsiness count trigger
        is_drowsy = (current_state == "DROWSY")
        if is_drowsy and not self.previous_drowsy_state:
            self.drowsiness_count += 1
        self.previous_drowsy_state = is_drowsy

    def get_summary(self):
        """Returns statistics summary structured dictionary with state durations."""
        duration = 0.0
        if self.start_time and self.last_update_time:
            duration = self.last_update_time - self.start_time

        avg_attention = (
            self.total_attention_sum / self.attention_count 
            if self.attention_count > 0 else 0.0
        )

        return {
            "session_duration": float(duration),
            "average_attention": float(avg_attention),
            "minimum_attention": float(self.min_attention if self.min_attention != 100.0 else 0.0),
            "maximum_attention": float(self.max_attention),
            "head_direction": self.last_head_direction,
            "eye_status": self.last_eye_status,
            "phone_detected": self.last_phone_detected,
            "blink_count": int(self.blink_count),
            "phone_usage_count": int(self.phone_usage_count),
            "state_durations": {k: float(v) for k, v in self.state_durations.items()},
            "looking_left_duration": float(self.state_durations.get("LOOKING_LEFT", 0.0)),
            "looking_right_duration": float(self.state_durations.get("LOOKING_RIGHT", 0.0)),
            "looking_down_duration": float(self.state_durations.get("TAKING_NOTES", 0.0) + self.state_durations.get("READING", 0.0)),
            "taking_notes_duration": float(self.state_durations.get("TAKING_NOTES", 0.0)),
            "reading_duration": float(self.state_durations.get("READING", 0.0)),
            "drowsiness_count": int(self.drowsiness_count),
            "state_changes": int(self.state_changes),
        }


class AttentionEngine:
    """
    Coordinator class orchestrating RuleEngine, StateEngine, and ScoreEngine.
    """
    def __init__(self, config=None):
        self.config = config if config else Config()
        self.history = []
        self.rule_engine = RuleEngine()
        self.state_engine = StateEngine(self.config)
        self.score_engine = ScoreEngine(self.config)
        self.confidence_engine = ConfidenceEngine(self.config)
        self.statistics_engine = StatisticsEngine()

    def analyze(self, features: StudentFeatures) -> dict:
        """
        Coordinates behavior classification, timer checks, scoring, and telemetry updates.
        Returns a structured dictionary of current analysis.
        """
        self.history.append(features)
        if len(self.history) > 1000:
            self.history.pop(0)

        # 1. Run all rules
        rule_evidence = self.rule_engine.evaluate_all(features, self.history)

        # 2. Pick candidate behavior (highest confidence wins)
        candidate_behavior = "UNKNOWN"
        highest_conf = 0.0
        active_reason = "No specific rules triggered."

        for behavior_name, is_active, conf, reason in rule_evidence:
            if is_active and conf > highest_conf:
                highest_conf = conf
                candidate_behavior = behavior_name
                active_reason = reason

        # 3. Process state machine and timers
        current_state = self.state_engine.update_state(candidate_behavior, features.timestamp)

        # 4. Calculate attention score
        score = self.score_engine.calculate_score(features, current_state)

        # 5. Extract classification confidence
        confidence = self.confidence_engine.calculate_confidence(current_state, rule_evidence)

        # 6. Update session telemetry statistics
        self.statistics_engine.update(current_state, score, features)

        # 7. Behavior duration
        behavior_duration = 0.0
        if self.state_engine.state_start_time:
            behavior_duration = features.timestamp - self.state_engine.state_start_time

        return {
            "current_behavior": candidate_behavior,
            "reason": active_reason,
            "attention_score": score,
            "confidence": confidence,
            "current_state": current_state,
            "behavior_duration": behavior_duration,
            "session_statistics": self.statistics_engine.get_summary(),
        }
