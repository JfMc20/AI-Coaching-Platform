"""
Password Security Implementation
Implements secure password hashing and validation following security best practices
"""

import os
import re
import hashlib
import logging
import asyncio
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass
from enum import Enum
import httpx
from pathlib import Path
from shared.cache import get_cache_manager

# Primary: Argon2id for new passwords
from argon2 import PasswordHasher as Argon2PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError

# Fallback: bcrypt for compatibility
from passlib.context import CryptContext

logger = logging.getLogger(__name__)


class PasswordStrength(str, Enum):
    """Password strength levels"""
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    FAIR = "fair"
    GOOD = "good"
    STRONG = "strong"


@dataclass
class PasswordStrengthResult:
    """Result of password strength validation"""
    strength: PasswordStrength
    score: int  # 0-100
    is_valid: bool
    violations: List[str]
    suggestions: List[str]
    estimated_crack_time: str


@dataclass
class PasswordPolicy:
    """Configurable password policy"""
    min_length: int = 8
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = True
    min_special_chars: int = 1
    forbidden_patterns: List[str] = None
    check_common_passwords: bool = True
    check_personal_info: bool = True
    check_compromised: bool = True
    
    def __post_init__(self):
        if self.forbidden_patterns is None:
            self.forbidden_patterns = [
                r'(.)\1{2,}',  # 3+ repeated characters
                r'(012|123|234|345|456|567|678|789|890)',  # Sequential numbers
                r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|lmn|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
                r'(qwerty|asdfgh|zxcvbn)',  # Keyboard patterns
            ]


