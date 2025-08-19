/**
 * Development Authentication Wrapper
 * Frontend Service - Multi-Channel AI Coaching Platform
 * 
 * Protected routes for internal development use only
 */

'use client';

import React, { useEffect, useState } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { isProtectedDevMode, ENV_CONFIG } from '@/config/environment';

interface DevAuthWrapperProps {
  children: React.ReactNode;
}

const DevAuthWrapper: React.FC<DevAuthWrapperProps> = ({ children }) => {
  const [isAuthorized, setIsAuthorized] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [devPassword, setDevPassword] = useState<string>(''); // 👈 aseguramos que sea string
  const [error, setError] = useState<string>('');

  const { isDeveloper, setDeveloper } = useAuthStore();

  useEffect(() => {
    // Check if dev mode is enabled
    if (!isProtectedDevMode()) {
      setError('Development routes are disabled in this environment');
      setLoading(false);
      return;
    }

    // Check if already authorized in session
    const sessionAuth = sessionStorage.getItem('dev_auth_session');
    if (sessionAuth === 'authorized') {
      setIsAuthorized(true);
      setDeveloper(true);
    }

    setLoading(false);
  }, [setDeveloper]);

  const handleDevAuth = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const validPasswords = [
      'dev2025',
      'coaching-ai-dev',
      'visual-program-builder'
    ];

    if (validPasswords.includes(devPassword)) {
      setIsAuthorized(true);
      setDeveloper(true);
      sessionStorage.setItem('dev_auth_session', 'authorized');
    } else {
      setError('Invalid development access code');
    }
  };

  const handleLogout = () => {
    setIsAuthorized(false);
    setDeveloper(false);
    sessionStorage.removeItem('dev_auth_session');
    setDevPassword('');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isProtectedDevMode()) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-lg text-center">
          <div className="text-6xl mb-4">🚫</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Access Restricted
          </h1>
          <p className="text-gray-600 mb-4">
            Development routes are not available in this environment.
          </p>
          <div className="text-sm text-gray-500">
            Environment: {ENV_CONFIG.DEVELOPMENT_MODE ? 'Development' : 'Production'}
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthorized) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-lg">
          <div className="text-center mb-6">
            <div className="text-4xl mb-2">🔒</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Developer Access Required
            </h1>
            <p className="text-gray-600 text-sm">
              This is a protected development interface for internal use only.
            </p>
          </div>

          <form onSubmit={handleDevAuth} className="space-y-4">
            <div>
              <label
                htmlFor="devPassword"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Development Access Code
              </label>
              <input
                type="password"
                id="devPassword"
                value={devPassword}
                onChange={(e) => {
                  console.log("Escribiendo:", e.target.value); // 👈 debug
                  setDevPassword(e.target.value);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="Enter access code..."
                required
              />
            </div>

            {error && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-colors"
            >
              Access Development Interface
            </button>
          </form>

          <div className="mt-6 text-center">
            <div className="text-xs text-gray-500 space-y-1">
              <div>🧪 Testing Service Interface</div>
              <div>🔧 Internal Development Only</div>
              <div>📊 Visual Program Builder</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Development Header */}
      <div className="bg-yellow-400 border-b border-yellow-500 px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-yellow-800 font-medium text-sm">
              🧪 DEVELOPMENT MODE
            </span>
            <span className="text-yellow-700 text-xs">
              Internal Testing Interface
            </span>
          </div>

          <button
            onClick={handleLogout}
            className="text-yellow-800 hover:text-yellow-900 text-sm font-medium"
          >
            Exit Dev Mode
          </button>
        </div>
      </div>

      {/* Main Content */}
      {children}
    </div>
  );
};

export default DevAuthWrapper;
