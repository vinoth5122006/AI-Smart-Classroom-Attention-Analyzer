"""
Authentication and Authorization Module for Enterprise Smart Classroom Console.
Provides session token generation, verification, and admin credential validation.
"""

import os
import hmac
import hashlib
import time
import base64
import json
from typing import Optional, Dict, Any

SECRET_KEY = os.environ.get("SECRET_KEY", "smart-classroom-master-secret-key-2026-secure")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "smartclass2026")

def verify_credentials(username: str, password: str) -> bool:
    """Verifies administrator credentials using constant-time comparison."""
    user_match = hmac.compare_digest(username.strip(), ADMIN_USERNAME)
    pass_match = hmac.compare_digest(password.strip(), ADMIN_PASSWORD)
    return user_match and pass_match

def create_session_token(username: str, role: str = "instructor", expiry_hours: int = 24) -> str:
    """Generates a tamper-proof HMAC-SHA256 signed session token."""
    now = int(time.time())
    expires = now + (expiry_hours * 3600)
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": expires
    }
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8').rstrip('=')
    
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        payload_b64.encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    return f"{payload_b64}.{sig_b64}"

def verify_session_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Validates token signature and expiration. Returns payload if valid, None otherwise."""
    if not token or '.' not in token:
        return None
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
        payload_b64, sig_b64 = parts
        
        # Verify signature
        expected_sig = hmac.new(
            SECRET_KEY.encode('utf-8'),
            payload_b64.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8').rstrip('=')
        
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None
            
        # Decode payload with padding
        padding = '=' * (4 - (len(payload_b64) % 4)) if len(payload_b64) % 4 else ''
        payload_json = base64.urlsafe_b64decode((payload_b64 + padding).encode('utf-8')).decode('utf-8')
        payload = json.loads(payload_json)
        
        # Check expiration
        if payload.get("exp", 0) < time.time():
            return None
            
        return payload
    except Exception:
        return None
