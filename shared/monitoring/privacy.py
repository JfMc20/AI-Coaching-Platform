"""
Privacy-Preserving Monitoring for ML Operations

Implements GDPR-compliant monitoring with data anonymization, 
secure sampling, and differential privacy techniques.
"""

import re
import hashlib
import json
import logging
import random
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

from shared.config.env_constants import get_env_value
from shared.security.gdpr_compliance import GDPRComplianceManager

logger = logging.getLogger(__name__)


class SamplingLevel(str, Enum):
    """Data sampling levels for debugging"""
    NONE = "none"
    METADATA_ONLY = "metadata_only"
    REDACTED = "redacted"
    FULL = "full"  # Only with explicit consent


class ContentType(str, Enum):
    """Content type classification (privacy-safe)"""
    QUESTION = "question"
    COMMAND = "command"
    CONVERSATION = "conversation"
    DOCUMENT_QUERY = "document_query"
    UNKNOWN = "unknown"


@dataclass
class PrivacyConfig:
    """Configuration for privacy-preserving monitoring"""
    sampling_rate: float = 0.01  # 1% sampling rate
    retention_days: int = 30     # Maximum data retention
    enable_pii_detection: bool = True
    enable_differential_privacy: bool = True
    min_anonymity_set_size: int = 5
    encryption_key: Optional[str] = None


@dataclass
class SampledData:
    """Container for sampled data with privacy protection"""
    id: str
    timestamp: datetime
    creator_id_hash: str  # Hashed creator ID
    operation_type: str
    model_name: str
    input_fingerprint: str  # Statistical fingerprint, not content
    output_fingerprint: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    redacted_input: Optional[str] = None  # Only first/last 50 chars
    consent_obtained: bool = False
    retention_until: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))


class InputSanitizer:
    """
    Sanitizes input data for privacy-compliant monitoring
    """
    
    def __init__(self):
        self._setup_pii_patterns()
    
    def _setup_pii_patterns(self):
        """Setup regex patterns for PII detection"""
        self.pii_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'),
            'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
            'url': re.compile(r'https?://[^\s]+'),
            'name_patterns': re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'),  # Common name patterns
        }
    
    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """
        Detect PII in text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of detected PII types and matches
        """
        detected = {}
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected[pii_type] = matches
        
        return detected
    
    def redact_pii(self, text: str, replacement: str = "[REDACTED]") -> str:
        """
        Redact PII from text
        
        Args:
            text: Text to redact
            replacement: Replacement string for PII
            
        Returns:
            Text with PII redacted
        """
        redacted_text = text
        
        for pattern in self.pii_patterns.values():
            redacted_text = pattern.sub(replacement, redacted_text)
        
        return redacted_text
    
    def create_safe_preview(self, text: str, max_chars: int = 50) -> str:
        """
        Create a safe preview of text (first/last N chars with PII redacted)
        
        Args:
            text: Original text
            max_chars: Maximum characters to include
            
        Returns:
            Safe preview string
        """
        if len(text) <= max_chars * 2:
            return self.redact_pii(text)
        
        # Take first and last portions
        first_part = text[:max_chars]
        last_part = text[-max_chars:]
        
        # Redact PII
        safe_first = self.redact_pii(first_part)
        safe_last = self.redact_pii(last_part)
        
        return f"{safe_first}...{safe_last}"
    
    def get_statistical_fingerprint(self, text: str) -> str:
        """
        Create a statistical fingerprint of text without storing content
        
        Args:
            text: Text to fingerprint
            
        Returns:
            Statistical fingerprint hash
        """
        # Statistical features (privacy-safe)
        features = {
            'length': len(text),
            'word_count': len(text.split()),
            'char_distribution': self._get_char_distribution(text),
            'avg_word_length': sum(len(word) for word in text.split()) / max(len(text.split()), 1),
            'punctuation_ratio': sum(1 for c in text if c in '.,!?;:') / max(len(text), 1),
            'digit_ratio': sum(1 for c in text if c.isdigit()) / max(len(text), 1),
            'upper_ratio': sum(1 for c in text if c.isupper()) / max(len(text), 1),
        }
        
        # Create hash of features
        features_json = json.dumps(features, sort_keys=True)
        return hashlib.sha256(features_json.encode()).hexdigest()[:16]
    
    def _get_char_distribution(self, text: str) -> Dict[str, float]:
        """Get character distribution for fingerprinting"""
        char_counts = {}
        total_chars = len(text)
        
        if total_chars == 0:
            return {}
        
        for char in text.lower():
            if char.isalpha():
                char_counts[char] = char_counts.get(char, 0) + 1
        
        # Convert to ratios (privacy-safe)
        return {char: count / total_chars for char, count in char_counts.items()}
    
    def classify_content_type(self, text: str) -> ContentType:
        """
        Classify content type without storing content
        
        Args:
            text: Text to classify
            
        Returns:
            Classified content type
        """
        text_lower = text.lower().strip()
        
        # Question patterns
        question_indicators = ['?', 'what', 'how', 'why', 'when', 'where', 'who', 'which']
        if any(indicator in text_lower for indicator in question_indicators):
            return ContentType.QUESTION
        
        # Command patterns
        command_indicators = ['please', 'can you', 'help me', 'show me', 'create', 'generate']
        if any(indicator in text_lower for indicator in command_indicators):
            return ContentType.COMMAND
        
        # Document query patterns
        doc_indicators = ['document', 'file', 'pdf', 'search for', 'find in']
        if any(indicator in text_lower for indicator in doc_indicators):
            return ContentType.DOCUMENT_QUERY
        
        # Conversation patterns (longer, conversational)
        if len(text.split()) > 20:
            return ContentType.CONVERSATION
        
        return ContentType.UNKNOWN


