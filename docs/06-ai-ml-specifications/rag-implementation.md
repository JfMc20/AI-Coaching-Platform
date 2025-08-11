# RAG Implementation Specification

## Overview

The Retrieval-Augmented Generation (RAG) system combines the power of large language models with creator-specific knowledge bases to provide accurate, contextual, and personalized coaching responses. This implementation uses LangChain for orchestration, ChromaDB for vector storage, and Ollama for LLM serving.

## Architecture Components

### Document Processing Pipeline
```python
from langchain.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma
import chromadb

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    async def process_document(self, file_path: str, creator_id: str, metadata: dict = None):
        """Process a document and store it in the vector database"""
        # Load document based on file type
        loader = self._get_loader(file_path)
        documents = loader.load()
        
        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        # Add metadata
        for chunk in chunks:
            chunk.metadata.update({
                'creator_id': creator_id,
                'source_file': file_path,
                'processed_at': datetime.utcnow().isoformat(),
                **(metadata or {})
            })
        
        # Generate embeddings and store
        collection_name = f"creator_{creator_id}"
        vectorstore = Chroma(
            client=self.chroma_client,
            collection_name=collection_name,
            embedding_function=self.embeddings
        )
        
        chunk_ids = await vectorstore.aadd_documents(chunks)
        
        return {
            'chunks_created': len(chunks),
            'chunk_ids': chunk_ids,
            'collection': collection_name
        }
```##
# Vector Database Configuration
```python
class VectorStoreManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    def get_or_create_collection(self, creator_id: str):
        """Get or create a collection for a specific creator"""
        collection_name = f"creator_{creator_id}"
        
        try:
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embeddings
            )
        except ValueError:
            # Collection doesn't exist, create it
            collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embeddings,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 200,
                    "hnsw:M": 16
                }
            )
        
        return collection
    
    async def similarity_search(
        self, 
        query: str, 
        creator_id: str, 
        k: int = 5,
        filter_metadata: dict = None,
        score_threshold: float = 0.7
    ):
        """Perform similarity search with optional filtering"""
        collection = self.get_or_create_collection(creator_id)
        
        # Build where clause for filtering
        where_clause = {"creator_id": creator_id}
        if filter_metadata:
            where_clause.update(filter_metadata)
        
        results = collection.query(
            query_texts=[query],
            n_results=k,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        # Filter by score threshold
        filtered_results = []
        for i, distance in enumerate(results['distances'][0]):
            similarity_score = 1 - distance  # Convert distance to similarity
            if similarity_score >= score_threshold:
                filtered_results.append({
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity_score': similarity_score
                })
        
        return filtered_results

### Retrieval Strategies
```python
class RetrievalStrategy:
    def __init__(self, vector_store_manager: VectorStoreManager):
        self.vector_store = vector_store_manager
        self.query_expander = QueryExpander()
        self.context_ranker = ContextRanker()
    
    async def retrieve_context(
        self, 
        query: str, 
        creator_id: str, 
        user_context: dict,
        strategy: str = "hybrid"
    ):
        """Retrieve relevant context using specified strategy"""
        
        if strategy == "semantic":
            return await self._semantic_retrieval(query, creator_id, user_context)
        elif strategy == "keyword":
            return await self._keyword_retrieval(query, creator_id, user_context)
        elif strategy == "hybrid":
            return await self._hybrid_retrieval(query, creator_id, user_context)
        else:
            raise ValueError(f"Unknown retrieval strategy: {strategy}")
    
    async def _semantic_retrieval(self, query: str, creator_id: str, user_context: dict):
        """Pure semantic similarity search"""
        # Expand query with user context
        expanded_query = await self.query_expander.expand(query, user_context)
        
        # Perform similarity search
        results = await self.vector_store.similarity_search(
            expanded_query, 
            creator_id, 
            k=10,
            score_threshold=0.6
        )
        
        # Rank results by relevance
        ranked_results = await self.context_ranker.rank(results, query, user_context)
        
        return ranked_results[:5]  # Return top 5
    
    async def _hybrid_retrieval(self, query: str, creator_id: str, user_context: dict):
        """Combine semantic and keyword-based retrieval"""
        # Get semantic results
        semantic_results = await self._semantic_retrieval(query, creator_id, user_context)
        
        # Get keyword results
        keyword_results = await self._keyword_retrieval(query, creator_id, user_context)
        
        # Merge and deduplicate
        combined_results = self._merge_results(semantic_results, keyword_results)
        
        # Final ranking
        final_results = await self.context_ranker.rank(combined_results, query, user_context)
        
        return final_results[:5]

