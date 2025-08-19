/**
 * Knowledge Management Testing Component
 * Frontend Service - Multi-Channel AI Coaching Platform
 */

'use client';

import React, { useState, useCallback } from 'react';
import { useKnowledge } from '@/hooks/useKnowledge';

const KnowledgeManagement: React.FC = () => {
  const {
    documents,
    loading,
    uploading,
    error,
    uploadDocument,
    searchKnowledge,
    refreshDocuments,
  } = useKnowledge();

  const [dragActive, setDragActive] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [uploadMetadata, setUploadMetadata] = useState({
    title: '',
    description: '',
  });

  // Handle file upload
  const handleFileUpload = useCallback(async (files: FileList) => {
    if (files.length === 0) return;

    const file = files[0];
    
    // Validate file type
    const allowedTypes = [
      'text/plain',
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/markdown',
    ];

    if (!allowedTypes.includes(file.type)) {
      alert('File type not supported. Please upload PDF, DOC, DOCX, TXT, or MD files.');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('File too large. Maximum size is 10MB.');
      return;
    }

    try {
      await uploadDocument(file, {
        title: uploadMetadata.title || file.name,
        description: uploadMetadata.description,
      });
      
      // Reset form
      setUploadMetadata({ title: '', description: '' });
      alert('Document uploaded successfully!');
    } catch (err) {
      alert('Failed to upload document. Please try again.');
    }
  }, [uploadDocument, uploadMetadata]);

  // Handle drag events
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files);
    }
  }, [handleFileUpload]);

  // Handle search
  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;

    setSearching(true);
    try {
      const results = await searchKnowledge(searchQuery, 10);
      setSearchResults(results);
    } catch (err) {
      alert('Search failed. Please try again.');
    } finally {
      setSearching(false);
    }
  }, [searchQuery, searchKnowledge]);

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Upload Section */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📁 Upload Documents
          </h3>
          
          {/* Upload Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Document Title
              </label>
              <input
                type="text"
                value={uploadMetadata.title}
                onChange={(e) => setUploadMetadata(prev => ({ ...prev, title: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="Enter document title..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (Optional)
              </label>
              <input
                type="text"
                value={uploadMetadata.description}
                onChange={(e) => setUploadMetadata(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="Describe the content..."
              />
            </div>
          </div>

          {/* Drag & Drop Area */}
          <div
            className={`
              border-2 border-dashed rounded-lg p-8 text-center transition-colors
              ${dragActive 
                ? 'border-blue-400 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
              }
              ${uploading ? 'opacity-50 pointer-events-none' : ''}
            `}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {uploading ? (
              <div className="space-y-2">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-sm text-gray-600">Uploading and processing...</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-4xl">📄</div>
                <div>
                  <p className="text-lg font-medium text-gray-900">
                    Drop files here or click to upload
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    Supports PDF, DOC, DOCX, TXT, MD (max 10MB)
                  </p>
                </div>
                <input
                  type="file"
                  className="hidden"
                  id="file-upload"
                  accept=".pdf,.doc,.docx,.txt,.md"
                  onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
                />
                <label
                  htmlFor="file-upload"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer transition-colors"
                >
                  Choose Files
                </label>
              </div>
            )}
          </div>
        </div>

        {/* Knowledge Search */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            🔍 Search Knowledge Base
          </h3>
          
          <div className="flex space-x-4 mb-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Search your knowledge base..."
            />
            <button
              onClick={handleSearch}
              disabled={searching || !searchQuery.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {searching ? 'Searching...' : 'Search'}
            </button>
          </div>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Search Results:</h4>
              {searchResults.map((result, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-sm text-gray-900 mb-2">{result.content}</p>
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span>Source: {result.source}</span>
                        <span>Relevance: {(result.relevance_score * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Documents List */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              📚 Uploaded Documents ({documents.length})
            </h3>
            <button
              onClick={refreshDocuments}
              disabled={loading}
              className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {documents.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-4xl mb-2">📭</div>
              <p className="text-gray-600">No documents uploaded yet</p>
              <p className="text-sm text-gray-500 mt-1">Upload your first document to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div key={doc.id} className="p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{doc.title}</h4>
                      {doc.description && (
                        <p className="text-sm text-gray-600 mt-1">{doc.description}</p>
                      )}
                      <div className="flex items-center space-x-4 text-xs text-gray-500 mt-2">
                        <span>📁 {doc.filename}</span>
                        <span>📊 {(doc.file_size / 1024).toFixed(1)} KB</span>
                        <span>📅 {new Date(doc.upload_date).toLocaleDateString()}</span>
                        <span className={`
                          px-2 py-1 rounded-full text-xs
                          ${doc.processing_status === 'completed' ? 'bg-green-100 text-green-800' : ''}
                          ${doc.processing_status === 'processing' ? 'bg-yellow-100 text-yellow-800' : ''}
                          ${doc.processing_status === 'pending' ? 'bg-gray-100 text-gray-800' : ''}
                          ${doc.processing_status === 'failed' ? 'bg-red-100 text-red-800' : ''}
                        `}>
                          {doc.processing_status}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeManagement;