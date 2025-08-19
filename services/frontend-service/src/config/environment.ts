/**
 * Environment Configuration
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

export const ENV_CONFIG = {
  // Service URLs (defaults for development)
  AUTH_SERVICE_URL: process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://localhost:8001',
  CREATOR_HUB_SERVICE_URL: process.env.NEXT_PUBLIC_CREATOR_HUB_SERVICE_URL || 'http://localhost:8002',
  AI_ENGINE_SERVICE_URL: process.env.NEXT_PUBLIC_AI_ENGINE_SERVICE_URL || 'http://localhost:8003',
  CHANNEL_SERVICE_URL: process.env.NEXT_PUBLIC_CHANNEL_SERVICE_URL || 'http://localhost:8004',
  
  // Development Configuration
  DEVELOPMENT_MODE: process.env.NODE_ENV === 'development',
  
  // Frontend Service Configuration
  FRONTEND_PORT: process.env.PORT || '8006',
  
  // Protected Routes Configuration
  ENABLE_DEV_ROUTES: process.env.NEXT_PUBLIC_ENABLE_DEV_ROUTES === 'true' || process.env.NODE_ENV === 'development',
  
  // API Configuration
  API_TIMEOUT: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '10000'),
  
  // Authentication Configuration
  JWT_STORAGE_KEY: 'ai_coaching_platform_token',
  REFRESH_TOKEN_KEY: 'ai_coaching_platform_refresh_token',
  
  // Canvas Configuration
  AUTOSAVE_INTERVAL: parseInt(process.env.NEXT_PUBLIC_AUTOSAVE_INTERVAL || '30000'), // 30 seconds
  MAX_NODES_PER_PROGRAM: parseInt(process.env.NEXT_PUBLIC_MAX_NODES_PER_PROGRAM || '50'),
  
  // Debugging
  DEBUG_MODE: process.env.NEXT_PUBLIC_DEBUG_MODE === 'true',
} as const;

export type EnvironmentConfig = typeof ENV_CONFIG;

// Validation function for required environment variables
export function validateEnvironment(): void {
  const requiredVars = [
    'NEXT_PUBLIC_AUTH_SERVICE_URL',
    'NEXT_PUBLIC_CREATOR_HUB_SERVICE_URL',
    'NEXT_PUBLIC_AI_ENGINE_SERVICE_URL',
  ];

  const missing = requiredVars.filter(varName => !process.env[varName] && ENV_CONFIG.DEVELOPMENT_MODE);
  
  if (missing.length > 0 && ENV_CONFIG.DEVELOPMENT_MODE) {
    console.warn(`⚠️  Missing environment variables (using defaults): ${missing.join(', ')}`);
  }
}

// Helper function to check if we're in protected development mode
export function isProtectedDevMode(): boolean {
  return ENV_CONFIG.DEVELOPMENT_MODE && ENV_CONFIG.ENABLE_DEV_ROUTES;
}