### Context Assembly
```python
class ContextAssembler:
    def __init__(self):
        self.summarizer = DocumentSummarizer()
        self.relevance_scorer = RelevanceScorer()
        self.context_optimizer = ContextOptimizer()
    
    async def assemble_context(
        self, 
        retrieved_docs: list, 
        query: str, 
        user_context: dict,
        max_tokens: int = 4000
    ):
        """Assemble retrieved documents into coherent context"""
        
        # Score relevance of each document
        scored_docs = []
        for doc in retrieved_docs:
            relevance_score = await self.relevance_scorer.score(
                doc['document'], 
                query, 
                user_context
            )
            scored_docs.append({
                **doc,
                'relevance_score': relevance_score
            })
        
        # Sort by relevance
        scored_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Optimize context for token limit
        optimized_context = await self.context_optimizer.optimize(
            scored_docs, 
            max_tokens
        )
        
        # Format context
        formatted_context = self._format_context(optimized_context)
        
        return {
            'context': formatted_context,
            'sources': [doc['metadata'] for doc in optimized_context],
            'total_relevance_score': sum(doc['relevance_score'] for doc in optimized_context),
            'token_count': self._count_tokens(formatted_context)
        }
    
    def _format_context(self, docs: list) -> str:
        """Format documents into a coherent context string"""
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            source_info = f"Source {i}"
            if 'title' in doc['metadata']:
                source_info += f" ({doc['metadata']['title']})"
            
            context_parts.append(f"{source_info}:\n{doc['document']}\n")
        
        return "\n".join(context_parts)

### Response Generation Integration
```python
class RAGResponseGenerator:
    def __init__(self):
        self.retrieval_strategy = RetrievalStrategy(VectorStoreManager())
        self.context_assembler = ContextAssembler()
        self.llm = Ollama(model="llama3:8b", temperature=0.7)
        self.response_validator = ResponseValidator()
    
    async def generate_response(
        self, 
        user_message: str, 
        creator_id: str, 
        user_context: dict,
        conversation_history: list = None
    ):
        """Generate a response using RAG"""
        
        # Retrieve relevant context
        retrieved_docs = await self.retrieval_strategy.retrieve_context(
            user_message, 
            creator_id, 
            user_context
        )
        
        if not retrieved_docs:
            return await self._handle_no_context(user_message, user_context)
        
        # Assemble context
        context_assembly = await self.context_assembler.assemble_context(
            retrieved_docs, 
            user_message, 
            user_context
        )
        
        # Build prompt
        prompt = self._build_rag_prompt(
            user_message, 
            context_assembly['context'], 
            user_context,
            conversation_history
        )
        
        # Generate response
        response = await self.llm.agenerate([prompt])
        response_text = response.generations[0][0].text
        
        # Validate response
        validation = await self.response_validator.validate(
            response_text, 
            context_assembly['context'], 
            user_message
        )
        
        return {
            'response': response_text,
            'sources': context_assembly['sources'],
            'relevance_score': context_assembly['total_relevance_score'],
            'validation': validation,
            'context_used': len(retrieved_docs)
        }
    
    def _build_rag_prompt(
        self, 
        user_message: str, 
        context: str, 
        user_context: dict,
        conversation_history: list = None
    ) -> str:
        """Build the RAG prompt template"""
        
        creator_info = user_context.get('creator', {})
        user_profile = user_context.get('user_profile', {})
        
        prompt = f"""You are an AI coaching assistant representing {creator_info.get('name', 'the coach')}.

COACHING CONTEXT:
{context}

USER PROFILE:
- Goals: {', '.join(user_profile.get('goals', []))}
- Preferences: {user_profile.get('communication_style', 'supportive')}
- Progress: {user_profile.get('progress_summary', 'Getting started')}

CONVERSATION HISTORY:
{self._format_conversation_history(conversation_history)}

USER MESSAGE: {user_message}

INSTRUCTIONS:
1. Use the coaching context above to provide accurate, helpful information
2. Maintain the coach's voice and methodology
3. Be supportive and encouraging
4. Provide actionable advice when appropriate
5. If the context doesn't contain relevant information, acknowledge this and provide general guidance
6. Keep responses conversational and engaging

RESPONSE:"""
        
        return prompt

### Performance Optimization
```python
class RAGOptimizer:
    def __init__(self):
        self.cache = RAGCache()
        self.batch_processor = BatchProcessor()
        self.performance_monitor = PerformanceMonitor()
    
    async def optimize_retrieval(self, queries: list, creator_id: str):
        """Optimize retrieval for multiple queries"""
        
        # Check cache first
        cached_results = await self.cache.get_batch(queries, creator_id)
        uncached_queries = [q for q in queries if q not in cached_results]
        
        if not uncached_queries:
            return cached_results
        
        # Batch process uncached queries
        batch_results = await self.batch_processor.process_batch(
            uncached_queries, 
            creator_id
        )
        
        # Cache results
        await self.cache.set_batch(batch_results, creator_id)
        
        # Combine cached and new results
        all_results = {**cached_results, **batch_results}
        
        return all_results
    
    async def optimize_embeddings(self, texts: list):
        """Optimize embedding generation"""
        
        # Batch embeddings for efficiency
        embeddings = await self.batch_processor.generate_embeddings_batch(texts)
        
        return embeddings

### Quality Assurance
```python
class RAGQualityAssurance:
    def __init__(self):
        self.relevance_evaluator = RelevanceEvaluator()
        self.accuracy_checker = AccuracyChecker()
        self.hallucination_detector = HallucinationDetector()
    
    async def evaluate_rag_quality(
        self, 
        query: str, 
        retrieved_context: str, 
        generated_response: str
    ):
        """Evaluate the quality of RAG output"""
        
        quality_metrics = {
            'context_relevance': await self.relevance_evaluator.evaluate(
                query, retrieved_context
            ),
            'response_accuracy': await self.accuracy_checker.check(
                retrieved_context, generated_response
            ),
            'hallucination_score': await self.hallucination_detector.detect(
                retrieved_context, generated_response
            ),
            'context_utilization': self._calculate_context_utilization(
                retrieved_context, generated_response
            )
        }
        
        overall_quality = self._calculate_overall_quality(quality_metrics)
        
        return {
            'overall_quality': overall_quality,
            'metrics': quality_metrics,
            'recommendations': self._generate_quality_recommendations(quality_metrics)
        }
```

This RAG implementation provides a robust foundation for knowledge-grounded response generation while maintaining high quality and performance standards.