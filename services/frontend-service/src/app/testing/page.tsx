/**
 * Testing Service Main Page
 * Frontend Service - Multi-Channel AI Coaching Platform
 * 
 * Protected development interface for internal testing
 */

'use client';

import React from 'react';
import DevAuthWrapper from '@/components/auth/DevAuthWrapper';
import ProgramCanvas from '@/components/canvas/ProgramCanvas';

const TestingPage: React.FC = () => {
  return (
    <DevAuthWrapper>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Visual Program Builder
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Testing Interface - Multi-Channel AI Coaching Platform
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                Service: Frontend (Port 8006)
              </div>
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span className="text-sm text-green-600 font-medium">
                Connected
              </span>
            </div>
          </div>
        </div>

        {/* Canvas Area */}
        <div className="flex-1">
          <ProgramCanvas />
        </div>

        {/* Footer */}
        <div className="bg-gray-50 border-t border-gray-200 px-6 py-2">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div>
              React Flow Canvas • Drag & Drop • Visual Programming
            </div>
            <div>
              Frontend Service v1.0.0 • Multi-Channel AI Coaching Platform
            </div>
          </div>
        </div>
      </div>
    </DevAuthWrapper>
  );
};

export default TestingPage;