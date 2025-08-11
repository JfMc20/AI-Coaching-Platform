# Coding Standards and Guidelines

## Overview

This document establishes comprehensive coding standards for the multi-channel proactive coaching platform, covering Python (FastAPI), JavaScript/TypeScript (React, React Native), code formatting, naming conventions, documentation requirements, and code review guidelines.

## General Principles

### Code Quality Principles
1. **Readability First**: Code should be self-documenting and easy to understand
2. **Consistency**: Follow established patterns and conventions throughout the codebase
3. **Maintainability**: Write code that is easy to modify and extend
4. **Performance**: Consider performance implications without premature optimization
5. **Security**: Follow security best practices and validate all inputs
6. **Testability**: Write code that is easy to test and debug

## Python/FastAPI Standards

### Code Formatting and Style
```python
# Use Black for code formatting with line length of 88 characters
# pyproject.toml configuration
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

# Use isort for import sorting
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["app", "core", "api", "models", "services"]
```

### Import Organization
```python
# Standard library imports
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from uuid import UUID

# Third-party imports
import httpx
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

# Local application imports
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.ai_service import AIService
from app.utils.helpers import generate_uuid
```

### Naming Conventions
```python
# Constants - ALL_CAPS with underscores
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 30
API_VERSION = "v1"

# Variables and functions - snake_case
user_id = "12345"
conversation_history = []
def calculate_engagement_score(user_data: Dict) -> float:
    pass

# Classes - PascalCase
class UserProfileManager:
    pass

class ConversationAIService:
    pass

# Private methods and variables - leading underscore
class DataProcessor:
    def __init__(self):
        self._internal_cache = {}
    
    def _validate_input(self, data: Dict) -> bool:
        pass

# Constants within classes - ALL_CAPS
class APIConfig:
    MAX_REQUESTS_PER_MINUTE = 100
    DEFAULT_PAGE_SIZE = 20
```

### Type Hints and Documentation
```python
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel
from datetime import datetime

class UserProfile(BaseModel):
    """User profile model with comprehensive type hints and validation.
    
    Attributes:
        user_id: Unique identifier for the user
        name: User's display name
        goals: List of user's coaching goals
        preferences: User preferences dictionary
        created_at: Timestamp when profile was created
        updated_at: Timestamp when profile was last updated
    """
    user_id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., min_length=1, max_length=100)
    goals: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None

async def process_user_message(
    message: str,
    user_id: str,
    conversation_context: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Union[str, float, List[str]]]:
    """Process user message and generate AI response.
    
    Args:
        message: The user's input message
        user_id: Unique identifier for the user
        conversation_context: Optional context from previous conversation
        db: Database session dependency
    
    Returns:
        Dictionary containing:
            - response: Generated AI response text
            - confidence: Confidence score (0.0-1.0)
            - sources: List of knowledge sources used
    
    Raises:
        HTTPException: If user not found or processing fails
        ValidationError: If message format is invalid
    """
    if not message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )
    
    # Implementation here
    pass
```

### Error Handling
```python
import logging
from fastapi import HTTPException, status
from typing import Optional

logger = logging.getLogger(__name__)

class CoachingPlatformException(Exception):
    """Base exception for coaching platform errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class UserNotFoundError(CoachingPlatformException):
    """Raised when a user is not found."""
    pass

class AIServiceError(CoachingPlatformException):
    """Raised when AI service encounters an error."""
    pass

async def safe_ai_generation(
    prompt: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    """Safely generate AI response with retry logic and error handling.
    
    Args:
        prompt: Input prompt for AI generation
        max_retries: Maximum number of retry attempts
    
    Returns:
        Generated response data
    
    Raises:
        AIServiceError: If generation fails after all retries
    """
    for attempt in range(max_retries):
        try:
            response = await ai_service.generate_response(prompt)
            return response
        except Exception as e:
            logger.warning(
                f"AI generation attempt {attempt + 1} failed: {str(e)}"
            )
            if attempt == max_retries - 1:
                logger.error(f"AI generation failed after {max_retries} attempts")
                raise AIServiceError(
                    f"Failed to generate AI response: {str(e)}",
                    error_code="AI_GENERATION_FAILED"
                )
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Async/Await Best Practices
```python
import asyncio
from typing import List, Dict, Any
import httpx

