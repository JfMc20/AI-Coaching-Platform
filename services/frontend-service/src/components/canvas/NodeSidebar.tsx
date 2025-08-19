/**
 * Node Configuration Sidebar Component
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

'use client';

import React from 'react';
import { useCanvasStore } from '@/stores/canvasStore';
import { StepType, TriggerType, ActionType } from '@/types';
import EdgeInfoPanel from './EdgeInfoPanel';

const NodeSidebar: React.FC = () => {
  const { nodes, selectedNode, updateNode } = useCanvasStore();

  // Find the selected node
  const selectedNodeData = selectedNode 
    ? nodes.find(node => node.id === selectedNode)?.data 
    : null;

  if (!selectedNode || !selectedNodeData) {
    return (
      <div className="w-80 bg-white border-l border-gray-200 p-4">
        <div className="text-center text-gray-500 mt-8">
          <div className="text-4xl mb-2">👆</div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">
            Select a Step
          </h3>
          <p className="text-sm text-gray-600">
            Click on a step in the canvas to configure its settings
          </p>
        </div>
      </div>
    );
  }

  const { step, stepType } = selectedNodeData;

  const updateStepField = (field: string, value: any) => {
    const newStep = { ...step };
    
    // Handle nested field updates
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      newStep[parent as keyof typeof step] = {
        ...newStep[parent as keyof typeof step],
        [child]: value,
      };
    } else {
      (newStep as any)[field] = value;
    }

    updateNode(selectedNode, {
      step: newStep,
      label: newStep.step_name,
    });
  };

  return (
    <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">
          Step Configuration
        </h2>
        <p className="text-sm text-gray-600">
          {stepType} Step
        </p>
      </div>

      {/* Configuration Form */}
      <div className="flex-1 p-4 overflow-y-auto space-y-6">
        {/* Basic Information */}
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">
            Basic Information
          </h3>
          
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Step Name
              </label>
              <input
                type="text"
                value={step.step_name}
                onChange={(e) => updateStepField('step_name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm"
                placeholder="Enter step name..."
              />
            </div>
          </div>
        </div>

        {/* Trigger Configuration */}
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">
            Trigger Settings
          </h3>
          
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Trigger Type
              </label>
              <select
                value={step.trigger_config.trigger_type}
                onChange={(e) => updateStepField('trigger_config.trigger_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm"
              >
                <option value={TriggerType.IMMEDIATE}>Immediate</option>
                <option value={TriggerType.TIME_BASED}>Time Based</option>
                <option value={TriggerType.CONDITION_BASED}>Condition Based</option>
                <option value={TriggerType.USER_ACTION}>User Action</option>
                <option value={TriggerType.DELAYED}>Delayed</option>
              </select>
            </div>

            {step.trigger_config.trigger_type === TriggerType.TIME_BASED && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Schedule
                </label>
                <input
                  type="text"
                  value={step.trigger_config.schedule || ''}
                  onChange={(e) => updateStepField('trigger_config.schedule', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm"
                  placeholder="e.g., daily, weekly, 09:00"
                />
              </div>
            )}

            {step.trigger_config.trigger_type === TriggerType.CONDITION_BASED && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Condition Expression
                </label>
                <textarea
                  value={step.trigger_config.condition_expression || ''}
                  onChange={(e) => updateStepField('trigger_config.condition_expression', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm"
                  rows={3}
                  placeholder="e.g., user_engagement_score > 0.8"
                />
              </div>
            )}

            {step.trigger_config.trigger_type === TriggerType.DELAYED && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Delay (minutes)
                </label>
                <input
                  type="number"
                  value={step.trigger_config.delay_minutes || 0}
                  onChange={(e) => updateStepField('trigger_config.delay_minutes', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm"
                  min="0"
                />
              </div>
            )}
          </div>
        </div>

        {/* Action Configuration */}
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">
            Action Settings
          </h3>
          
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Action Type
              </label>
              <select
                value={step.action_config.action_type}
                onChange={(e) => updateStepField('action_config.action_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm"
              >
                <option value={ActionType.SEND_MESSAGE}>Send Message</option>
                <option value={ActionType.ASSIGN_TASK}>Assign Task</option>
                <option value={ActionType.SEND_SURVEY}>Send Survey</option>
                <option value={ActionType.WAIT}>Wait</option>
                <option value={ActionType.TRIGGER_WEBHOOK}>Trigger Webhook</option>
              </select>
            </div>

            {step.action_config.action_type === ActionType.SEND_MESSAGE && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Message Template
                </label>
                <textarea
                  value={step.action_config.message_template || ''}
                  onChange={(e) => updateStepField('action_config.message_template', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm"
                  rows={4}
                  placeholder="Enter your message template..."
                />
              </div>
            )}

            {step.action_config.action_type === ActionType.ASSIGN_TASK && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Task Description
                </label>
                <textarea
                  value={step.action_config.task_description || ''}
                  onChange={(e) => updateStepField('action_config.task_description', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm"
                  rows={3}
                  placeholder="Describe the task..."
                />
              </div>
            )}

            {step.action_config.action_type === ActionType.WAIT && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Wait Duration (minutes)
                </label>
                <input
                  type="number"
                  value={step.action_config.wait_duration_minutes || 0}
                  onChange={(e) => updateStepField('action_config.wait_duration_minutes', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm"
                  min="0"
                />
              </div>
            )}
          </div>
        </div>

        {/* AI Integration Settings */}
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">
            AI Integration
          </h3>
          
          <div className="space-y-3">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="use_knowledge"
                checked={step.action_config.use_knowledge_context || false}
                onChange={(e) => updateStepField('action_config.use_knowledge_context', e.target.checked)}
                className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-400"
              />
              <label htmlFor="use_knowledge" className="text-sm text-gray-700">
                Use Knowledge Context
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="use_personality"
                checked={step.action_config.use_personality || false}
                onChange={(e) => updateStepField('action_config.use_personality', e.target.checked)}
                className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-400"
              />
              <label htmlFor="use_personality" className="text-sm text-gray-700">
                Use Personality Enhancement
              </label>
            </div>

            {step.action_config.use_knowledge_context && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Context Query
                </label>
                <input
                  type="text"
                  value={step.action_config.context_query || ''}
                  onChange={(e) => updateStepField('action_config.context_query', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm"
                  placeholder="e.g., motivation techniques"
                />
              </div>
            )}
          </div>
        </div>

        {/* Edge Information Panel */}
        <EdgeInfoPanel />
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          Step ID: {step.step_id}
        </div>
      </div>
    </div>
  );
};

export default NodeSidebar;