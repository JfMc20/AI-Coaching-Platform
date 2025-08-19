/**
 * Program Validation Hook
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

import { useMemo } from 'react';
import { useCanvasStore } from '@/stores/canvasStore';
import { StepType } from '@/types';

interface ValidationIssue {
  id: string;
  type: 'error' | 'warning' | 'info';
  message: string;
  nodeId?: string;
  edgeId?: string;
}

interface ValidationResult {
  isValid: boolean;
  issues: ValidationIssue[];
  stats: {
    totalNodes: number;
    totalEdges: number;
    triggerNodes: number;
    orphanedNodes: number;
    deadEndNodes: number;
  };
}

export const useProgramValidation = (): ValidationResult => {
  const { nodes, edges } = useCanvasStore();

  return useMemo(() => {
    const issues: ValidationIssue[] = [];
    
    // Calculate stats
    const totalNodes = nodes.length;
    const totalEdges = edges.length;
    const triggerNodes = nodes.filter(node => 
      node.data.step.step_type === StepType.TRIGGER
    ).length;

    // Find orphaned nodes (no incoming or outgoing connections)
    const orphanedNodes = nodes.filter(node => {
      const hasIncoming = edges.some(edge => edge.target === node.id);
      const hasOutgoing = edges.some(edge => edge.source === node.id);
      return !hasIncoming && !hasOutgoing && totalNodes > 1;
    });

    // Find dead end nodes (no outgoing connections, except for intentional end steps)
    const deadEndNodes = nodes.filter(node => {
      const hasOutgoing = edges.some(edge => edge.source === node.id);
      return !hasOutgoing && 
             node.data.step.step_type !== StepType.WAIT &&
             totalNodes > 1;
    });

    // Validation Rules

    // 1. Must have at least one trigger node
    if (triggerNodes === 0 && totalNodes > 0) {
      issues.push({
        id: 'no-trigger',
        type: 'error',
        message: 'Program must have at least one trigger step to start execution',
      });
    }

    // 2. Too many trigger nodes might be confusing
    if (triggerNodes > 3) {
      issues.push({
        id: 'too-many-triggers',
        type: 'warning',
        message: `${triggerNodes} trigger steps found. Consider simplifying the program flow`,
      });
    }

    // 3. Check for orphaned nodes
    orphanedNodes.forEach(node => {
      issues.push({
        id: `orphaned-${node.id}`,
        type: 'warning',
        message: `Step "${node.data.step.step_name}" is not connected to any other steps`,
        nodeId: node.id,
      });
    });

    // 4. Check for dead end nodes (except wait steps)
    deadEndNodes.forEach(node => {
      if (node.data.step.step_type !== StepType.WAIT) {
        issues.push({
          id: `dead-end-${node.id}`,
          type: 'info',
          message: `Step "${node.data.step.step_name}" has no outgoing connections`,
          nodeId: node.id,
        });
      }
    });

    // 5. Check for empty step names
    nodes.forEach(node => {
      if (!node.data.step.step_name.trim()) {
        issues.push({
          id: `empty-name-${node.id}`,
          type: 'warning',
          message: 'Step has no name',
          nodeId: node.id,
        });
      }
    });

    // 6. Check for message steps without templates
    nodes.forEach(node => {
      const step = node.data.step;
      if (step.step_type === StepType.MESSAGE && 
          (!step.action_config.message_template || !step.action_config.message_template.trim())) {
        issues.push({
          id: `empty-message-${node.id}`,
          type: 'error',
          message: `Message step "${step.step_name}" has no message template`,
          nodeId: node.id,
        });
      }
    });

    // 7. Check for task steps without descriptions
    nodes.forEach(node => {
      const step = node.data.step;
      if (step.step_type === StepType.TASK && 
          (!step.action_config.task_description || !step.action_config.task_description.trim())) {
        issues.push({
          id: `empty-task-${node.id}`,
          type: 'error',
          message: `Task step "${step.step_name}" has no task description`,
          nodeId: node.id,
        });
      }
    });

    // 8. Check for condition steps without expressions
    nodes.forEach(node => {
      const step = node.data.step;
      if (step.step_type === StepType.CONDITION && 
          step.trigger_config.trigger_type === 'CONDITION_BASED' &&
          (!step.trigger_config.condition_expression || !step.trigger_config.condition_expression.trim())) {
        issues.push({
          id: `empty-condition-${node.id}`,
          type: 'error',
          message: `Condition step "${step.step_name}" has no condition expression`,
          nodeId: node.id,
        });
      }
    });

    // 9. Performance warning for too many nodes
    if (totalNodes > 20) {
      issues.push({
        id: 'too-many-nodes',
        type: 'warning',
        message: `Program has ${totalNodes} steps. Consider breaking it into smaller programs for better performance`,
      });
    }

    // 10. Info about AI integration usage
    const aiIntegratedNodes = nodes.filter(node => 
      node.data.step.action_config.use_knowledge_context || 
      node.data.step.action_config.use_personality
    );

    if (aiIntegratedNodes.length === 0 && totalNodes > 0) {
      issues.push({
        id: 'no-ai-integration',
        type: 'info',
        message: 'Consider enabling AI integration (Knowledge Context or Personality) for a more personalized experience',
      });
    }

    // Determine overall validity
    const hasErrors = issues.some(issue => issue.type === 'error');
    const isValid = !hasErrors && totalNodes > 0;

    return {
      isValid,
      issues,
      stats: {
        totalNodes,
        totalEdges,
        triggerNodes,
        orphanedNodes: orphanedNodes.length,
        deadEndNodes: deadEndNodes.length,
      },
    };
  }, [nodes, edges]);
};

export default useProgramValidation;