/**
 * Programs Management Hook
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/apiClient';
import { Program, ProgramStep } from '@/types';

interface UseProgramsResult {
  programs: Program[];
  loading: boolean;
  error: string | null;
  
  // Actions
  createProgram: (programData: {
    title: string;
    description: string;
    enable_personality?: boolean;
    enable_analytics?: boolean;
  }) => Promise<Program>;
  
  updateProgram: (programId: string, updates: Partial<Program>) => Promise<Program>;
  deleteProgram: (programId: string) => Promise<void>;
  refreshPrograms: () => Promise<void>;
}

interface UseProgramResult {
  program: Program | null;
  steps: ProgramStep[];
  loading: boolean;
  error: string | null;
  
  // Actions
  updateProgram: (updates: Partial<Program>) => Promise<Program>;
  saveSteps: (steps: ProgramStep[]) => Promise<void>;
  executeProgram: (context?: { user_context?: string; debug_mode?: boolean }) => Promise<any>;
  getAnalytics: (timeRangeDays?: number) => Promise<any>;
}

// Hook for managing multiple programs
export const usePrograms = (): UseProgramsResult => {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshPrograms = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.creators.getPrograms(1, 50); // Get first 50 programs
      setPrograms(response.items || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch programs';
      setError(errorMessage);
      console.error('Error fetching programs:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createProgram = useCallback(async (programData: {
    title: string;
    description: string;
    enable_personality?: boolean;
    enable_analytics?: boolean;
  }): Promise<Program> => {
    setError(null);

    try {
      const newProgram = await apiClient.creators.createProgram(programData);
      setPrograms(prev => [newProgram, ...prev]);
      return newProgram;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create program';
      setError(errorMessage);
      throw err;
    }
  }, []);

  const updateProgram = useCallback(async (programId: string, updates: Partial<Program>): Promise<Program> => {
    setError(null);

    try {
      const updatedProgram = await apiClient.creators.updateProgram(programId, updates);
      setPrograms(prev => 
        prev.map(program => 
          program.id === programId ? { ...program, ...updatedProgram } : program
        )
      );
      return updatedProgram;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update program';
      setError(errorMessage);
      throw err;
    }
  }, []);

  const deleteProgram = useCallback(async (programId: string): Promise<void> => {
    setError(null);

    try {
      await apiClient.creators.deleteProgram(programId);
      setPrograms(prev => prev.filter(program => program.id !== programId));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete program';
      setError(errorMessage);
      throw err;
    }
  }, []);

  // Load programs on mount
  useEffect(() => {
    refreshPrograms();
  }, [refreshPrograms]);

  return {
    programs,
    loading,
    error,
    createProgram,
    updateProgram,
    deleteProgram,
    refreshPrograms,
  };
};

// Hook for managing a single program
export const useProgram = (programId: string | null): UseProgramResult => {
  const [program, setProgram] = useState<Program | null>(null);
  const [steps, setSteps] = useState<ProgramStep[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadProgram = useCallback(async () => {
    if (!programId) {
      setProgram(null);
      setSteps([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.creators.getProgram(programId);
      setProgram(response.program);
      setSteps(response.steps || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch program';
      setError(errorMessage);
      console.error('Error fetching program:', err);
    } finally {
      setLoading(false);
    }
  }, [programId]);

  const updateProgram = useCallback(async (updates: Partial<Program>): Promise<Program> => {
    if (!programId) throw new Error('No program ID provided');

    setError(null);

    try {
      const updatedProgram = await apiClient.creators.updateProgram(programId, updates);
      setProgram(prev => prev ? { ...prev, ...updatedProgram } : updatedProgram);
      return updatedProgram;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update program';
      setError(errorMessage);
      throw err;
    }
  }, [programId]);

  const saveSteps = useCallback(async (newSteps: ProgramStep[]): Promise<void> => {
    if (!programId) throw new Error('No program ID provided');

    setError(null);

    try {
      // This is a simplified implementation
      // In a real implementation, you would need to handle:
      // - Creating new steps
      // - Updating existing steps  
      // - Deleting removed steps
      // - Handling step order/connections

      for (const step of newSteps) {
        if (step.id.startsWith('node_')) {
          // New step - create it
          await apiClient.creators.addProgramStep(programId, {
            step_type: step.step_type,
            step_name: step.step_name,
            trigger_config_json: JSON.stringify(step.trigger_config),
            action_config_json: JSON.stringify(step.action_config),
            position_x: step.position.x,
            position_y: step.position.y,
          });
        } else {
          // Existing step - update it
          await apiClient.creators.updateProgramStep(programId, step.step_id, {
            step_name: step.step_name,
            trigger_config_json: JSON.stringify(step.trigger_config),
            action_config_json: JSON.stringify(step.action_config),
            position_x: step.position.x,
            position_y: step.position.y,
          });
        }
      }

      setSteps(newSteps);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save steps';
      setError(errorMessage);
      throw err;
    }
  }, [programId]);

  const executeProgram = useCallback(async (context?: { 
    user_context?: string; 
    debug_mode?: boolean 
  }): Promise<any> => {
    if (!programId) throw new Error('No program ID provided');

    setError(null);

    try {
      const result = await apiClient.creators.executeProgram(programId, context || {});
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to execute program';
      setError(errorMessage);
      throw err;
    }
  }, [programId]);

  const getAnalytics = useCallback(async (timeRangeDays = 30): Promise<any> => {
    if (!programId) throw new Error('No program ID provided');

    setError(null);

    try {
      const analytics = await apiClient.creators.getProgramAnalytics(programId, timeRangeDays);
      return analytics;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch analytics';
      setError(errorMessage);
      throw err;
    }
  }, [programId]);

  // Load program on mount or when programId changes
  useEffect(() => {
    loadProgram();
  }, [loadProgram]);

  return {
    program,
    steps,
    loading,
    error,
    updateProgram,
    saveSteps,
    executeProgram,
    getAnalytics,
  };
};