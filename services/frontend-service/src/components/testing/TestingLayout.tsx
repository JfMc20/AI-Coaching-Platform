/**
 * Complete Testing Layout - All Creator Flow Features
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

'use client';

import React, { useState } from 'react';

interface Tab {
  id: string;
  name: string;
  icon: string;
  description: string;
}

const tabs: Tab[] = [
  {
    id: 'onboarding',
    name: 'Creator Onboarding',
    icon: '🚀',
    description: 'Complete creator registration and setup flow'
  },
  {
    id: 'knowledge',
    name: 'Knowledge Management',
    icon: '📚',
    description: 'Upload documents and build knowledge base'
  },
  {
    id: 'personality',
    name: 'Personality Analysis',
    icon: '🎭',
    description: 'Analyze and customize creator personality'
  },
  {
    id: 'programs',
    name: 'Program Builder',
    icon: '🔧',
    description: 'Create coaching programs with visual builder'
  },
  {
    id: 'chat',
    name: 'AI Chat Testing',
    icon: '💬',
    description: 'Test AI conversations and responses'
  },
  {
    id: 'execution',
    name: 'Program Testing',
    icon: '⚡',
    description: 'Execute and test complete programs'
  },
  {
    id: 'analytics',
    name: 'Analytics & Debug',
    icon: '📊',
    description: 'Performance analytics and debugging tools'
  }
];

interface TestingLayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

const TestingLayout: React.FC<TestingLayoutProps> = ({ 
  children, 
  activeTab, 
  onTabChange 
}) => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  const activeTabData = tabs.find(tab => tab.id === activeTab);

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Sidebar with tabs */}
      <div className={`bg-white border-r border-gray-200 transition-all duration-300 ${
        isSidebarCollapsed ? 'w-16' : 'w-80'
      }`}>
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {!isSidebarCollapsed && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  Creator Testing Suite
                </h2>
                <p className="text-sm text-gray-600">
                  Complete AI Coaching Platform Testing
                </p>
              </div>
            )}
            <button
              onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              className="p-2 rounded-md hover:bg-gray-100 transition-colors"
            >
              {isSidebarCollapsed ? '→' : '←'}
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-2 space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`
                  w-full text-left p-3 rounded-lg transition-all duration-200
                  ${activeTab === tab.id 
                    ? 'bg-blue-100 text-blue-900 border border-blue-200' 
                    : 'text-gray-700 hover:bg-gray-100'
                  }
                `}
              >
                <div className="flex items-start space-x-3">
                  <span className="text-xl">{tab.icon}</span>
                  {!isSidebarCollapsed && (
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium">{tab.name}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {tab.description}
                      </div>
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-gray-200">
          {!isSidebarCollapsed && (
            <div className="text-xs text-gray-500 space-y-1">
              <div>🧪 Testing Environment</div>
              <div>🔒 Development Only</div>
              <div>⚡ All Features Enabled</div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Content Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
                <span>{activeTabData?.icon}</span>
                <span>{activeTabData?.name}</span>
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                {activeTabData?.description}
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                Service: Frontend (8006)
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-sm text-green-600 font-medium">
                  Active
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
      </div>
    </div>
  );
};

export default TestingLayout;