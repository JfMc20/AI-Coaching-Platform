/**
 * Edge Information Panel Component
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

'use client';

import React from 'react';
import { useCanvasStore } from '@/stores/canvasStore';

const EdgeInfoPanel: React.FC = () => {
  const { edges, nodes, selectedNode } = useCanvasStore();

  // Find connections for the selected node
  const nodeConnections = edges.filter(
    edge => edge.source === selectedNode || edge.target === selectedNode
  );

  if (!selectedNode || nodeConnections.length === 0) {
    return null;
  }

  const selectedNodeData = nodes.find(node => node.id === selectedNode);
  if (!selectedNodeData) return null;

  return (
    <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
      <h4 className="text-sm font-medium text-gray-900 mb-3">
        Step Connections
      </h4>
      
      <div className="space-y-3">
        {/* Incoming connections */}
        {nodeConnections
          .filter(edge => edge.target === selectedNode)
          .map(edge => {
            const sourceNode = nodes.find(node => node.id === edge.source);
            return (
              <div key={edge.id} className="flex items-center space-x-2 text-xs">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-gray-600">From:</span>
                <span className="font-medium text-gray-900">
                  {sourceNode?.data.step.step_name || 'Unknown Step'}
                </span>
              </div>
            );
          })}

        {/* Outgoing connections */}
        {nodeConnections
          .filter(edge => edge.source === selectedNode)
          .map(edge => {
            const targetNode = nodes.find(node => node.id === edge.target);
            return (
              <div key={edge.id} className="flex items-center space-x-2 text-xs">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                <span className="text-gray-600">To:</span>
                <span className="font-medium text-gray-900">
                  {targetNode?.data.step.step_name || 'Unknown Step'}
                </span>
              </div>
            );
          })}
      </div>

      {nodeConnections.length === 0 && (
        <div className="text-xs text-gray-500 text-center py-2">
          No connections for this step
        </div>
      )}
    </div>
  );
};

export default EdgeInfoPanel;