/**
 * Authentication Store - Zustand State Management
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, AuthTokens, LoginRequest } from '@/types';
import { ENV_CONFIG } from '@/config/environment';

interface AuthState {
  // Authentication State
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Development Mode State
  isDeveloper: boolean;
  devModeEnabled: boolean;

  // Actions
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  setUser: (user: User | null) => void;
  setTokens: (tokens: AuthTokens | null) => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
  
  // Development Actions
  enableDevMode: () => void;
  disableDevMode: () => void;
  setDeveloper: (isDeveloper: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial State
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      isDeveloper: false,
      devModeEnabled: ENV_CONFIG.DEVELOPMENT_MODE,

      // Authentication Actions
      login: async (credentials: LoginRequest) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials),
          });

          if (!response.ok) {
            throw new Error('Login failed');
          }

          const data = await response.json();
          
          set({
            user: data.creator,
            tokens: data.tokens,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });

          // Store tokens in localStorage for persistence
          if (typeof window !== 'undefined') {
            localStorage.setItem(ENV_CONFIG.JWT_STORAGE_KEY, data.tokens.access_token);
            localStorage.setItem(ENV_CONFIG.REFRESH_TOKEN_KEY, data.tokens.refresh_token);
          }

        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Login failed',
            isLoading: false,
            isAuthenticated: false,
          });
          throw error;
        }
      },

      logout: () => {
        // Clear tokens from localStorage
        if (typeof window !== 'undefined') {
          localStorage.removeItem(ENV_CONFIG.JWT_STORAGE_KEY);
          localStorage.removeItem(ENV_CONFIG.REFRESH_TOKEN_KEY);
        }

        set({
          user: null,
          tokens: null,
          isAuthenticated: false,
          error: null,
        });
      },

      refreshToken: async () => {
        const { tokens } = get();
        if (!tokens?.refresh_token) {
          throw new Error('No refresh token available');
        }

        try {
          const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              refresh_token: tokens.refresh_token,
            }),
          });

          if (!response.ok) {
            throw new Error('Token refresh failed');
          }

          const newTokens = await response.json();
          
          set({ tokens: newTokens });

          // Update tokens in localStorage
          if (typeof window !== 'undefined') {
            localStorage.setItem(ENV_CONFIG.JWT_STORAGE_KEY, newTokens.access_token);
            localStorage.setItem(ENV_CONFIG.REFRESH_TOKEN_KEY, newTokens.refresh_token);
          }

        } catch (error) {
          // If refresh fails, logout user
          get().logout();
          throw error;
        }
      },

      setUser: (user: User | null) => {
        set({ user, isAuthenticated: !!user });
      },

      setTokens: (tokens: AuthTokens | null) => {
        set({ tokens });
      },

      setError: (error: string | null) => {
        set({ error });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      // Development Actions
      enableDevMode: () => {
        set({ devModeEnabled: true });
      },

      disableDevMode: () => {
        set({ devModeEnabled: false });
      },

      setDeveloper: (isDeveloper: boolean) => {
        set({ isDeveloper });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
        isDeveloper: state.isDeveloper,
        devModeEnabled: state.devModeEnabled,
      }),
    }
  )
);

// Helper function to check if user is authenticated with valid tokens
export function useIsAuthenticated(): boolean {
  const { isAuthenticated, tokens } = useAuthStore();
  
  if (!isAuthenticated || !tokens) {
    return false;
  }

  // Check if token is expired
  try {
    const payload = JSON.parse(atob(tokens.access_token.split('.')[1]));
    const now = Date.now() / 1000;
    
    if (payload.exp < now) {
      // Token is expired, attempt refresh
      useAuthStore.getState().refreshToken().catch(() => {
        useAuthStore.getState().logout();
      });
      return false;
    }
    
    return true;
  } catch {
    return false;
  }
}

// Helper function to get authorization header
export function getAuthHeader(): string | null {
  const { tokens } = useAuthStore.getState();
  return tokens ? `Bearer ${tokens.access_token}` : null;
}