/**
 * Canvas API Integration Hook
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

import { useCallback, useEffect } from 'react';
import { useCanvasStore } from '@/stores/canvasStore';
import { useProgram } from '@/hooks/usePrograms';
import { ProgramStep } from '@/types';

interface UseCanvasAPIProps {
  programId: string | null;
  autoSave?: boolean;
  autoSaveInterval?: number;
}

interface UseCanvasAPIResult {
  // State
  isSaving: boolean;
  isLoading: boolean;
  error: string | null;
  hasUnsavedChanges: boolean;
  
  // Actions
  saveProgram: () => Promise<void>;
  loadProgram: (programId: string) => Promise<void>;
  executeProgram: (context?: { user_context?: string; debug_mode?: boolean }) => Promise<any>;
  testProgram: () => Promise<any>;
  
  // Canvas operations
  exportProgram: () => any;
  importProgram: (data: any) => void;
}

export const useCanvasAPI = ({
  programId,
  autoSave = false,
  autoSaveInterval = 30000, // 30 seconds
}: UseCanvasAPIProps): UseCanvasAPIResult => {
  const {
    nodes,
    edges,
    currentProgramId,
    isDirty,
    isLoading: canvasLoading,
    error: canvasError,
    loadProgram: loadProgramToCanvas,
    saveProgram: saveProgramFromCanvas,
    setLoading,
    setError,
    setDirty,
  } = useCanvasStore();

  const {
    program,
    steps,
    loading: programLoading,
    error: programError,
    updateProgram,
    saveSteps,
    executeProgram: executeProgramAPI,
  } = useProgram(programId);

  const isLoading = canvasLoading || programLoading;
  const error = canvasError || programError;

  // Convert React Flow nodes to ProgramStep format
  const convertNodesToProgramSteps = useCallback((): ProgramStep[] => {
    return nodes.map(node => ({
      ...node.data.step,
      position: node.position,
    }));
  }, [nodes]);

  // Save program to backend
  const saveProgram = useCallback(async () => {
    if (!currentProgramId) {
      throw new Error('No program loaded');
    }

    setLoading(true);
    setError(null);

    try {
      const programSteps = convertNodesToProgramSteps();
      await saveSteps(programSteps);
      setDirty(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save program';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [currentProgramId, convertNodesToProgramSteps, saveSteps, setLoading, setError, setDirty]);

  // Load program from backend
  const loadProgram = useCallback(async (programId: string) => {
    setLoading(true);
    setError(null);

    try {
      // Wait for program data to load
      await new Promise(resolve => {
        const checkProgram = () => {
          if (program && steps) {
            resolve(void 0);
          } else {
            setTimeout(checkProgram, 100);
          }
        };
        checkProgram();
      });

      if (program && steps) {
        loadProgramToCanvas(programId, steps);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load program';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [program, steps, loadProgramToCanvas, setLoading, setError]);

  // Execute program
  const executeProgram = useCallback(async (context?: { 
    user_context?: string; 
    debug_mode?: boolean 
  }) => {
    if (!currentProgramId) {
      throw new Error('No program loaded');
    }

    try {
      const result = await executeProgramAPI(context);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to execute program';
      setError(errorMessage);
      throw err;
    }
  }, [currentProgramId, executeProgramAPI, setError]);

  // Test program with sample data
  const testProgram = useCallback(async () => {
    if (!currentProgramId) {
      throw new Error('No program loaded');
    }

    try {
      const result = await executeProgram({
        user_context: 'Test execution with sample user data',
        debug_mode: true,
      });
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to test program';
      setError(errorMessage);
      throw err;
    }
  }, [currentProgramId, executeProgram, setError]);

  // Export program as JSON
  const exportProgram = useCallback(() => {
    const programSteps = convertNodesToProgramSteps();
    
    return {
      version: '1.0',
      program: program,
      steps: programSteps,
      edges: edges,
      metadata: {
        exportDate: new Date().toISOString(),
        nodeCount: nodes.length,
        edgeCount: edges.length,
      },
    };
  }, [program, convertNodesToProgramSteps, edges, nodes.length]);

  // Import program from JSON
  const importProgram = useCallback((data: any) => {
    if (!data.steps || !Array.isArray(data.steps)) {
      throw new Error('Invalid program data: missing steps');
    }

    // Create a new program ID for imported programs
    const importedProgramId = `imported_${Date.now()}`;
    
    try {
      loadProgramToCanvas(importedProgramId, data.steps);
      
      // Update program title if provided
      if (data.program?.title) {
        useCanvasStore.getState().setProgramTitle(`${data.program.title} (Imported)`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to import program';
      setError(errorMessage);
      throw err;
    }
  }, [loadProgramToCanvas, setError]);

  // Auto-save functionality
  useEffect(() => {
    if (!autoSave || !isDirty || !currentProgramId) {
      return;
    }

    const autoSaveTimer = setTimeout(() => {
      saveProgram().catch(err => {
        console.warn('Auto-save failed:', err);
      });
    }, autoSaveInterval);

    return () => clearTimeout(autoSaveTimer);
  }, [autoSave, isDirty, currentProgramId, autoSaveInterval, saveProgram]);

  // Load program when programId changes
  useEffect(() => {
    if (programId && programId !== currentProgramId) {
      loadProgram(programId);
    }
  }, [programId, currentProgramId, loadProgram]);

  return {
    // State
    isSaving: canvasLoading,
    isLoading,
    error,
    hasUnsavedChanges: isDirty,
    
    // Actions
    saveProgram,
    loadProgram,
    executeProgram,
    testProgram,
    
    // Canvas operations
    exportProgram,
    importProgram,
  };
};