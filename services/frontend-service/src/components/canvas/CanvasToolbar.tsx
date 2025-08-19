/**
 * Canvas Toolbar Component - Node Palette & Actions
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

'use client';

import React from 'react';
import { StepType } from '@/types';
import { useCanvasStore } from '@/stores/canvasStore';
import ValidationPanel from './ValidationPanel';

interface DraggableNodeProps {
  stepType: StepType;
  icon: string;
  label: string;
  description: string;
  color: string;
}

const DraggableNode: React.FC<DraggableNodeProps> = ({ 
  stepType, 
  icon, 
  label, 
  description, 
  color 
}) => {
  const onDragStart = (event: React.DragEvent, nodeType: StepType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      className={`
        p-3 rounded-lg border-2 cursor-grab active:cursor-grabbing
        hover:shadow-md transition-all duration-200 bg-white
        ${color}
      `}
      draggable
      onDragStart={(event) => onDragStart(event, stepType)}
      title={description}
    >
      <div className="flex flex-col items-center space-y-1">
        <span className="text-2xl">{icon}</span>
        <span className="text-xs font-medium text-center">{label}</span>
      </div>
    </div>
  );
};

const CanvasToolbar: React.FC = () => {
  const { 
    clearCanvas, 
    saveProgram, 
    autoLayout, 
    resetView, 
    isLoading, 
    isDirty,
    programTitle,
    setProgramTitle 
  } = useCanvasStore();

  const nodeTypes = [
    {
      stepType: StepType.MESSAGE,
      icon: '💬',
      label: 'Message',
      description: 'Send a message to the user',
      color: 'border-blue-300 hover:border-blue-400 hover:bg-blue-50',
    },
    {
      stepType: StepType.TASK,
      icon: '✅',
      label: 'Task',
      description: 'Assign a task to the user',
      color: 'border-green-300 hover:border-green-400 hover:bg-green-50',
    },
    {
      stepType: StepType.SURVEY,
      icon: '📋',
      label: 'Survey',
      description: 'Collect feedback from the user',
      color: 'border-yellow-300 hover:border-yellow-400 hover:bg-yellow-50',
    },
    {
      stepType: StepType.WAIT,
      icon: '⏱️',
      label: 'Wait',
      description: 'Pause program execution',
      color: 'border-gray-300 hover:border-gray-400 hover:bg-gray-50',
    },
    {
      stepType: StepType.CONDITION,
      icon: '🔀',
      label: 'Condition',
      description: 'Create conditional logic branches',
      color: 'border-purple-300 hover:border-purple-400 hover:bg-purple-50',
    },
    {
      stepType: StepType.TRIGGER,
      icon: '⚡',
      label: 'Trigger',
      description: 'Start point for the program',
      color: 'border-red-300 hover:border-red-400 hover:bg-red-50',
    },
  ];

  const handleSave = async () => {
    try {
      await saveProgram();
    } catch (error) {
      console.error('Failed to save program:', error);
    }
  };

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Program Builder
        </h2>
        
        {/* Program Title */}
        <input
          type="text"
          value={programTitle}
          onChange={(e) => setProgramTitle(e.target.value)}
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
          placeholder="Program title..."
        />
      </div>

      {/* Node Palette */}
      <div className="flex-1 p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">
          Drag & Drop Steps
        </h3>
        
        <div className="grid grid-cols-2 gap-2">
          {nodeTypes.map((nodeType) => (
            <DraggableNode
              key={nodeType.stepType}
              stepType={nodeType.stepType}
              icon={nodeType.icon}
              label={nodeType.label}
              description={nodeType.description}
              color={nodeType.color}
            />
          ))}
        </div>

        {/* Instructions */}
        <div className="mt-6 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="text-sm font-medium text-blue-900 mb-1">
            How to use:
          </h4>
          <ul className="text-xs text-blue-700 space-y-1">
            <li>• Drag steps to canvas</li>
            <li>• Connect with handles</li>
            <li>• Double-click to edit</li>
            <li>• Select & press Delete</li>
          </ul>
        </div>

        {/* Validation Panel */}
        <div className="mt-4">
          <ValidationPanel />
        </div>
      </div>

      {/* Actions */}
      <div className="p-4 border-t border-gray-200 space-y-2">
        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={isLoading || !isDirty}
          className={`
            w-full px-4 py-2 rounded-md text-sm font-medium transition-colors
            ${isDirty 
              ? 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-400' 
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }
          `}
        >
          {isLoading ? 'Saving...' : isDirty ? 'Save Program' : 'Saved'}
        </button>

        {/* Canvas Actions */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={autoLayout}
            className="px-3 py-2 text-xs font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Auto Layout
          </button>
          
          <button
            onClick={resetView}
            className="px-3 py-2 text-xs font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Reset View
          </button>
        </div>

        {/* Clear Canvas */}
        <button
          onClick={clearCanvas}
          className="w-full px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-md hover:bg-red-100 transition-colors"
        >
          Clear Canvas
        </button>
      </div>
    </div>
  );
};

export default CanvasToolbar;