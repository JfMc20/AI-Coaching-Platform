/**
 * Knowledge Management Hook
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

import { useState, useCallback, useEffect, useMemo } from 'react';
import { apiClient } from '@/lib/apiClient';

interface Document {
  id: string;
  title: string;
  description?: string;
  filename: string;
  content_type: string;
  file_size: number;
  upload_date: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
}

interface KnowledgeSearchResult {
  content: string;
  source: string;
  relevance_score: number;
  metadata?: any;
}

interface UseKnowledgeResult {
  documents: Document[];
  loading: boolean;
  uploading: boolean;
  error: string | null;
  
  // Actions
  uploadDocument: (file: File, metadata: { title: string; description?: string }) => Promise<Document>;
  searchKnowledge: (query: string, limit?: number) => Promise<KnowledgeSearchResult[]>;
  refreshDocuments: () => Promise<void>;
}

interface PersonalityProfile {
  personality_summary: string;
  dominant_traits: Array<{
    dimension: string;
    value: string;
    confidence: number;
  }>;
  key_methodologies: string[];
  confidence_score: number;
}

interface UsePersonalityResult {
  profile: PersonalityProfile | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  analyzePersonality: (includeDocuments?: boolean, forceReanalysis?: boolean) => Promise<PersonalityProfile>;
  generatePersonalizedPrompt: (context: string, userQuery: string, messageTemplate?: string) => Promise<{
    personalized_prompt: string;
    confidence_score: number;
  }>;
}

// Knowledge Management Hook
export const useKnowledge = (): UseKnowledgeResult => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.creators.getDocuments(1, 50); // Get first 50 documents
      setDocuments(response.items || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch documents';
      setError(errorMessage);
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const uploadDocument = useCallback(async (
    file: File, 
    metadata: { title: string; description?: string }
  ): Promise<Document> => {
    setUploading(true);
    setError(null);

    try {
      const newDocument = await apiClient.creators.uploadDocument(file, metadata);
      setDocuments(prev => [newDocument, ...prev]);
      return newDocument;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload document';
      setError(errorMessage);
      throw err;
    } finally {
      setUploading(false);
    }
  }, []);

  const searchKnowledge = useCallback(async (
    query: string, 
    limit = 10
  ): Promise<KnowledgeSearchResult[]> => {
    setError(null);

    try {
      const response = await apiClient.creators.searchKnowledge(query, limit);
      return response.results || [];
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to search knowledge';
      setError(errorMessage);
      throw err;
    }
  }, []);

  // Load documents on mount
  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  return {
    documents,
    loading,
    uploading,
    error,
    uploadDocument,
    searchKnowledge,
    refreshDocuments,
  };
};

// Personality Management Hook
export const usePersonality = (): UsePersonalityResult => {
  const [profile, setProfile] = useState<PersonalityProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzePersonality = useCallback(async (
    includeDocuments = true,
    forceReanalysis = false
  ): Promise<PersonalityProfile> => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.creators.analyzePersonality(includeDocuments, forceReanalysis);
      const newProfile = response.personality_profile;
      setProfile(newProfile);
      return newProfile;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to analyze personality';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const generatePersonalizedPrompt = useCallback(async (
    context: string,
    userQuery: string,
    messageTemplate?: string
  ): Promise<{ personalized_prompt: string; confidence_score: number }> => {
    setError(null);

    try {
      const response = await apiClient.creators.generatePersonalizedPrompt(
        context,
        userQuery,
        messageTemplate
      );
      return {
        personalized_prompt: response.personalized_prompt,
        confidence_score: response.confidence_score,
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate personalized prompt';
      setError(errorMessage);
      throw err;
    }
  }, []);

  return {
    profile,
    loading,
    error,
    analyzePersonality,
    generatePersonalizedPrompt,
  };
};

// Combined Knowledge & Personality Hook
export const useCreatorProfile = () => {
  const knowledge = useKnowledge();
  const personality = usePersonality();

  const initializeProfile = useCallback(async () => {
    // Load documents first
    await knowledge.refreshDocuments();
    
    // Then analyze personality if we have documents
    if (knowledge.documents.length > 0) {
      await personality.analyzePersonality(true, false);
    }
  }, [knowledge, personality]);

  const isProfileComplete = useMemo(() => {
    return knowledge.documents.length > 0 && personality.profile !== null;
  }, [knowledge.documents.length, personality.profile]);

  return {
    knowledge,
    personality,
    initializeProfile,
    isProfileComplete,
    loading: knowledge.loading || personality.loading,
    error: knowledge.error || personality.error,
  };
};