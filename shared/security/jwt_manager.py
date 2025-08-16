"""
Advanced JWT Management System
Implements RS256 JWT tokens with key rotation, blacklisting, and comprehensive security features
"""

import os
import uuid
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_

from shared.models.database import JWTBlacklist, RefreshToken
from shared.cache import get_cache_manager

logger = logging.getLogger(__name__)


class JWTKeyManager:
    """Manages JWT signing keys with automatic rotation"""
    
    def __init__(self):
        self.keys_dir = Path(os.getenv("JWT_KEYS_DIR", "/app/keys"))
        self.key_rotation_days = int(os.getenv("JWT_KEY_ROTATION_DAYS", "30"))
        self.current_key_id: Optional[str] = None
        self.keys: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
        # Ensure keys directory exists
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """Initialize key manager and load existing keys"""
        async with self._lock:
            await self._load_existing_keys()
            if not self.keys:
                await self._generate_initial_key()
            await self._set_current_key()
    
    async def _load_existing_keys(self):
        """Load existing keys from filesystem"""
        try:
            for key_file in self.keys_dir.glob("*.json"):
                key_id = key_file.stem
                with open(key_file, 'r') as f:
                    key_data = json.load(f)
                
                # Load private key
                private_key_path = self.keys_dir / f"{key_id}_private.pem"
                public_key_path = self.keys_dir / f"{key_id}_public.pem"
                
                if private_key_path.exists() and public_key_path.exists():
                    with open(private_key_path, 'rb') as f:
                        private_key = serialization.load_pem_private_key(
                            f.read(), password=None, backend=default_backend()
                        )
                    
                    with open(public_key_path, 'rb') as f:
                        public_key = serialization.load_pem_public_key(
                            f.read(), backend=default_backend()
                        )
                    
                    self.keys[key_id] = {
                        **key_data,
                        'private_key': private_key,
                        'public_key': public_key,
                        'created_at': datetime.fromisoformat(key_data['created_at'])
                    }
                    
                    logger.info(f"Loaded JWT key: {key_id}")
                    
        except Exception as e:
            logger.error(f"Error loading existing keys: {e}")
    
    async def _generate_initial_key(self):
        """Generate initial JWT signing key"""
        key_id = str(uuid.uuid4())
        await self._generate_key_pair(key_id)
        logger.info(f"Generated initial JWT key: {key_id}")
    
    async def _generate_key_pair(self, key_id: str):
        """Generate RSA key pair for JWT signing"""
        try:
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            
            # Serialize keys
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Save keys to filesystem
            private_key_path = self.keys_dir / f"{key_id}_private.pem"
            public_key_path = self.keys_dir / f"{key_id}_public.pem"
            
            with open(private_key_path, 'wb') as f:
                f.write(private_pem)
            
            with open(public_key_path, 'wb') as f:
                f.write(public_pem)
            
            # Set restrictive permissions
            private_key_path.chmod(0o600)
            public_key_path.chmod(0o644)
            
            # Store key metadata
            key_data = {
                'key_id': key_id,
                'algorithm': 'RS256',
                'created_at': datetime.utcnow().isoformat(),
                'is_active': True
            }
            
            metadata_path = self.keys_dir / f"{key_id}.json"
            with open(metadata_path, 'w') as f:
                json.dump(key_data, f, indent=2)
            
            # Store in memory
            self.keys[key_id] = {
                **key_data,
                'private_key': private_key,
                'public_key': public_key,
                'created_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error generating key pair {key_id}: {e}")
            raise
    
    async def _set_current_key(self):
        """Set the current active key (most recent)"""
        if not self.keys:
            return
        
        # Find the most recent active key
        active_keys = [
            (key_id, key_data) for key_id, key_data in self.keys.items()
            if key_data.get('is_active', True)
        ]
        
        if active_keys:
            # Sort by creation date, most recent first
            active_keys.sort(key=lambda x: x[1]['created_at'], reverse=True)
            self.current_key_id = active_keys[0][0]
            logger.info(f"Current JWT key set to: {self.current_key_id}")
    
    async def get_current_key(self) -> Tuple[str, Any]:
        """Get current signing key"""
        if not self.current_key_id or self.current_key_id not in self.keys:
            await self.initialize()
        
        if not self.current_key_id:
            raise ValueError("No current JWT key available")
        
        key_data = self.keys[self.current_key_id]
        return self.current_key_id, key_data['private_key']
    
    async def get_public_key(self, key_id: str) -> Optional[Any]:
        """Get public key for verification"""
        if key_id not in self.keys:
            return None
        
        return self.keys[key_id]['public_key']
    
    async def rotate_keys(self) -> str:
        """Rotate JWT keys - generate new key and mark old as inactive after grace period"""
        async with self._lock:
            # Generate new key
            new_key_id = str(uuid.uuid4())
            await self._generate_key_pair(new_key_id)
            
            # Set as current key
            old_key_id = self.current_key_id
            self.current_key_id = new_key_id
            
            logger.info(f"JWT key rotated: {old_key_id} -> {new_key_id}")
            
            # Schedule old key deactivation (keep active for grace period)
            if old_key_id:
                asyncio.create_task(self._deactivate_key_after_grace_period(old_key_id))
            
            return new_key_id
    
    async def _deactivate_key_after_grace_period(self, key_id: str, grace_hours: int = 24):
        """Deactivate old key after grace period"""
        await asyncio.sleep(grace_hours * 3600)  # Wait for grace period
        
        if key_id in self.keys:
            self.keys[key_id]['is_active'] = False
            
            # Update metadata file
            metadata_path = self.keys_dir / f"{key_id}.json"
            if metadata_path.exists():
                key_data = self.keys[key_id].copy()
                key_data.pop('private_key', None)
                key_data.pop('public_key', None)
                key_data['is_active'] = False
                
                with open(metadata_path, 'w') as f:
                    json.dump(key_data, f, indent=2)
            
            logger.info(f"JWT key deactivated after grace period: {key_id}")
    
    async def check_key_rotation_needed(self) -> bool:
        """Check if key rotation is needed based on age"""
        if not self.current_key_id or self.current_key_id not in self.keys:
            return True
        
        current_key = self.keys[self.current_key_id]
        age = datetime.utcnow() - current_key['created_at']
        
        return age.days >= self.key_rotation_days


class JWTManager:
    """Advanced JWT token management with blacklisting and security features"""
    
    def __init__(self):
        self.key_manager = JWTKeyManager()
        self.issuer = os.getenv("JWT_ISSUER", "mvp-coaching-ai-platform")
        self.audience = os.getenv("JWT_AUDIENCE", "api")
        self.access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self.refresh_token_expire_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))
        
        # Initialize cache manager for blacklist
        self.cache_manager = get_cache_manager()
    
    async def initialize(self):
        """Initialize JWT manager"""
        await self.key_manager.initialize()
    
    async def create_access_token(
        self,
        creator_id: str,
        roles: List[str] = None,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, str]:
        """
        Create JWT access token with comprehensive claims
        
        Args:
            creator_id: Creator UUID
            roles: List of roles for RBAC
            permissions: List of permissions
            expires_delta: Custom expiration time
            
        Returns:
            Tuple of (token, jti)
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        # Generate unique JTI for blacklisting
        jti = str(uuid.uuid4())
        
        # Standard JWT claims
        payload = {
            # Standard claims
            "iss": self.issuer,
            "aud": self.audience,
            "sub": creator_id,
            "iat": datetime.utcnow(),
            "exp": expire,
            "jti": jti,
            
            # Custom claims
            "type": "access",
            "creator_id": creator_id,
            "roles": roles or ["creator"],
            "permissions": permissions or [],
            
            # Security claims
            "token_version": "1.0",
            "scope": "api_access"
        }
        
        # Get current signing key
        key_id, private_key = await self.key_manager.get_current_key()
        
        # Add key ID to header
        headers = {"kid": key_id}
        
        try:
            # Create token
            token = jwt.encode(
                payload,
                private_key,
                algorithm="RS256",
                headers=headers
            )
            
            logger.debug(f"Created access token for creator {creator_id} with JTI {jti}")
            return token, jti
            
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise
    
    async def verify_token(
        self,
        token: str,
        db: AsyncSession,
        check_blacklist: bool = True
    ) -> Dict[str, Any]:
        """
        Verify JWT token with comprehensive validation
        
        Args:
            token: JWT token to verify
            db: Database session for blacklist checking
            check_blacklist: Whether to check token blacklist
            
        Returns:
            Token payload if valid
            
        Raises:
            JWTError: If token is invalid
        """
        try:
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get("kid")
            
            if not key_id:
                raise JWTError("Missing key ID in token header")
            
            # Get public key for verification
            public_key = await self.key_manager.get_public_key(key_id)
            if not public_key:
                raise JWTError(f"Unknown key ID: {key_id}")
            
            # Verify token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer
            )
            
            # Additional validation
            if payload.get("type") != "access":
                raise JWTError("Invalid token type")
            
            # Check blacklist if requested
            if check_blacklist:
                jti = payload.get("jti")
                if jti and await self._is_token_blacklisted(jti, db):
                    raise JWTError("Token has been revoked")
            
            return payload
            
        except ExpiredSignatureError:
            raise JWTError("Token has expired")
        except JWTClaimsError as e:
            raise JWTError(f"Invalid token claims: {e}")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise JWTError("Token verification failed")
    
    async def blacklist_token(
        self,
        jti: str,
        creator_id: str,
        reason: str,
        expires_at: datetime,
        db: AsyncSession
    ):
        """
        Add token to blacklist
        
        Args:
            jti: JWT ID to blacklist
            creator_id: Creator who owns the token
            reason: Reason for blacklisting
            expires_at: When the token would naturally expire
            db: Database session
        """
        try:
            # Add to database blacklist
            blacklist_entry = JWTBlacklist(
                jti=jti,
                creator_id=uuid.UUID(creator_id),
                expires_at=expires_at,
                reason=reason
            )
            
            db.add(blacklist_entry)
            await db.flush()
            
            # Add to Redis cache for fast lookup
            cache_key = f"blacklist:{jti}"
            ttl = int((expires_at - datetime.utcnow()).total_seconds())
            
            if ttl > 0:
                await self.cache_manager.redis.set(
                    "system", cache_key, "blacklisted", ttl=ttl
                )
            
            logger.info(f"Token blacklisted: {jti} (reason: {reason})")
            
        except Exception as e:
            logger.error(f"Error blacklisting token {jti}: {e}")
            raise
    
    async def _is_token_blacklisted(self, jti: str, db: AsyncSession) -> bool:
        """Check if token is blacklisted"""
        try:
            # Check Redis cache first
            cache_key = f"blacklist:{jti}"
            cached_result = await self.cache_manager.redis.get("system", cache_key)
            
            if cached_result:
                return True
            
            # Check database
            result = await db.execute(
                select(JWTBlacklist).where(
                    and_(
                        JWTBlacklist.jti == jti,
                        JWTBlacklist.expires_at > datetime.utcnow()
                    )
                )
            )
            
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"Error checking blacklist for {jti}: {e}")
            return False
    
    async def cleanup_expired_blacklist(self, db: AsyncSession):
        """Clean up expired blacklist entries"""
        try:
            # Remove expired entries from database
            await db.execute(
                delete(JWTBlacklist).where(
                    JWTBlacklist.expires_at <= datetime.utcnow()
                )
            )
            
            await db.commit()
            logger.info("Cleaned up expired blacklist entries")
            
        except Exception as e:
            logger.error(f"Error cleaning up blacklist: {e}")
            await db.rollback()
    
    async def revoke_all_tokens_for_creator(
        self,
        creator_id: str,
        reason: str,
        db: AsyncSession
    ):
        """
        Revoke all tokens for a creator (security breach response)
        
        Args:
            creator_id: Creator whose tokens to revoke
            reason: Reason for revocation
            db: Database session
        """
        try:
            # Revoke all refresh tokens
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.creator_id == uuid.UUID(creator_id))
                .values(
                    revoked_at=datetime.utcnow(),
                    is_active=False
                )
            )
            
            # Note: Access tokens will be handled by blacklist on next verification
            # We can't blacklist all existing access tokens without knowing their JTIs
            
            await db.commit()
            logger.warning(f"Revoked all tokens for creator {creator_id} (reason: {reason})")
            
        except Exception as e:
            logger.error(f"Error revoking tokens for creator {creator_id}: {e}")
            await db.rollback()
            raise
    
    async def rotate_keys_if_needed(self) -> bool:
        """Check and perform key rotation if needed"""
        try:
            if await self.key_manager.check_key_rotation_needed():
                new_key_id = await self.key_manager.rotate_keys()
                logger.info(f"JWT keys rotated: new key {new_key_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error during key rotation: {e}")
            return False


# Global JWT manager instance
_jwt_manager: Optional[JWTManager] = None


async def get_jwt_manager() -> JWTManager:
    """Get global JWT manager instance"""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
        await _jwt_manager.initialize()
    return _jwt_manager


async def cleanup_jwt_manager():
    """Cleanup JWT manager resources"""
    global _jwt_manager
    if _jwt_manager is not None:
        # Perform any necessary cleanup
        _jwt_manager = None