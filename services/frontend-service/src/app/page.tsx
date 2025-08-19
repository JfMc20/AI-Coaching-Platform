'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isProtectedDevMode } from '@/config/environment';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to testing interface if dev mode is enabled
    if (isProtectedDevMode()) {
      router.push('/testing');
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-lg text-center">
        <div className="text-6xl mb-4">🚀</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Frontend Service
        </h1>
        <p className="text-gray-600 mb-6">
          Multi-Channel AI Coaching Platform
        </p>

        <div className="space-y-4">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="text-sm font-medium text-blue-900 mb-2">
              Service Information
            </h3>
            <div className="text-xs text-blue-700 space-y-1">
              <div>Port: 8006</div>
              <div>Technology: Next.js + React Flow</div>
              <div>Purpose: Visual Program Builder</div>
            </div>
          </div>

          {isProtectedDevMode() ? (
            <button
              onClick={() => router.push('/testing')}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
            >
              Access Testing Interface
            </button>
          ) : (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-xs text-yellow-700">
                Development routes are disabled in production
              </p>
            </div>
          )}
        </div>

        <div className="mt-6 text-xs text-gray-500">
          Frontend Service v1.0.0
        </div>
      </div>
    </div>
  );
}
