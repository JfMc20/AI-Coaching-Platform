/**
 * Hooks Export Index
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

// Program Management
export { usePrograms, useProgram } from './usePrograms';

// Knowledge & Personality Management
export { useKnowledge, usePersonality, useCreatorProfile } from './useKnowledge';

// Program Validation
export { useProgramValidation } from './useProgramValidation';

// Canvas API Integration
export { useCanvasAPI } from './useCanvasAPI';

// Re-export store hooks for convenience
export { useAuthStore } from '@/stores/authStore';
export { useCanvasStore } from '@/stores/canvasStore';