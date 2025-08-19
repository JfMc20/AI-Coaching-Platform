/**
 * Canvas Store - Zustand State Management
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

import { create } from 'zustand';
import { Node, Edge, Connection } from '@xyflow/react';
import { NodeData, ProgramStep, StepType } from '@/types';

interface CanvasState {
  // Canvas Data
  nodes: Node<NodeData>[];
  edges: Edge[];
  
  // UI State
  selectedNode: string | null;
  isLoading: boolean;
  error: string | null;
  isDirty: boolean; // Has unsaved changes
  
  // Program State
  currentProgramId: string | null;
  programTitle: string;
  
  // Node Management
  addNode: (stepType: StepType, position: { x: number; y: number }) => void;
  updateNode: (id: string, updates: Partial<NodeData>) => void;
  deleteNode: (id: string) => void;
  duplicateNode: (id: string) => void;
  
  // Edge Management
  addEdge: (connection: Connection) => void;
  deleteEdge: (id: string) => void;
  updateEdgeData: (id: string, data: any) => void;
  
  // Selection
  selectNode: (id: string | null) => void;
  
  // Program Management
  loadProgram: (programId: string, steps: ProgramStep[]) => void;
  saveProgram: () => Promise<void>;
  clearCanvas: () => void;
  setProgramTitle: (title: string) => void;
  
  // UI State Management
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setDirty: (dirty: boolean) => void;
  
  // Canvas Operations
  resetView: () => void;
  autoLayout: () => void;
}

let nodeId = 0;
const generateNodeId = () => `node_${++nodeId}`;

let edgeId = 0;
const generateEdgeId = () => `edge_${++edgeId}`;

export const useCanvasStore = create<CanvasState>((set, get) => ({
  // Initial State
  nodes: [],
  edges: [],
  selectedNode: null,
  isLoading: false,
  error: null,
  isDirty: false,
  currentProgramId: null,
  programTitle: 'Untitled Program',

  // Node Management
  addNode: (stepType: StepType, position: { x: number; y: number }) => {
    const newNodeId = generateNodeId();
    const newStep: ProgramStep = {
      id: newNodeId,
      step_id: newNodeId,
      program_id: get().currentProgramId || '',
      step_type: stepType,
      step_name: `${stepType} Step`,
      position,
      trigger_config: {
        trigger_type: stepType === StepType.TRIGGER ? 'IMMEDIATE' as any : 'USER_ACTION' as any,
      },
      action_config: {
        action_type: stepType === StepType.MESSAGE ? 'SEND_MESSAGE' as any : 'WAIT' as any,
        use_knowledge_context: false,
        use_personality: false,
      },
    };

    const newNode: Node<NodeData> = {
      id: newNodeId,
      type: 'programStep',
      position,
      data: {
        step: newStep,
        label: newStep.step_name,
        stepType,
        isEditing: false,
      },
    };

    set(state => ({
      nodes: [...state.nodes, newNode],
      isDirty: true,
    }));
  },

  updateNode: (id: string, updates: Partial<NodeData>) => {
    set(state => ({
      nodes: state.nodes.map(node =>
        node.id === id
          ? { ...node, data: { ...node.data, ...updates } }
          : node
      ),
      isDirty: true,
    }));
  },

  deleteNode: (id: string) => {
    set(state => ({
      nodes: state.nodes.filter(node => node.id !== id),
      edges: state.edges.filter(edge => edge.source !== id && edge.target !== id),
      selectedNode: state.selectedNode === id ? null : state.selectedNode,
      isDirty: true,
    }));
  },

  duplicateNode: (id: string) => {
    const state = get();
    const existingNode = state.nodes.find(node => node.id === id);
    if (!existingNode) return;

    const newNodeId = generateNodeId();
    const newNode: Node<NodeData> = {
      ...existingNode,
      id: newNodeId,
      position: {
        x: existingNode.position.x + 20,
        y: existingNode.position.y + 20,
      },
      data: {
        ...existingNode.data,
        step: {
          ...existingNode.data.step,
          id: newNodeId,
          step_id: newNodeId,
          step_name: `${existingNode.data.step.step_name} (Copy)`,
        },
      },
    };

    set(state => ({
      nodes: [...state.nodes, newNode],
      isDirty: true,
    }));
  },

  // Edge Management
  addEdge: (connection: Connection) => {
    if (!connection.source || !connection.target) return;

    const newEdgeId = generateEdgeId();
    const newEdge: Edge = {
      id: newEdgeId,
      source: connection.source,
      target: connection.target,
      sourceHandle: connection.sourceHandle,
      targetHandle: connection.targetHandle,
      type: 'default',
      animated: true,
    };

    set(state => ({
      edges: [...state.edges, newEdge],
      isDirty: true,
    }));
  },

  deleteEdge: (id: string) => {
    set(state => ({
      edges: state.edges.filter(edge => edge.id !== id),
      isDirty: true,
    }));
  },

  updateEdgeData: (id: string, data: any) => {
    set(state => ({
      edges: state.edges.map(edge =>
        edge.id === id ? { ...edge, data } : edge
      ),
      isDirty: true,
    }));
  },

  // Selection
  selectNode: (id: string | null) => {
    set({ selectedNode: id });
  },

  // Program Management
  loadProgram: (programId: string, steps: ProgramStep[]) => {
    const nodes: Node<NodeData>[] = steps.map(step => ({
      id: step.step_id,
      type: 'programStep',
      position: step.position,
      data: {
        step,
        label: step.step_name,
        stepType: step.step_type,
        isEditing: false,
      },
    }));

    set({
      currentProgramId: programId,
      nodes,
      edges: [], // TODO: Load edges from program connections
      selectedNode: null,
      isDirty: false,
      error: null,
    });
  },

  saveProgram: async () => {
    const state = get();
    if (!state.currentProgramId) return;

    set({ isLoading: true, error: null });

    try {
      // TODO: Implement API call to save program
      const steps = state.nodes.map(node => ({
        ...node.data.step,
        position: node.position,
      }));

      console.log('Saving program:', { programId: state.currentProgramId, steps });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      set({ isDirty: false, isLoading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to save program',
        isLoading: false,
      });
    }
  },

  clearCanvas: () => {
    set({
      nodes: [],
      edges: [],
      selectedNode: null,
      currentProgramId: null,
      programTitle: 'Untitled Program',
      isDirty: false,
      error: null,
    });
  },

  setProgramTitle: (title: string) => {
    set({ programTitle: title, isDirty: true });
  },

  // UI State Management
  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  setDirty: (dirty: boolean) => {
    set({ isDirty: dirty });
  },

  // Canvas Operations
  resetView: () => {
    // TODO: Implement reset view functionality
    console.log('Reset view');
  },

  autoLayout: () => {
    // TODO: Implement auto layout algorithm
    console.log('Auto layout');
  },
}));