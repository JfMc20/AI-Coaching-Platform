/**
 * React Flow Custom Nodes Export
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

export { default as ProgramStepNode } from './ProgramStepNode';

// Export node types for React Flow
export const nodeTypes = {
  programStep: ProgramStepNode,
};

export type CustomNodeTypes = typeof nodeTypes;