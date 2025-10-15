"""
Security utilities for input sanitization, validation, and encryption
"""

import re
import html
import hashlib
import secrets
import bcrypt
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class InputSanitizer:
    """Input sanitization and validation utilities"""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """Sanitize string input by escaping HTML and limiting length"""
        if not isinstance(input_str, str):
            return ""
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_str)
        
        # HTML escape
        sanitized = html.escape(sanitized)
        
        # Limit length
        sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email:
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format"""
        if not username:
            return False
        
        # Username should be 3-30 characters, alphanumeric and underscores only
        username_pattern = r'^[a-zA-Z0-9_]{3,30}$'
        return bool(re.match(username_pattern, username))
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        if not password:
            return {"valid": False, "errors": ["Password is required"]}
        
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """Sanitize search query input"""
        if not query:
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\';]', '', query)
        
        # Limit length
        sanitized = sanitized[:500]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_isbn(isbn: str) -> bool:
        """Validate ISBN format (ISBN-10 or ISBN-13)"""
        if not isbn:
            return False
        
        # Remove hyphens and spaces
        isbn_clean = re.sub(r'[-\s]', '', isbn)
        
        # Check if it's a valid ISBN-10 or ISBN-13
        if len(isbn_clean) == 10:
            return InputSanitizer._validate_isbn10(isbn_clean)
        elif len(isbn_clean) == 13:
            return InputSanitizer._validate_isbn13(isbn_clean)
        
        return False
    
    @staticmethod
    def _validate_isbn10(isbn: str) -> bool:
        """Validate ISBN-10 checksum"""
        try:
            total = 0
            for i in range(9):
                total += int(isbn[i]) * (10 - i)
            
            check_digit = isbn[9]
            if check_digit == 'X':
                check_digit = 10
            else:
                check_digit = int(check_digit)
            
            return (total + check_digit) % 11 == 0
        except:
            return False
    
    @staticmethod
    def _validate_isbn13(isbn: str) -> bool:
        """Validate ISBN-13 checksum"""
        try:
            total = 0
            for i in range(12):
                multiplier = 1 if i % 2 == 0 else 3
                total += int(isbn[i]) * multiplier
            
            check_digit = (10 - (total % 10)) % 10
            return check_digit == int(isbn[12])
        except:
            return False

class EncryptionUtils:
    """Encryption and hashing utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        if not password or not hashed:
            return False
        
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except:
            return False
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def hash_data(data: str) -> str:
        """Create SHA-256 hash of data"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

class RateLimiter:
    """Simple rate limiting implementation"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, identifier: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed based on rate limit"""
        import time
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
        else:
            self.requests[identifier] = []
        
        # Check if under limit
        if len(self.requests[identifier]) < max_requests:
            self.requests[identifier].append(current_time)
            return True
        
        return False
    
    def get_remaining_requests(self, identifier: str, max_requests: int, window_seconds: int) -> int:
        """Get remaining requests in current window"""
        import time
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
            return max(0, max_requests - len(self.requests[identifier]))
        
        return max_requests

class SecurityHeaders:
    """Security headers for HTTP responses"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get security headers for HTTP responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }

class AuditLogger:
    """Security audit logging"""
    
    @staticmethod
    def log_security_event(event_type: str, details: Dict[str, Any], user_id: Optional[str] = None):
        """Log security-related events"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details,
            'ip_address': details.get('ip_address'),
            'user_agent': details.get('user_agent')
        }
        
        logger.warning(f"SECURITY_EVENT: {log_entry}")
    
    @staticmethod
    def log_failed_login(username: str, ip_address: str, user_agent: str):
        """Log failed login attempt"""
        AuditLogger.log_security_event(
            'failed_login',
            {
                'username': username,
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        )
    
    @staticmethod
    def log_rate_limit_exceeded(identifier: str, ip_address: str):
        """Log rate limit exceeded"""
        AuditLogger.log_security_event(
            'rate_limit_exceeded',
            {
                'identifier': identifier,
                'ip_address': ip_address
            }
        )
    
    @staticmethod
    def log_suspicious_activity(activity: str, details: Dict[str, Any], user_id: Optional[str] = None):
        """Log suspicious activity"""
        AuditLogger.log_security_event(
            'suspicious_activity',
            {
                'activity': activity,
                **details
            },
            user_id
        )

# Global rate limiter instance
rate_limiter = RateLimiter()

# Security validation functions
def validate_request_data(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """Validate request data and sanitize inputs"""
    result = {
        'valid': True,
        'errors': [],
        'sanitized_data': {}
    }
    
    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            result['errors'].append(f"Field '{field}' is required")
            result['valid'] = False
    
    # Sanitize string fields
    for key, value in data.items():
        if isinstance(value, str):
            result['sanitized_data'][key] = InputSanitizer.sanitize_string(value)
        else:
            result['sanitized_data'][key] = value
    
    return result

def check_rate_limit(identifier: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
    """Check if request is within rate limit"""
    return rate_limiter.is_allowed(identifier, max_requests, window_seconds)
