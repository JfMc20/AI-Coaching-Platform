/**
 * Personality Analysis Testing Component
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

'use client';

import React, { useState, useEffect } from 'react';
import { usePersonality } from '@/hooks/useKnowledge';

const PersonalityAnalysis: React.FC = () => {
  const {
    profile,
    loading,
    error,
    analyzePersonality,
    generatePersonalizedPrompt,
  } = usePersonality();

  const [analysisOptions, setAnalysisOptions] = useState({
    includeDocuments: true,
    forceReanalysis: false,
  });

  const [promptTest, setPromptTest] = useState({
    context: '',
    userQuery: '',
    messageTemplate: '',
    result: null as any,
    loading: false,
  });

  const [consistencyTest, setConsistencyTest] = useState({
    testPrompts: [
      'How can I improve my motivation?',
      'I feel stuck in my career, what should I do?',
      'How do I balance work and life better?',
    ],
    results: [] as any[],
    loading: false,
  });

  // Load profile on mount
  useEffect(() => {
    if (!profile && !loading) {
      handleAnalyzePersonality();
    }
  }, [profile, loading]);

  const handleAnalyzePersonality = async () => {
    try {
      await analyzePersonality(analysisOptions.includeDocuments, analysisOptions.forceReanalysis);
    } catch (err) {
      console.error('Personality analysis failed:', err);
    }
  };

  const handlePromptTest = async () => {
    if (!promptTest.context.trim() || !promptTest.userQuery.trim()) {
      alert('Please enter both context and user query');
      return;
    }

    setPromptTest(prev => ({ ...prev, loading: true }));
    try {
      const result = await generatePersonalizedPrompt(
        promptTest.context,
        promptTest.userQuery,
        promptTest.messageTemplate || undefined
      );
      setPromptTest(prev => ({ ...prev, result, loading: false }));
    } catch (err) {
      alert('Prompt generation failed');
      setPromptTest(prev => ({ ...prev, loading: false }));
    }
  };

  const handleConsistencyTest = async () => {
    if (!profile) {
      alert('Please analyze personality first');
      return;
    }

    setConsistencyTest(prev => ({ ...prev, loading: true, results: [] }));
    
    try {
      const results = [];
      for (const prompt of consistencyTest.testPrompts) {
        const result = await generatePersonalizedPrompt(
          'General coaching context',
          prompt,
          'Provide helpful coaching advice'
        );
        results.push({ prompt, result });
      }
      setConsistencyTest(prev => ({ ...prev, results, loading: false }));
    } catch (err) {
      alert('Consistency test failed');
      setConsistencyTest(prev => ({ ...prev, loading: false }));
    }
  };

  const getTraitColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Personality Analysis Section */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            🎭 Creator Personality Analysis
          </h3>

          {/* Analysis Options */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">Analysis Options</h4>
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={analysisOptions.includeDocuments}
                  onChange={(e) => setAnalysisOptions(prev => ({ 
                    ...prev, 
                    includeDocuments: e.target.checked 
                  }))}
                  className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-400"
                />
                <span className="text-sm text-gray-700">
                  Include uploaded documents in analysis
                </span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={analysisOptions.forceReanalysis}
                  onChange={(e) => setAnalysisOptions(prev => ({ 
                    ...prev, 
                    forceReanalysis: e.target.checked 
                  }))}
                  className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-400"
                />
                <span className="text-sm text-gray-700">
                  Force reanalysis (ignore cached results)
                </span>
              </label>
            </div>
            <button
              onClick={handleAnalyzePersonality}
              disabled={loading}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Analyzing...' : 'Analyze Personality'}
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Personality Profile Results */}
          {profile ? (
            <div className="space-y-6">
              {/* Summary */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-semibold text-blue-900 mb-2">
                  Personality Summary
                </h4>
                <p className="text-blue-800">{profile.personality_summary}</p>
                <div className="mt-2">
                  <span className="text-sm text-blue-700">
                    Overall Confidence: {(profile.confidence_score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Traits */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">
                  Dominant Personality Traits
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {profile.dominant_traits.map((trait, index) => (
                    <div key={index} className="p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-900 capitalize">
                          {trait.dimension}
                        </span>
                        <span className={`
                          px-2 py-1 rounded-full text-xs font-medium
                          ${getTraitColor(trait.confidence)}
                        `}>
                          {(trait.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 capitalize">
                        Level: {trait.value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Methodologies */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">
                  Key Coaching Methodologies
                </h4>
                <div className="flex flex-wrap gap-2">
                  {profile.key_methodologies.map((methodology, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium"
                    >
                      {methodology}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-4xl mb-2">🎭</div>
              <p className="text-gray-600">No personality analysis available</p>
              <p className="text-sm text-gray-500 mt-1">
                Upload documents and run analysis to see personality profile
              </p>
            </div>
          )}
        </div>

        {/* Personalized Prompt Testing */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            ✨ Personalized Prompt Testing
          </h3>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Form */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Context
                </label>
                <textarea
                  value={promptTest.context}
                  onChange={(e) => setPromptTest(prev => ({ ...prev, context: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                  rows={3}
                  placeholder="Describe the coaching context..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  User Query
                </label>
                <input
                  type="text"
                  value={promptTest.userQuery}
                  onChange={(e) => setPromptTest(prev => ({ ...prev, userQuery: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="What would the user ask?"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Message Template (Optional)
                </label>
                <input
                  type="text"
                  value={promptTest.messageTemplate}
                  onChange={(e) => setPromptTest(prev => ({ ...prev, messageTemplate: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Template for the response..."
                />
              </div>

              <button
                onClick={handlePromptTest}
                disabled={promptTest.loading || !profile}
                className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 transition-colors"
              >
                {promptTest.loading ? 'Generating...' : 'Generate Personalized Prompt'}
              </button>
            </div>

            {/* Results */}
            <div>
              {promptTest.result ? (
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <h4 className="font-medium text-green-900 mb-2">
                      Generated Prompt
                    </h4>
                    <p className="text-green-800 text-sm">
                      {promptTest.result.personalized_prompt}
                    </p>
                    <div className="mt-2 text-xs text-green-700">
                      Confidence: {(promptTest.result.confidence_score * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-3xl mb-2">✨</div>
                  <p>Enter context and query to generate personalized prompt</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Consistency Testing */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            🎯 Personality Consistency Testing
          </h3>

          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-3">
              Test how consistently the AI maintains the creator's personality across different queries:
            </p>
            
            <div className="space-y-2 mb-4">
              {consistencyTest.testPrompts.map((prompt, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">#{index + 1}</span>
                  <input
                    type="text"
                    value={prompt}
                    onChange={(e) => {
                      const newPrompts = [...consistencyTest.testPrompts];
                      newPrompts[index] = e.target.value;
                      setConsistencyTest(prev => ({ ...prev, testPrompts: newPrompts }));
                    }}
                    className="flex-1 px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  />
                </div>
              ))}
            </div>

            <button
              onClick={handleConsistencyTest}
              disabled={consistencyTest.loading || !profile}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {consistencyTest.loading ? 'Testing Consistency...' : 'Run Consistency Test'}
            </button>
          </div>

          {/* Consistency Results */}
          {consistencyTest.results.length > 0 && (
            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Test Results:</h4>
              {consistencyTest.results.map((result, index) => (
                <div key={index} className="p-4 border border-gray-200 rounded-lg">
                  <div className="mb-2">
                    <span className="text-sm font-medium text-gray-900">
                      Query: {result.prompt}
                    </span>
                  </div>
                  <div className="text-sm text-gray-700 mb-2">
                    {result.result.personalized_prompt}
                  </div>
                  <div className="text-xs text-gray-500">
                    Confidence: {(result.result.confidence_score * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
              
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="text-sm text-blue-800">
                  <strong>Average Confidence:</strong> {' '}
                  {(consistencyTest.results.reduce((sum, r) => sum + r.result.confidence_score, 0) / consistencyTest.results.length * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PersonalityAnalysis;