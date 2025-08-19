/**
 * Program Step Node Component - Custom React Flow Node
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { NodeData, StepType } from '@/types';
import { useCanvasStore } from '@/stores/canvasStore';

// Icons for different step types
const StepIcons = {
  [StepType.MESSAGE]: '💬',
  [StepType.TASK]: '✅',
  [StepType.SURVEY]: '📋',
  [StepType.WAIT]: '⏱️',
  [StepType.CONDITION]: '🔀',
  [StepType.TRIGGER]: '⚡',
};

// Colors for different step types
const StepColors = {
  [StepType.MESSAGE]: 'bg-blue-100 border-blue-300 text-blue-800',
  [StepType.TASK]: 'bg-green-100 border-green-300 text-green-800',
  [StepType.SURVEY]: 'bg-yellow-100 border-yellow-300 text-yellow-800',
  [StepType.WAIT]: 'bg-gray-100 border-gray-300 text-gray-800',
  [StepType.CONDITION]: 'bg-purple-100 border-purple-300 text-purple-800',
  [StepType.TRIGGER]: 'bg-red-100 border-red-300 text-red-800',
};

interface ProgramStepNodeProps extends NodeProps<NodeData> {}

const ProgramStepNode: React.FC<ProgramStepNodeProps> = ({ 
  id, 
  data, 
  selected 
}) => {
  const { selectNode, updateNode, deleteNode } = useCanvasStore();
  const { step, stepType, isEditing } = data;

  const handleNodeClick = (event: React.MouseEvent) => {
    event.stopPropagation();
    selectNode(id);
  };

  const handleDoubleClick = (event: React.MouseEvent) => {
    event.stopPropagation();
    updateNode(id, { isEditing: true });
  };

  const handleDelete = (event: React.MouseEvent) => {
    event.stopPropagation();
    deleteNode(id);
  };

  const handleTitleChange = (newTitle: string) => {
    updateNode(id, {
      step: { ...step, step_name: newTitle },
      label: newTitle,
    });
  };

  const finishEditing = () => {
    updateNode(id, { isEditing: false });
  };

  const stepColorClass = StepColors[stepType] || StepColors[StepType.MESSAGE];
  const stepIcon = StepIcons[stepType] || StepIcons[StepType.MESSAGE];

  return (
    <div
      className={`
        relative min-w-[200px] max-w-[300px] p-4 rounded-lg border-2 shadow-lg 
        cursor-pointer transition-all duration-200 bg-white
        ${stepColorClass}
        ${selected ? 'ring-2 ring-blue-400 shadow-xl' : 'hover:shadow-xl'}
      `}
      onClick={handleNodeClick}
      onDoubleClick={handleDoubleClick}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-gray-400 border-2 border-white"
      />

      {/* Node Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{stepIcon}</span>
          <span className="text-xs font-semibold uppercase tracking-wide">
            {stepType}
          </span>
        </div>
        
        {/* Delete Button */}
        {selected && (
          <button
            onClick={handleDelete}
            className="w-6 h-6 rounded-full bg-red-500 text-white text-xs hover:bg-red-600 transition-colors"
            title="Delete Step"
          >
            ×
          </button>
        )}
      </div>

      {/* Node Title */}
      <div className="mb-3">
        {isEditing ? (
          <input
            type="text"
            value={step.step_name}
            onChange={(e) => handleTitleChange(e.target.value)}
            onBlur={finishEditing}
            onKeyDown={(e) => {
              if (e.key === 'Enter') finishEditing();
              if (e.key === 'Escape') finishEditing();
            }}
            className="w-full px-2 py-1 text-sm font-medium bg-white border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
            autoFocus
          />
        ) : (
          <h3 className="text-sm font-medium text-gray-900 line-clamp-2">
            {step.step_name}
          </h3>
        )}
      </div>

      {/* Node Configuration Summary */}
      <div className="space-y-1 text-xs text-gray-600">
        {/* Trigger Info */}
        <div className="flex items-center space-x-1">
          <span className="font-medium">Trigger:</span>
          <span>{step.trigger_config.trigger_type}</span>
        </div>

        {/* Action Info */}
        <div className="flex items-center space-x-1">
          <span className="font-medium">Action:</span>
          <span>{step.action_config.action_type}</span>
        </div>

        {/* Integration Indicators */}
        <div className="flex items-center space-x-2 mt-2">
          {step.action_config.use_knowledge_context && (
            <span className="px-2 py-1 bg-blue-200 text-blue-800 rounded-full text-xs">
              📚 Knowledge
            </span>
          )}
          {step.action_config.use_personality && (
            <span className="px-2 py-1 bg-purple-200 text-purple-800 rounded-full text-xs">
              🎭 Personality
            </span>
          )}
        </div>
      </div>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-gray-400 border-2 border-white"
      />

      {/* Status Indicator */}
      {selected && (
        <div className="absolute -top-2 -right-2 w-4 h-4 bg-blue-500 rounded-full border-2 border-white"></div>
      )}
    </div>
  );
};

export default memo(ProgramStepNode);