"""Custom JSON encoders and decoders"""

import json
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from enum import Enum


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for common Python types"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, 'dict'):
            # Handle Pydantic models
            return obj.dict()
        return super().default(obj)