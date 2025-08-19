/**
 * Program Validation Panel Component
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

'use client';

import React, { useState } from 'react';
import { useCanvasStore } from '@/stores/canvasStore';
import { useProgramValidation } from '@/hooks/useProgramValidation';

const ValidationPanel: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { selectNode } = useCanvasStore();
  const { isValid, issues, stats } = useProgramValidation();

  const errorCount = issues.filter(issue => issue.type === 'error').length;
  const warningCount = issues.filter(issue => issue.type === 'warning').length;
  const infoCount = issues.filter(issue => issue.type === 'info').length;

  const getStatusColor = () => {
    if (errorCount > 0) return 'bg-red-500';
    if (warningCount > 0) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getStatusText = () => {
    if (errorCount > 0) return 'Issues Found';
    if (warningCount > 0) return 'Warnings';
    return 'Valid';
  };

  const handleIssueClick = (issue: any) => {
    if (issue.nodeId) {
      selectNode(issue.nodeId);
    }
  };

  if (stats.totalNodes === 0) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Header */}
      <div 
        className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${getStatusColor()}`}></div>
          <span className="text-sm font-medium text-gray-900">
            Program Validation
          </span>
          <span className="text-xs text-gray-500">
            {getStatusText()}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {/* Issue counts */}
          {errorCount > 0 && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-red-100 text-red-800">
              {errorCount} error{errorCount !== 1 ? 's' : ''}
            </span>
          )}
          {warningCount > 0 && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-yellow-100 text-yellow-800">
              {warningCount} warning{warningCount !== 1 ? 's' : ''}
            </span>
          )}
          
          {/* Expand/Collapse icon */}
          <div className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-200">
          {/* Stats */}
          <div className="p-3 bg-gray-50">
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-600">Steps:</span>
                <span className="font-medium">{stats.totalNodes}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Connections:</span>
                <span className="font-medium">{stats.totalEdges}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Triggers:</span>
                <span className="font-medium">{stats.triggerNodes}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Orphaned:</span>
                <span className={`font-medium ${stats.orphanedNodes > 0 ? 'text-yellow-600' : ''}`}>
                  {stats.orphanedNodes}
                </span>
              </div>
            </div>
          </div>

          {/* Issues List */}
          {issues.length > 0 ? (
            <div className="p-3 space-y-2 max-h-40 overflow-y-auto">
              {issues.map((issue) => (
                <div
                  key={issue.id}
                  className={`
                    p-2 rounded-md text-xs cursor-pointer transition-colors
                    ${issue.type === 'error' ? 'bg-red-50 hover:bg-red-100 text-red-800' : ''}
                    ${issue.type === 'warning' ? 'bg-yellow-50 hover:bg-yellow-100 text-yellow-800' : ''}
                    ${issue.type === 'info' ? 'bg-blue-50 hover:bg-blue-100 text-blue-800' : ''}
                    ${issue.nodeId ? 'hover:shadow-sm' : 'cursor-default'}
                  `}
                  onClick={() => handleIssueClick(issue)}
                >
                  <div className="flex items-start space-x-2">
                    <span className="flex-shrink-0 mt-0.5">
                      {issue.type === 'error' && '❌'}
                      {issue.type === 'warning' && '⚠️'}
                      {issue.type === 'info' && 'ℹ️'}
                    </span>
                    <span className="flex-1">{issue.message}</span>
                    {issue.nodeId && (
                      <span className="text-xs opacity-60">Click to select</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 text-center">
              <div className="text-green-600 text-sm">
                ✅ Program validation passed
              </div>
              <div className="text-xs text-gray-500 mt-1">
                No issues found
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ValidationPanel;