class PasswordHasher:
    """
    Secure password hashing with Argon2id primary and bcrypt fallback
    """
    
    def __init__(self):
        # Argon2id configuration (OWASP recommended parameters)
        self.argon2_hasher = Argon2PasswordHasher(
            memory_cost=65536,  # 64 MB
            time_cost=3,        # 3 iterations
            parallelism=4,      # 4 parallel threads
            hash_len=32,        # 32 byte hash
            salt_len=16         # 16 byte salt
        )
        
        # bcrypt fallback configuration
        self.bcrypt_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12  # Cost factor 12
        )
        
        # Load configuration from environment
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables"""
        try:
            # Argon2 parameters (configurable via environment)
            memory_cost = int(os.getenv("ARGON2_MEMORY_COST", "65536"))
            time_cost = int(os.getenv("ARGON2_TIME_COST", "3"))
            parallelism = int(os.getenv("ARGON2_PARALLELISM", "4"))
            
            # Recreate hasher with custom parameters if different
            if (memory_cost != 65536 or time_cost != 3 or parallelism != 4):
                self.argon2_hasher = Argon2PasswordHasher(
                    memory_cost=memory_cost,
                    time_cost=time_cost,
                    parallelism=parallelism,
                    hash_len=32,
                    salt_len=16
                )
                logger.info(f"Argon2 configured with custom parameters: memory={memory_cost}, time={time_cost}, parallelism={parallelism}")
            
            # bcrypt cost factor
            bcrypt_rounds = int(os.getenv("BCRYPT_ROUNDS", "12"))
            if bcrypt_rounds != 12:
                self.bcrypt_context = CryptContext(
                    schemes=["bcrypt"],
                    deprecated="auto",
                    bcrypt__rounds=bcrypt_rounds
                )
                logger.info(f"bcrypt configured with custom rounds: {bcrypt_rounds}")
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid password hashing configuration, using defaults: {e}")
    
    def hash_password(self, password: str, use_argon2: bool = True) -> str:
        """
        Hash a password using Argon2id (primary) or bcrypt (fallback)
        
        Args:
            password: Plain text password
            use_argon2: Use Argon2id if True, bcrypt if False
            
        Returns:
            Hashed password string
            
        Raises:
            HashingError: If hashing fails
        """
        try:
            if use_argon2:
                # Use Argon2id (primary method)
                hashed = self.argon2_hasher.hash(password)
                logger.debug("Password hashed using Argon2id")
                return hashed
            else:
                # Use bcrypt (fallback method)
                hashed = self.bcrypt_context.hash(password)
                logger.debug("Password hashed using bcrypt")
                return hashed
                
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise HashingError(f"Failed to hash password: {e}")
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash, supporting both Argon2id and bcrypt
        
        Args:
            password: Plain text password
            hashed_password: Hashed password to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            # Try Argon2id first (starts with $argon2id$)
            if hashed_password.startswith("$argon2id$"):
                try:
                    self.argon2_hasher.verify(hashed_password, password)
                    logger.debug("Password verified using Argon2id")
                    return True
                except VerifyMismatchError:
                    return False
            
            # Try bcrypt fallback (starts with $2b$ or similar)
            elif hashed_password.startswith(("$2a$", "$2b$", "$2x$", "$2y$")):
                result = self.bcrypt_context.verify(password, hashed_password)
                logger.debug("Password verified using bcrypt")
                return result
            
            else:
                logger.warning(f"Unknown password hash format: {hashed_password[:10]}...")
                return False
                
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    def needs_rehash(self, hashed_password: str) -> bool:
        """
        Check if a password hash needs to be updated
        
        Args:
            hashed_password: Existing password hash
            
        Returns:
            True if hash should be updated
        """
        try:
            # Argon2id hashes are current, no rehash needed
            if hashed_password.startswith("$argon2id$"):
                return False
            
            # bcrypt hashes should be migrated to Argon2id
            if hashed_password.startswith(("$2a$", "$2b$", "$2x$", "$2y$")):
                return True
            
            # Unknown format should be rehashed
            return True
            
        except Exception as e:
            logger.error(f"Error checking hash format: {e}")
            return True


class PasswordValidator:
    """
    Password strength validation and policy enforcement
    """
    
    def __init__(self, policy: Optional[PasswordPolicy] = None):
        self.policy = policy or PasswordPolicy()
        self._common_passwords: Optional[Set[str]] = None
        self._load_common_passwords()
    
    def _load_common_passwords(self):
        """Load common passwords list for validation"""
        try:
            # Try to load from file first
            common_passwords_file = Path(__file__).parent / "common_passwords.txt"
            if common_passwords_file.exists():
                with open(common_passwords_file, 'r', encoding='utf-8') as f:
                    self._common_passwords = {line.strip().lower() for line in f if line.strip()}
                logger.info(f"Loaded {len(self._common_passwords)} common passwords from file")
            else:
                # Fallback to hardcoded list of most common passwords
                self._common_passwords = {
                    "password", "123456", "password123", "admin", "qwerty",
                    "letmein", "welcome", "monkey", "1234567890", "abc123",
                    "123456789", "password1", "12345678", "123123", "1234567",
                    "welcome123", "admin123", "root", "toor", "pass"
                }
                logger.info(f"Using fallback common passwords list ({len(self._common_passwords)} entries)")
                
        except Exception as e:
            logger.warning(f"Failed to load common passwords: {e}")
            self._common_passwords = set()
    
    async def validate_password_strength(
        self, 
        password: str, 
        personal_info: Optional[Dict[str, str]] = None
    ) -> PasswordStrengthResult:
        """
        Validate password strength against policy
        
        Args:
            password: Password to validate
            personal_info: Optional dict with user info (email, name, etc.)
            
        Returns:
            PasswordStrengthResult with validation details
        """
        violations = []
        suggestions = []
        score = 0
        
        # Basic length check
        if len(password) < self.policy.min_length:
            violations.append(f"Password must be at least {self.policy.min_length} characters long")
            suggestions.append(f"Add {self.policy.min_length - len(password)} more characters")
        else:
            score += min(20, len(password) * 2)  # Up to 20 points for length
        
        if len(password) > self.policy.max_length:
            violations.append(f"Password must not exceed {self.policy.max_length} characters")
        
        # Character requirements
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        if self.policy.require_uppercase and not has_upper:
            violations.append("Password must contain at least one uppercase letter")
            suggestions.append("Add uppercase letters (A-Z)")
        elif has_upper:
            score += 15
        
        if self.policy.require_lowercase and not has_lower:
            violations.append("Password must contain at least one lowercase letter")
            suggestions.append("Add lowercase letters (a-z)")
        elif has_lower:
            score += 15
        
        if self.policy.require_digits and not has_digit:
            violations.append("Password must contain at least one digit")
            suggestions.append("Add numbers (0-9)")
        elif has_digit:
            score += 15
        
        if self.policy.require_special_chars and not has_special:
            violations.append("Password must contain at least one special character")
            suggestions.append("Add special characters (!@#$%^&*)")
        elif has_special:
            score += 15
        
        # Check for forbidden patterns
        for pattern in self.policy.forbidden_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                violations.append("Password contains forbidden patterns (repeated characters, sequences)")
                suggestions.append("Avoid repeated characters and keyboard patterns")
                score -= 10
                break
        
        # Check against common passwords
        if self.policy.check_common_passwords and self._common_passwords:
            if password.lower() in self._common_passwords:
                violations.append("Password is too common and easily guessable")
                suggestions.append("Use a more unique password")
                score -= 20
        
        # Check against personal information
        if self.policy.check_personal_info and personal_info:
            for key, value in personal_info.items():
                if value and len(value) > 2 and value.lower() in password.lower():
                    violations.append(f"Password contains personal information ({key})")
                    suggestions.append("Avoid using personal information in passwords")
                    score -= 15
                    break
        
        # Check against compromised passwords (HaveIBeenPwned API)
        if self.policy.check_compromised:
            is_compromised = await self._check_compromised_password(password)
            if is_compromised:
                violations.append("Password has been found in data breaches")
                suggestions.append("Use a password that hasn't been compromised")
                score -= 25
        
        # Bonus points for diversity
        char_types = sum([has_upper, has_lower, has_digit, has_special])
        score += char_types * 5
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        # Determine strength level
        if score >= 80:
            strength = PasswordStrength.STRONG
        elif score >= 60:
            strength = PasswordStrength.GOOD
        elif score >= 40:
            strength = PasswordStrength.FAIR
        elif score >= 20:
            strength = PasswordStrength.WEAK
        else:
            strength = PasswordStrength.VERY_WEAK
        
        # Estimate crack time (simplified)
        crack_time = self._estimate_crack_time(password, score)
        
        return PasswordStrengthResult(
            strength=strength,
            score=score,
            is_valid=len(violations) == 0,
            violations=violations,
            suggestions=suggestions,
            estimated_crack_time=crack_time
        )
    
    async def _check_compromised_password(self, password: str) -> bool:
        """
        Check if password has been compromised using HaveIBeenPwned API
        
        Args:
            password: Password to check
            
        Returns:
            True if password is compromised, False otherwise
        """
        # Hash password with SHA-1
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        
        # Initialize cache manager
        cache_manager = get_cache_manager()
        cache_key = f"pwned_password:{prefix}"
        
        try:
            # Try to get cached response
            cached_response = await cache_manager.redis.get("system", cache_key)
            if cached_response:
                # Check if our suffix appears in the cached response
                for line in cached_response.splitlines():
                    hash_suffix, count = line.split(':')
                    if hash_suffix == suffix:
                        logger.warning(f"Password found in {count} breaches (cached)")
                        return True
                return False
            
            # Query HaveIBeenPwned API with k-anonymity
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"https://api.pwnedpasswords.com/range/{prefix}",
                    headers={"User-Agent": "MVP-Coaching-AI-Platform"}
                )
                
                if response.status_code == 200:
                    # Cache the response for 1 hour
                    await cache_manager.redis.set("system", cache_key, response.text, ttl=3600)
                    
                    # Check if our suffix appears in the response
                    for line in response.text.splitlines():
                        hash_suffix, count = line.split(':')
                        if hash_suffix == suffix:
                            logger.warning(f"Password found in {count} breaches")
                            return True
                    return False
                else:
                    logger.warning(f"HaveIBeenPwned API error: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.warning(f"Failed to check compromised password: {e}")
            return False  # Fail open - don't block if service is unavailable
    
    def _estimate_crack_time(self, password: str, score: int) -> str:
        """
        Estimate time to crack password (simplified calculation)
        
        Args:
            password: Password to analyze
            score: Password strength score
            
        Returns:
            Human-readable crack time estimate
        """
        # Simplified calculation based on character set and length
        charset_size = 0
        if re.search(r'[a-z]', password):
            charset_size += 26
        if re.search(r'[A-Z]', password):
            charset_size += 26
        if re.search(r'\d', password):
            charset_size += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            charset_size += 32
        
        if charset_size == 0:
            return "instantly"
        
        # Rough calculation (assumes 1 billion guesses per second)
        combinations = charset_size ** len(password)
        seconds = combinations / (2 * 1_000_000_000)  # Average case
        
        # Adjust based on score
        if score < 20:
            seconds /= 1000  # Very weak passwords crack much faster
        elif score < 40:
            seconds /= 100
        elif score < 60:
            seconds /= 10
        
        # Convert to human readable
        if seconds < 1:
            return "instantly"
        elif seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            return f"{int(seconds/60)} minutes"
        elif seconds < 86400:
            return f"{int(seconds/3600)} hours"
        elif seconds < 31536000:
            return f"{int(seconds/86400)} days"
        else:
            return f"{int(seconds/31536000)} years"


# Convenience functions for easy usage
_password_hasher = PasswordHasher()
_password_validator = PasswordValidator()


def hash_password(password: str, use_argon2: bool = True) -> str:
    """Hash a password using the default hasher"""
    return _password_hasher.hash_password(password, use_argon2)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password using the default hasher"""
    return _password_hasher.verify_password(password, hashed_password)


async def validate_password_strength(
    password: str, 
    personal_info: Optional[Dict[str, str]] = None
) -> PasswordStrengthResult:
    """Validate password strength using the default validator"""
    return await _password_validator.validate_password_strength(password, personal_info)


def check_password_policy(password: str, policy: Optional[PasswordPolicy] = None) -> bool:
    """Quick check if password meets policy requirements"""
    validator = PasswordValidator(policy)
    # Synchronous version for quick checks
    violations = []
    
    if len(password) < validator.policy.min_length:
        violations.append("Too short")
    
    if validator.policy.require_uppercase and not re.search(r'[A-Z]', password):
        violations.append("Missing uppercase")
    
    if validator.policy.require_lowercase and not re.search(r'[a-z]', password):
        violations.append("Missing lowercase")
    
    if validator.policy.require_digits and not re.search(r'\d', password):
        violations.append("Missing digits")
    
    if validator.policy.require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        violations.append("Missing special characters")
    
    return len(violations) == 0