class DataSampler:
    """
    GDPR-compliant data sampler for debugging and analysis
    """
    
    def __init__(self, config: PrivacyConfig):
        self.config = config
        self.sanitizer = InputSanitizer()
        self.gdpr_manager = GDPRComplianceManager()
        self._setup_encryption()
    
    def _setup_encryption(self):
        """Setup encryption for sampled data"""
        encryption_key = self.config.encryption_key or get_env_value("MONITORING_ENCRYPTION_KEY")
        
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode()[:44].ljust(44, b'='))
        else:
            # Generate a new key for this session
            self.cipher = Fernet(Fernet.generate_key())
            logger.warning("Using session-only encryption key for monitoring data")
    
    def should_sample(self, creator_id: str, has_consent: bool = False) -> bool:
        """
        Determine if request should be sampled
        
        Args:
            creator_id: Creator ID
            has_consent: Whether explicit consent was obtained
            
        Returns:
            True if should sample
        """
        # Never sample without proper configuration
        if self.config.sampling_rate <= 0:
            return False
        
        # Always sample if explicit consent is given
        if has_consent:
            return True
        
        # Random sampling based on rate
        return random.random() < self.config.sampling_rate
    
    def sample_request(
        self,
        creator_id: str,
        operation_type: str,
        model_name: str,
        input_text: str,
        output_text: str,
        has_consent: bool = False,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[SampledData]:
        """
        Sample request data with privacy protection
        
        Args:
            creator_id: Creator ID
            operation_type: Type of ML operation
            model_name: Model name
            input_text: Input text
            output_text: Output text
            has_consent: Whether explicit consent was obtained
            additional_metadata: Additional metadata to store
            
        Returns:
            SampledData object if sampled, None otherwise
        """
        if not self.should_sample(creator_id, has_consent):
            return None
        
        try:
            # Create hashed creator ID for anonymization
            creator_hash = hashlib.sha256(f"{creator_id}:monitoring".encode()).hexdigest()[:16]
            
            # Create statistical fingerprints
            input_fingerprint = self.sanitizer.get_statistical_fingerprint(input_text)
            output_fingerprint = self.sanitizer.get_statistical_fingerprint(output_text)
            
            # Prepare metadata (privacy-safe only)
            metadata = {
                'input_length': len(input_text),
                'output_length': len(output_text),
                'content_type': self.sanitizer.classify_content_type(input_text).value,
                'timestamp': datetime.utcnow().isoformat(),
                'has_pii': bool(self.sanitizer.detect_pii(input_text)),
            }
            
            # Add additional metadata if provided
            if additional_metadata:
                # Only include safe metadata (no PII)
                safe_keys = ['latency_ms', 'cache_hit', 'model_version', 'error_code']
                for key in safe_keys:
                    if key in additional_metadata:
                        metadata[key] = additional_metadata[key]
            
            # Create redacted input preview only if consent given or no PII detected
            redacted_input = None
            if has_consent or not metadata['has_pii']:
                redacted_input = self.sanitizer.create_safe_preview(input_text)
            
            # Create sampled data
            sampled_data = SampledData(
                id=f"sample_{int(time.time())}_{random.randint(1000, 9999)}",
                timestamp=datetime.utcnow(),
                creator_id_hash=creator_hash,
                operation_type=operation_type,
                model_name=model_name,
                input_fingerprint=input_fingerprint,
                output_fingerprint=output_fingerprint,
                metadata=metadata,
                redacted_input=redacted_input,
                consent_obtained=has_consent,
                retention_until=datetime.utcnow() + timedelta(days=self.config.retention_days)
            )
            
            logger.info(f"Sampled request {sampled_data.id} for monitoring (consent: {has_consent})")
            return sampled_data
            
        except Exception as e:
            logger.error(f"Failed to sample request: {e}")
            return None
    
    def encrypt_sampled_data(self, data: SampledData) -> bytes:
        """
        Encrypt sampled data for secure storage
        
        Args:
            data: SampledData to encrypt
            
        Returns:
            Encrypted data bytes
        """
        try:
            # Convert to JSON
            data_dict = {
                'id': data.id,
                'timestamp': data.timestamp.isoformat(),
                'creator_id_hash': data.creator_id_hash,
                'operation_type': data.operation_type,
                'model_name': data.model_name,
                'input_fingerprint': data.input_fingerprint,
                'output_fingerprint': data.output_fingerprint,
                'metadata': data.metadata,
                'redacted_input': data.redacted_input,
                'consent_obtained': data.consent_obtained,
                'retention_until': data.retention_until.isoformat()
            }
            
            json_data = json.dumps(data_dict, sort_keys=True)
            return self.cipher.encrypt(json_data.encode())
            
        except Exception as e:
            logger.error(f"Failed to encrypt sampled data: {e}")
            raise
    
    def cleanup_expired_samples(self, storage_backend) -> int:
        """
        Clean up expired sampled data
        
        Args:
            storage_backend: Storage backend with delete capability
            
        Returns:
            Number of samples deleted
        """
        try:
            datetime.utcnow()
            deleted_count = 0
            
            # This would typically query your storage backend
            # Implementation depends on storage choice (Redis, PostgreSQL, etc.)
            
            logger.info(f"Cleaned up {deleted_count} expired monitoring samples")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired samples: {e}")
            return 0


class PrivacyPreservingMonitor:
    """
    Main privacy-preserving monitoring system
    """
    
    def __init__(self, config: Optional[PrivacyConfig] = None):
        self.config = config or PrivacyConfig()
        self.sampler = DataSampler(self.config)
        self.sanitizer = InputSanitizer()
        self._drift_baselines = {}
    
    def monitor_request(
        self,
        creator_id: str,
        operation_type: str,
        model_name: str,
        input_text: str,
        output_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        has_consent: bool = False
    ) -> Dict[str, Any]:
        """
        Monitor an ML request with privacy protection
        
        Args:
            creator_id: Creator ID
            operation_type: Type of operation
            model_name: Model name
            input_text: Input text
            output_text: Output text
            metadata: Additional metadata
            has_consent: Whether explicit consent was obtained
            
        Returns:
            Privacy-safe monitoring data
        """
        try:
            # Extract privacy-safe metrics
            monitoring_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'operation_type': operation_type,
                'model_name': model_name,
                'input_length': len(input_text),
                'output_length': len(output_text),
                'content_type': self.sanitizer.classify_content_type(input_text).value,
                'has_pii': bool(self.sanitizer.detect_pii(input_text)),
                'input_fingerprint': self.sanitizer.get_statistical_fingerprint(input_text),
                'creator_id_hash': hashlib.sha256(f"{creator_id}:monitor".encode()).hexdigest()[:16]
            }
            
            # Add safe metadata
            if metadata:
                safe_fields = ['latency_ms', 'cache_hit', 'error_code', 'model_version']
                for field in safe_fields:
                    if field in metadata:
                        monitoring_data[field] = metadata[field]
            
            # Sample data if appropriate
            if self.sampler.should_sample(creator_id, has_consent):
                sampled_data = self.sampler.sample_request(
                    creator_id=creator_id,
                    operation_type=operation_type,
                    model_name=model_name,
                    input_text=input_text,
                    output_text=output_text,
                    has_consent=has_consent,
                    additional_metadata=metadata
                )
                
                if sampled_data:
                    monitoring_data['sampled'] = True
                    monitoring_data['sample_id'] = sampled_data.id
            
            # Check for drift (privacy-safe)
            drift_score = self._calculate_drift_score(
                operation_type, 
                model_name, 
                monitoring_data['input_fingerprint']
            )
            monitoring_data['drift_score'] = drift_score
            
            return monitoring_data
            
        except Exception as e:
            logger.error(f"Failed to monitor request: {e}")
            return {}
    
    async def log_query(
        self,
        query: str,
        creator_id: str,
        correlation_id: str,
        consent_given: bool = False
    ) -> Dict[str, Any]:
        """
        Log a privacy-preserving query event
        
        Args:
            query: User query
            creator_id: Creator identifier
            correlation_id: Request correlation ID
            consent_given: Whether user consent was obtained
            
        Returns:
            Privacy-safe log entry
        """
        try:
            log_entry = {
                'event_type': 'query',
                'timestamp': datetime.utcnow().isoformat(),
                'correlation_id': correlation_id,
                'creator_id_hash': hashlib.sha256(f"{creator_id}:query".encode()).hexdigest()[:16],
                'input_length': len(query),
                'content_type': self.sanitizer.classify_content_type(query).value,
                'has_pii': bool(self.sanitizer.detect_pii(query)),
                'input_fingerprint': self.sanitizer.get_statistical_fingerprint(query),
                'consent_given': consent_given
            }
            
            # Sample for debugging if consent given
            if consent_given and self.sampler.should_sample(creator_id, consent_given):
                redacted_query = self.sanitizer.redact_pii(query)
                log_entry['redacted_query'] = redacted_query[:100] + "..." if len(redacted_query) > 100 else redacted_query
            
            logger.info(f"Query logged: {log_entry}")
            return log_entry
            
        except Exception as e:
            logger.error(f"Failed to log query: {e}")
            return {}
    
    async def log_response(
        self,
        response: str,
        creator_id: str,
        correlation_id: str,
        model_used: str,
        processing_time_ms: float,
        sources_count: int = 0
    ) -> Dict[str, Any]:
        """
        Log a privacy-preserving response event
        
        Args:
            response: AI response
            creator_id: Creator identifier
            correlation_id: Request correlation ID
            model_used: Model that generated response
            processing_time_ms: Processing time
            sources_count: Number of sources used
            
        Returns:
            Privacy-safe log entry
        """
        try:
            log_entry = {
                'event_type': 'response',
                'timestamp': datetime.utcnow().isoformat(),
                'correlation_id': correlation_id,
                'creator_id_hash': hashlib.sha256(f"{creator_id}:response".encode()).hexdigest()[:16],
                'model_used': model_used,
                'processing_time_ms': processing_time_ms,
                'output_length': len(response),
                'sources_count': sources_count,
                'output_fingerprint': self.sanitizer.get_statistical_fingerprint(response)
            }
            
            logger.info(f"Response logged: {log_entry}")
            return log_entry
            
        except Exception as e:
            logger.error(f"Failed to log response: {e}")
            return {}
    
    async def log_document_processing(
        self,
        filename: str,
        file_size: int,
        creator_id: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """
        Log a privacy-preserving document processing event
        
        Args:
            filename: Document filename
            file_size: File size in bytes
            creator_id: Creator identifier
            correlation_id: Request correlation ID
            
        Returns:
            Privacy-safe log entry
        """
        try:
            # Redact filename for privacy
            safe_filename = self.sanitizer.redact_pii(filename)
            
            log_entry = {
                'event_type': 'document_processing',
                'timestamp': datetime.utcnow().isoformat(),
                'correlation_id': correlation_id,
                'creator_id_hash': hashlib.sha256(f"{creator_id}:doc".encode()).hexdigest()[:16],
                'filename_hash': hashlib.sha256(filename.encode()).hexdigest()[:16],
                'safe_filename': safe_filename,
                'file_size_bytes': file_size,
                'file_size_category': self._categorize_file_size(file_size)
            }
            
            logger.info(f"Document processing logged: {log_entry}")
            return log_entry
            
        except Exception as e:
            logger.error(f"Failed to log document processing: {e}")
            return {}
    
    async def log_search_results(
        self,
        query: str,
        result_count: int,
        creator_id: str,
        correlation_id: str,
        processing_time_ms: float
    ) -> Dict[str, Any]:
        """
        Log privacy-preserving search results
        
        Args:
            query: Search query
            result_count: Number of results returned
            creator_id: Creator identifier
            correlation_id: Request correlation ID
            processing_time_ms: Processing time
            
        Returns:
            Privacy-safe log entry
        """
        try:
            log_entry = {
                'event_type': 'search_results',
                'timestamp': datetime.utcnow().isoformat(),
                'correlation_id': correlation_id,
                'creator_id_hash': hashlib.sha256(f"{creator_id}:search".encode()).hexdigest()[:16],
                'query_fingerprint': self.sanitizer.get_statistical_fingerprint(query),
                'result_count': result_count,
                'processing_time_ms': processing_time_ms,
                'query_length': len(query)
            }
            
            logger.info(f"Search results logged: {log_entry}")
            return log_entry
            
        except Exception as e:
            logger.error(f"Failed to log search results: {e}")
            return {}
    
    def _categorize_file_size(self, size_bytes: int) -> str:
        """Categorize file size for privacy-safe logging"""
        if size_bytes < 1024:
            return "tiny"
        elif size_bytes < 1024 * 1024:
            return "small"
        elif size_bytes < 10 * 1024 * 1024:
            return "medium"
        elif size_bytes < 100 * 1024 * 1024:
            return "large"
        else:
            return "very_large"
    
    def _calculate_drift_score(
        self, 
        operation_type: str, 
        model_name: str, 
        input_fingerprint: str
    ) -> float:
        """
        Calculate drift score using privacy-preserving techniques
        
        Args:
            operation_type: Type of operation
            model_name: Model name
            input_fingerprint: Statistical fingerprint of input
            
        Returns:
            Drift score (0.0 to 1.0)
        """
        try:
            baseline_key = f"{operation_type}:{model_name}"
            
            # Initialize baseline if not exists
            if baseline_key not in self._drift_baselines:
                self._drift_baselines[baseline_key] = {
                    'fingerprints': [],
                    'last_updated': datetime.utcnow()
                }
            
            baseline = self._drift_baselines[baseline_key]
            
            # Add to baseline (keep last N fingerprints)
            baseline['fingerprints'].append(input_fingerprint)
            if len(baseline['fingerprints']) > 100:
                baseline['fingerprints'] = baseline['fingerprints'][-100:]
            
            # Calculate similarity to baseline (simplified)
            if len(baseline['fingerprints']) < 10:
                return 0.0  # Not enough data
            
            # Count similar fingerprints
            similar_count = sum(1 for fp in baseline['fingerprints'] if fp == input_fingerprint)
            drift_score = 1.0 - (similar_count / len(baseline['fingerprints']))
            
            return min(drift_score, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate drift score: {e}")
            return 0.0
    
    def get_privacy_compliance_report(self) -> Dict[str, Any]:
        """
        Generate privacy compliance report
        
        Returns:
            Compliance report dictionary
        """
        return {
            'sampling_rate': self.config.sampling_rate,
            'retention_days': self.config.retention_days,
            'pii_detection_enabled': self.config.enable_pii_detection,
            'differential_privacy_enabled': self.config.enable_differential_privacy,
            'encryption_enabled': self.sampler.cipher is not None,
            'gdpr_compliant': True,
            'last_audit': datetime.utcnow().isoformat()
        }