async def fetch_user_data(user_id: str) -> Dict[str, Any]:
    """Fetch user data asynchronously."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/api/users/{user_id}")
        response.raise_for_status()
        return response.json()

async def process_multiple_users(user_ids: List[str]) -> List[Dict[str, Any]]:
    """Process multiple users concurrently."""
    tasks = [fetch_user_data(user_id) for user_id in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle exceptions in results
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Failed to process user {user_ids[i]}: {result}")
        else:
            processed_results.append(result)
    
    return processed_results

# Use context managers for resource management
async def process_with_database():
    async with get_async_db_session() as db:
        # Database operations here
        user = await db.get(User, user_id)
        # Session automatically closed
```

## JavaScript/TypeScript Standards

### TypeScript Configuration
```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["DOM", "DOM.Iterable", "ES6"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": "src",
    "paths": {
      "@/*": ["*"],
      "@/components/*": ["components/*"],
      "@/services/*": ["services/*"],
      "@/utils/*": ["utils/*"],
      "@/types/*": ["types/*"]
    }
  },
  "include": [
    "src"
  ]
}
```

### Code Formatting (Prettier)
```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "avoid",
  "endOfLine": "lf"
}
```

### Naming Conventions
```typescript
// Constants - ALL_CAPS with underscores
const MAX_MESSAGE_LENGTH = 2000;
const API_ENDPOINTS = {
  USERS: '/api/users',
  CONVERSATIONS: '/api/conversations',
} as const;

// Variables and functions - camelCase
const userId = '12345';
const conversationHistory: Message[] = [];

const calculateEngagementScore = (userData: UserData): number => {
  // Implementation
  return 0.85;
};

// Types and Interfaces - PascalCase
interface UserProfile {
  id: string;
  name: string;
  goals: string[];
  preferences: UserPreferences;
}

type ConversationState = 'active' | 'paused' | 'completed';

// Components - PascalCase
const UserProfileCard: React.FC<UserProfileCardProps> = ({ user }) => {
  return <div>{user.name}</div>;
};

// Enums - PascalCase with PascalCase values
enum MessageType {
  Text = 'TEXT',
  Image = 'IMAGE',
  Audio = 'AUDIO',
}
```

### Type Definitions
```typescript
// types/user.ts
export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface UserProfile {
  userId: string;
  goals: Goal[];
  preferences: UserPreferences;
  progressData: ProgressData;
}

export interface Goal {
  id: string;
  title: string;
  description: string;
  targetDate: Date;
  status: GoalStatus;
  progress: number; // 0-1
}

export type GoalStatus = 'active' | 'completed' | 'paused' | 'cancelled';

// Use utility types for common patterns
export type CreateUserRequest = Omit<User, 'id' | 'createdAt' | 'updatedAt'>;
export type UpdateUserRequest = Partial<Pick<User, 'name' | 'email'>>;

// Generic types for API responses
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  errors?: string[];
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}
```

### React Component Standards
```typescript
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { User, UserProfile } from '@/types/user';
import { useUserProfile } from '@/hooks/useUserProfile';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface UserProfileCardProps {
  userId: string;
  onProfileUpdate?: (profile: UserProfile) => void;
  className?: string;
}

/**
 * UserProfileCard component displays user profile information
 * with editing capabilities.
 */
export const UserProfileCard: React.FC<UserProfileCardProps> = ({
  userId,
  onProfileUpdate,
  className = '',
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const { profile, loading, error, updateProfile } = useUserProfile(userId);

  // Memoize expensive calculations
  const completionPercentage = useMemo(() => {
    if (!profile?.goals) return 0;
    const completedGoals = profile.goals.filter(goal => goal.status === 'completed');
    return (completedGoals.length / profile.goals.length) * 100;
  }, [profile?.goals]);

  // Use useCallback for event handlers
  const handleSaveProfile = useCallback(async (updatedProfile: UserProfile) => {
    try {
      await updateProfile(updatedProfile);
      onProfileUpdate?.(updatedProfile);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update profile:', error);
    }
  }, [updateProfile, onProfileUpdate]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <div className="error">Error loading profile: {error.message}</div>;
  }

  return (
    <div className={`user-profile-card ${className}`}>
      <div className="profile-header">
        <h2>{profile?.name}</h2>
        <Button
          variant="secondary"
          onClick={() => setIsEditing(!isEditing)}
        >
          {isEditing ? 'Cancel' : 'Edit'}
        </Button>
      </div>
      
      <div className="profile-content">
        <div className="goals-section">
          <h3>Goals ({profile?.goals?.length || 0})</h3>
          <div className="completion-bar">
            <div 
              className="completion-fill"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// Default export for the component
export default UserProfileCard;
```

### Custom Hooks
```typescript
import { useState, useEffect, useCallback } from 'react';
import { UserProfile } from '@/types/user';
import { userService } from '@/services/userService';

interface UseUserProfileReturn {
  profile: UserProfile | null;
  loading: boolean;
  error: Error | null;
  updateProfile: (profile: UserProfile) => Promise<void>;
  refreshProfile: () => Promise<void>;
}

/**
 * Custom hook for managing user profile data
 */
export const useUserProfile = (userId: string): UseUserProfileReturn => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchProfile = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const profileData = await userService.getProfile(userId);
      setProfile(profileData);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const updateProfile = useCallback(async (updatedProfile: UserProfile) => {
    try {
      const updated = await userService.updateProfile(userId, updatedProfile);
      setProfile(updated);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Update failed'));
      throw err; // Re-throw to allow component to handle
    }
  }, [userId]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  return {
    profile,
    loading,
    error,
    updateProfile,
    refreshProfile: fetchProfile,
  };
};
```

## Testing Standards

### Python Testing (pytest)
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.ai_service import AIService
from app.models.user import User

# Test client setup
client = TestClient(app)

class TestUserAPI:
    """Test suite for User API endpoints."""
    
    @pytest.fixture
    def mock_user(self):
        """Fixture providing a mock user object."""
        return User(
            id="test-user-123",
            email="test@example.com",
            name="Test User",
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def mock_db_session(self):
        """Fixture providing a mock database session."""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value = mock_session
            yield mock_session
    
    def test_get_user_success(self, mock_db_session, mock_user):
        """Test successful user retrieval."""
        # Arrange
        mock_db_session.get.return_value = mock_user
        
        # Act
        response = client.get(f"/api/users/{mock_user.id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_user.id
        assert data["email"] == mock_user.email
    
    def test_get_user_not_found(self, mock_db_session):
        """Test user not found scenario."""
        # Arrange
        mock_db_session.get.return_value = None
        
        # Act
        response = client.get("/api/users/nonexistent-id")
        
        # Assert
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_ai_service_integration(self):
        """Test AI service integration."""
        # Arrange
        ai_service = AIService()
        test_prompt = "Hello, how are you?"
        
        with patch.object(ai_service, 'generate_response', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = {
                "response": "I'm doing well, thank you!",
                "confidence": 0.95
            }
            
            # Act
            result = await ai_service.generate_response(test_prompt)
            
            # Assert
            assert result["response"] == "I'm doing well, thank you!"
            assert result["confidence"] == 0.95
            mock_generate.assert_called_once_with(test_prompt)

# Parametrized tests
@pytest.mark.parametrize("input_data,expected_status", [
    ({"name": "Valid Name", "email": "valid@email.com"}, 201),
    ({"name": "", "email": "valid@email.com"}, 422),
    ({"name": "Valid Name", "email": "invalid-email"}, 422),
    ({}, 422),
])
def test_create_user_validation(input_data, expected_status):
    """Test user creation with various input validation scenarios."""
    response = client.post("/api/users", json=input_data)
    assert response.status_code == expected_status
```

### JavaScript/TypeScript Testing (Jest + React Testing Library)
```typescript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserProfileCard } from '@/components/UserProfileCard';
import { useUserProfile } from '@/hooks/useUserProfile';
import { UserProfile } from '@/types/user';

// Mock the custom hook
jest.mock('@/hooks/useUserProfile');
const mockUseUserProfile = useUserProfile as jest.MockedFunction<typeof useUserProfile>;

describe('UserProfileCard', () => {
  const mockProfile: UserProfile = {
    userId: 'test-user-123',
    goals: [
      { id: '1', title: 'Goal 1', status: 'active', progress: 0.5 },
      { id: '2', title: 'Goal 2', status: 'completed', progress: 1.0 },
    ],
    preferences: {},
    progressData: {},
  };

  beforeEach(() => {
    mockUseUserProfile.mockReturnValue({
      profile: mockProfile,
      loading: false,
      error: null,
      updateProfile: jest.fn(),
      refreshProfile: jest.fn(),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders user profile information', () => {
    render(<UserProfileCard userId="test-user-123" />);
    
    expect(screen.getByText('Goals (2)')).toBeInTheDocument();
    expect(screen.getByText('Edit')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockUseUserProfile.mockReturnValue({
      profile: null,
      loading: true,
      error: null,
      updateProfile: jest.fn(),
      refreshProfile: jest.fn(),
    });

    render(<UserProfileCard userId="test-user-123" />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('shows error state', () => {
    const error = new Error('Failed to load profile');
    mockUseUserProfile.mockReturnValue({
      profile: null,
      loading: false,
      error,
      updateProfile: jest.fn(),
      refreshProfile: jest.fn(),
    });

    render(<UserProfileCard userId="test-user-123" />);
    
    expect(screen.getByText(/Error loading profile/)).toBeInTheDocument();
  });

  it('calls onProfileUpdate when profile is updated', async () => {
    const mockOnProfileUpdate = jest.fn();
    const mockUpdateProfile = jest.fn().mockResolvedValue(undefined);
    
    mockUseUserProfile.mockReturnValue({
      profile: mockProfile,
      loading: false,
      error: null,
      updateProfile: mockUpdateProfile,
      refreshProfile: jest.fn(),
    });

    render(
      <UserProfileCard 
        userId="test-user-123" 
        onProfileUpdate={mockOnProfileUpdate}
      />
    );

    // Click edit button
    fireEvent.click(screen.getByText('Edit'));
    
    // Simulate profile update (this would depend on your actual edit UI)
    // For this example, assume there's a save button that appears
    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockUpdateProfile).toHaveBeenCalled();
      expect(mockOnProfileUpdate).toHaveBeenCalledWith(mockProfile);
    });
  });
});

// Service testing
import { userService } from '@/services/userService';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  http.get('/api/users/:userId/profile', ({ params }) => {
    return HttpResponse.json({
      userId: params.userId,
      goals: [],
      preferences: {},
      progressData: {},
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('userService', () => {
  it('fetches user profile successfully', async () => {
    const profile = await userService.getProfile('test-user-123');
    
    expect(profile.userId).toBe('test-user-123');
    expect(Array.isArray(profile.goals)).toBe(true);
  });

  it('handles API errors gracefully', async () => {
    server.use(
      http.get('/api/users/:userId/profile', () => {
        return new HttpResponse(null, { status: 404 });
      })
    );

    await expect(userService.getProfile('nonexistent')).rejects.toThrow();
  });
});
```

## Code Review Guidelines

### Review Checklist
- [ ] Code follows established style guidelines
- [ ] All functions and classes have appropriate documentation
- [ ] Error handling is comprehensive and appropriate
- [ ] Tests are included and cover edge cases
- [ ] Security considerations are addressed
- [ ] Performance implications are considered
- [ ] Code is DRY (Don't Repeat Yourself)
- [ ] Variable and function names are descriptive
- [ ] Complex logic is commented and explained
- [ ] Dependencies are justified and minimal

### Review Process
1. **Automated Checks**: All automated tests and linting must pass
2. **Self Review**: Author reviews their own code before requesting review
3. **Peer Review**: At least one team member reviews the code
4. **Security Review**: Security-sensitive changes require security team review
5. **Documentation**: Update relevant documentation with code changes

This comprehensive coding standards document ensures consistency, maintainability, and quality across the entire codebase while supporting team collaboration and code review processes.