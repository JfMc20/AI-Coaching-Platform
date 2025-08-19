/**
 * Program Canvas Component - React Flow Implementation
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

'use client';

import React, { useCallback, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  ReactFlowProvider,
  ReactFlowInstance,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useCanvasStore } from '@/stores/canvasStore';
import { useCanvasAPI } from '@/hooks/useCanvasAPI';
import { StepType } from '@/types';
import ProgramStepNode from './nodes/ProgramStepNode';
import CanvasToolbar from './CanvasToolbar';
import NodeSidebar from './NodeSidebar';

// Custom node types
const nodeTypes = {
  programStep: ProgramStepNode,
};

interface ProgramCanvasProps {
  className?: string;
}

const ProgramCanvas: React.FC<ProgramCanvasProps> = ({ className = '' }) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = React.useState<ReactFlowInstance | null>(null);

  // Canvas Store
  const {
    nodes,
    edges,
    selectedNode,
    addNode,
    addEdge: addCanvasEdge,
    selectNode,
    setError,
    currentProgramId,
  } = useCanvasStore();

  // Canvas API Integration
  const {
    isLoading: apiLoading,
    error: apiError,
    hasUnsavedChanges,
  } = useCanvasAPI({
    programId: currentProgramId,
    autoSave: true,
    autoSaveInterval: 30000, // 30 seconds
  });

  // React Flow state (synced with Zustand store)
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState(nodes);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState(edges);

  // Sync React Flow state with Zustand store
  React.useEffect(() => {
    setRfNodes(nodes);
  }, [nodes, setRfNodes]);

  React.useEffect(() => {
    setRfEdges(edges);
  }, [edges, setRfEdges]);

  // Handle connection between nodes
  const onConnect = useCallback(
    (connection: Connection) => {
      if (connection.source && connection.target) {
        addCanvasEdge(connection);
        setRfEdges((eds) => addEdge(connection, eds));
      }
    },
    [addCanvasEdge, setRfEdges]
  );

  // Handle node selection
  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      selectNode(node.id);
    },
    [selectNode]
  );

  // Handle canvas click (deselect nodes)
  const onPaneClick = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

  // Handle drag over for node dropping
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle node drop from toolbar
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const stepType = event.dataTransfer.getData('application/reactflow') as StepType;
      
      if (!stepType || !reactFlowWrapper.current || !reactFlowInstance) {
        return;
      }

      const bounds = reactFlowWrapper.current.getBoundingClientRect();
      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX - bounds.left,
        y: event.clientY - bounds.top,
      });

      try {
        addNode(stepType, position);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to add node');
      }
    },
    [reactFlowInstance, addNode, setError]
  );

  // Handle keyboard shortcuts
  const onKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === 'Delete' && selectedNode) {
        // Delete selected node
        const deleteNode = useCanvasStore.getState().deleteNode;
        deleteNode(selectedNode);
      }
    },
    [selectedNode]
  );

  React.useEffect(() => {
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [onKeyDown]);

  return (
    <div className={`flex h-full ${className}`}>
      {/* Canvas Toolbar */}
      <CanvasToolbar />

      {/* Main Canvas Area */}
      <div className="flex-1 relative">
        {/* API Status Indicators */}
        {apiLoading && (
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg">
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span className="text-sm">Syncing with backend...</span>
            </div>
          </div>
        )}

        {apiError && (
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10 bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg">
            <div className="flex items-center space-x-2">
              <span className="text-sm">❌ {apiError}</span>
            </div>
          </div>
        )}

        {hasUnsavedChanges && !apiLoading && (
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10 bg-yellow-600 text-white px-4 py-2 rounded-lg shadow-lg">
            <div className="flex items-center space-x-2">
              <span className="text-sm">💾 Unsaved changes</span>
            </div>
          </div>
        )}
        <div 
          ref={reactFlowWrapper} 
          className="h-full w-full"
          onDrop={onDrop}
          onDragOver={onDragOver}
        >
          <ReactFlow
            nodes={rfNodes}
            edges={rfEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            onInit={setReactFlowInstance}
            nodeTypes={nodeTypes}
            fitView
            attributionPosition="bottom-left"
            className="bg-gray-50"
            defaultEdgeOptions={{
              animated: true,
              type: 'smoothstep',
            }}
          >
            <Background 
              color="#aaa" 
              gap={16}
              size={1}
              variant="dots" 
            />
            <Controls 
              position="top-left"
              showZoom={true}
              showFitView={true}
              showInteractive={true}
            />
            <MiniMap 
              position="bottom-right"
              nodeColor={(node) => {
                switch (node.data?.stepType) {
                  case StepType.MESSAGE:
                    return '#3B82F6'; // Blue
                  case StepType.TASK:
                    return '#10B981'; // Green
                  case StepType.SURVEY:
                    return '#F59E0B'; // Yellow
                  case StepType.WAIT:
                    return '#6B7280'; // Gray
                  case StepType.CONDITION:
                    return '#8B5CF6'; // Purple
                  case StepType.TRIGGER:
                    return '#EF4444'; // Red
                  default:
                    return '#6B7280';
                }
              }}
              maskColor="rgba(0, 0, 0, 0.1)"
            />
          </ReactFlow>
        </div>
      </div>

      {/* Node Configuration Sidebar */}
      <NodeSidebar />
    </div>
  );
};

// Main component wrapper with ReactFlowProvider
const ProgramCanvasWrapper: React.FC<ProgramCanvasProps> = (props) => {
  return (
    <ReactFlowProvider>
      <ProgramCanvas {...props} />
    </ReactFlowProvider>
  );
};

export default ProgramCanvasWrapper;