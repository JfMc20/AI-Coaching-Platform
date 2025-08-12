#!/usr/bin/env python3
"""
Test script for ChromaDB and Ollama setup
Validates multi-tenant ChromaDB configuration and Ollama model availability
"""

import asyncio
import sys
import os
import logging
from typing import Dict, Any, List
import uuid
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.ai.chromadb_manager import ChromaDBManager, ChromaDBError
from shared.ai.ollama_manager import OllamaManager, OllamaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChromaDBOllamaSetupTester:
    """Test ChromaDB and Ollama setup and integration"""
    
    def __init__(self):
        self.chromadb_manager = None
        self.ollama_manager = None
        self.test_results = {
            "chromadb_health": False,
            "ollama_health": False,
            "models_available": False,
            "embedding_generation": False,
            "chat_generation": False,
            "chromadb_storage": False,
            "tenant_isolation": False,
            "integration_test": False
        }
    
    async def setup(self):
        """Initialize managers"""
        logger.info("🔧 Setting up ChromaDB and Ollama managers...")
        
        try:
            # Initialize ChromaDB manager
            self.chromadb_manager = ChromaDBManager(
                chromadb_url="http://localhost:8000",
                shard_count=10,
                max_connections=5
            )
            
            # Initialize Ollama manager
            self.ollama_manager = OllamaManager(
                ollama_url="http://localhost:11434",
                embedding_model="nomic-embed-text",
                chat_model="gpt-oss-20b",
                timeout=30
            )
            
            logger.info("✅ Managers initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize managers: {str(e)}")
            raise
    
    async def test_chromadb_health(self) -> bool:
        """Test ChromaDB health and connectivity"""
        logger.info("🔍 Testing ChromaDB health...")
        
        try:
            health = await self.chromadb_manager.health_check()
            
            logger.info(f"✅ ChromaDB health check passed:")
            logger.info(f"   - Status: {health['status']}")
            logger.info(f"   - URL: {health['url']}")
            logger.info(f"   - Collections: {health['collections_count']}")
            logger.info(f"   - Shard count: {health['shard_count']}")
            
            self.test_results["chromadb_health"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ ChromaDB health check failed: {str(e)}")
            return False
    
    async def test_ollama_health(self) -> bool:
        """Test Ollama health and connectivity"""
        logger.info("🔍 Testing Ollama health...")
        
        try:
            health = await self.ollama_manager.health_check()
            
            logger.info(f"✅ Ollama health check passed:")
            logger.info(f"   - Status: {health['status']}")
            logger.info(f"   - URL: {health['url']}")
            logger.info(f"   - Models count: {health['models_count']}")
            logger.info(f"   - Embedding model: {health['embedding_model']['name']} "
                       f"({'available' if health['embedding_model']['available'] else 'not available'})")
            logger.info(f"   - Chat model: {health['chat_model']['name']} "
                       f"({'available' if health['chat_model']['available'] else 'not available'})")
            
            self.test_results["ollama_health"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Ollama health check failed: {str(e)}")
            return False
    
    async def test_models_availability(self) -> bool:
        """Test and ensure required models are available"""
        logger.info("🔍 Testing model availability...")
        
        try:
            # List current models
            models = await self.ollama_manager.list_models()
            logger.info(f"📋 Available models ({len(models)}):")
            for model in models:
                logger.info(f"   - {model.name} (size: {model.size}, modified: {model.modified_at})")
            
            # Ensure required models are available
            model_status = await self.ollama_manager.ensure_models_available()
            
            logger.info(f"✅ Model availability ensured:")
            logger.info(f"   - Embedding model ({self.ollama_manager.embedding_model}): "
                       f"{'✅' if model_status['embedding_model'] else '❌'}")
            logger.info(f"   - Chat model ({self.ollama_manager.chat_model}): "
                       f"{'✅' if model_status['chat_model'] else '❌'}")
            
            success = all(model_status.values())
            self.test_results["models_available"] = success
            return success
            
        except Exception as e:
            logger.error(f"❌ Model availability test failed: {str(e)}")
            return False
    
    async def test_embedding_generation(self) -> bool:
        """Test embedding generation"""
        logger.info("🔍 Testing embedding generation...")
        
        try:
            test_texts = [
                "This is a test document for ChromaDB and Ollama integration.",
                "Multi-tenant architecture ensures data isolation between creators.",
                "Vector embeddings enable semantic search capabilities."
            ]
            
            response = await self.ollama_manager.generate_embeddings(test_texts)
            
            logger.info(f"✅ Embedding generation successful:")
            logger.info(f"   - Model: {response.model}")
            logger.info(f"   - Embeddings count: {len(response.embeddings)}")
            logger.info(f"   - Embedding dimensions: {len(response.embeddings[0]) if response.embeddings else 0}")
            logger.info(f"   - Processing time: {response.processing_time_ms:.2f}ms")
            logger.info(f"   - Token count: {response.token_count}")
            
            # Validate embeddings
            assert len(response.embeddings) == len(test_texts)
            assert all(len(emb) > 0 for emb in response.embeddings)
            assert response.processing_time_ms > 0
            
            self.test_results["embedding_generation"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Embedding generation test failed: {str(e)}")
            return False
    
    async def test_chat_generation(self) -> bool:
        """Test chat response generation"""
        logger.info("🔍 Testing chat generation...")
        
        try:
            test_prompt = "Hello! Please explain what ChromaDB is in one sentence."
            
            response = await self.ollama_manager.generate_chat_response(
                prompt=test_prompt,
                temperature=0.7
            )
            
            logger.info(f"✅ Chat generation successful:")
            logger.info(f"   - Model: {response.model}")
            logger.info(f"   - Prompt: {test_prompt}")
            logger.info(f"   - Response: {response.response[:100]}...")
            logger.info(f"   - Processing time: {response.processing_time_ms:.2f}ms")
            logger.info(f"   - Done: {response.done}")
            
            # Validate response
            assert len(response.response) > 0
            assert response.processing_time_ms > 0
            assert response.done is True
            
            self.test_results["chat_generation"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Chat generation test failed: {str(e)}")
            return False
    
    async def test_chromadb_storage(self) -> bool:
        """Test ChromaDB storage and retrieval"""
        logger.info("🔍 Testing ChromaDB storage...")
        
        try:
            creator_id = f"test-creator-{uuid.uuid4()}"
            document_id = f"test-doc-{uuid.uuid4()}"
            
            # Generate embeddings
            test_texts = [
                "ChromaDB storage test document 1",
                "ChromaDB storage test document 2"
            ]
            
            embedding_response = await self.ollama_manager.generate_embeddings(test_texts)
            
            # Store in ChromaDB
            metadatas = [
                {"source": "storage_test", "index": i, "test_type": "chromadb_storage"}
                for i in range(len(test_texts))
            ]
            
            ids = await self.chromadb_manager.add_embeddings(
                creator_id=creator_id,
                document_id=document_id,
                embeddings=embedding_response.embeddings,
                documents=test_texts,
                metadatas=metadatas
            )
            
            logger.info(f"✅ Embeddings stored successfully:")
            logger.info(f"   - Creator ID: {creator_id}")
            logger.info(f"   - Document ID: {document_id}")
            logger.info(f"   - Stored IDs: {len(ids)}")
            
            # Query embeddings
            query_results = await self.chromadb_manager.query_embeddings(
                creator_id=creator_id,
                query_embeddings=[embedding_response.embeddings[0]],
                n_results=5
            )
            
            logger.info(f"✅ Embeddings queried successfully:")
            logger.info(f"   - Results count: {len(query_results['ids'][0])}")
            logger.info(f"   - Documents: {query_results['documents'][0]}")
            
            # Validate results
            assert len(ids) == 2
            assert len(query_results["ids"][0]) == 2
            assert all(text in query_results["documents"][0] for text in test_texts)
            
            self.test_results["chromadb_storage"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ ChromaDB storage test failed: {str(e)}")
            return False
    
    async def test_tenant_isolation(self) -> bool:
        """Test multi-tenant data isolation"""
        logger.info("🔍 Testing tenant isolation...")
        
        try:
            creator1_id = f"test-creator-1-{uuid.uuid4()}"
            creator2_id = f"test-creator-2-{uuid.uuid4()}"
            document_id = f"test-doc-{uuid.uuid4()}"
            
            # Generate embeddings
            test_texts = ["Tenant isolation test document"]
            embedding_response = await self.ollama_manager.generate_embeddings(test_texts)
            
            # Store for creator 1
            await self.chromadb_manager.add_embeddings(
                creator_id=creator1_id,
                document_id=document_id,
                embeddings=embedding_response.embeddings,
                documents=test_texts,
                metadatas=[{"tenant": "creator1"}]
            )
            
            # Store for creator 2
            await self.chromadb_manager.add_embeddings(
                creator_id=creator2_id,
                document_id=document_id,
                embeddings=embedding_response.embeddings,
                documents=test_texts,
                metadatas=[{"tenant": "creator2"}]
            )
            
            # Query for creator 1 - should only see creator 1's data
            results1 = await self.chromadb_manager.query_embeddings(
                creator_id=creator1_id,
                query_embeddings=embedding_response.embeddings,
                n_results=10
            )
            
            # Query for creator 2 - should only see creator 2's data
            results2 = await self.chromadb_manager.query_embeddings(
                creator_id=creator2_id,
                query_embeddings=embedding_response.embeddings,
                n_results=10
            )
            
            # Validate isolation
            creator1_metadata = results1["metadatas"][0]
            creator2_metadata = results2["metadatas"][0]
            
            assert all(meta["creator_id"] == creator1_id for meta in creator1_metadata)
            assert all(meta["creator_id"] == creator2_id for meta in creator2_metadata)
            
            # Verify no cross-tenant data leakage
            creator1_ids = set(results1["ids"][0])
            creator2_ids = set(results2["ids"][0])
            assert creator1_ids.isdisjoint(creator2_ids)
            
            logger.info(f"✅ Tenant isolation verified:")
            logger.info(f"   - Creator 1 results: {len(results1['ids'][0])}")
            logger.info(f"   - Creator 2 results: {len(results2['ids'][0])}")
            logger.info(f"   - No data leakage: ✅")
            
            self.test_results["tenant_isolation"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Tenant isolation test failed: {str(e)}")
            return False
    
    async def test_integration(self) -> bool:
        """Test full integration workflow"""
        logger.info("🔍 Testing full integration workflow...")
        
        try:
            creator_id = f"integration-test-{uuid.uuid4()}"
            
            # Step 1: Generate embeddings with Ollama
            documents = [
                "Integration test: ChromaDB and Ollama working together",
                "Multi-tenant vector database with AI embeddings",
                "Scalable architecture for coaching AI platform"
            ]
            
            embedding_response = await self.ollama_manager.generate_embeddings(documents)
            
            # Step 2: Store embeddings in ChromaDB
            document_id = f"integration-doc-{uuid.uuid4()}"
            metadatas = [
                {"type": "integration_test", "step": i + 1, "timestamp": datetime.utcnow().isoformat()}
                for i in range(len(documents))
            ]
            
            ids = await self.chromadb_manager.add_embeddings(
                creator_id=creator_id,
                document_id=document_id,
                embeddings=embedding_response.embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            # Step 3: Query similar content
            query_text = "How does the AI platform handle multiple tenants?"
            query_embedding_response = await self.ollama_manager.generate_embeddings([query_text])
            
            search_results = await self.chromadb_manager.query_embeddings(
                creator_id=creator_id,
                query_embeddings=query_embedding_response.embeddings,
                n_results=3
            )
            
            # Step 4: Generate AI response based on retrieved context
            context_docs = search_results["documents"][0]
            context = "\n".join(context_docs)
            
            chat_prompt = f"""Based on the following context, answer the question: {query_text}
            
Context:
{context}

Answer:"""
            
            chat_response = await self.ollama_manager.generate_chat_response(
                prompt=chat_prompt,
                temperature=0.7
            )
            
            logger.info(f"✅ Full integration workflow successful:")
            logger.info(f"   - Documents embedded: {len(documents)}")
            logger.info(f"   - Documents stored: {len(ids)}")
            logger.info(f"   - Search results: {len(search_results['ids'][0])}")
            logger.info(f"   - Query: {query_text}")
            logger.info(f"   - AI Response: {chat_response.response[:150]}...")
            
            # Validate workflow
            assert len(ids) == len(documents)
            assert len(search_results["ids"][0]) > 0
            assert len(chat_response.response) > 0
            
            self.test_results["integration_test"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Integration test failed: {str(e)}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        logger.info("🚀 Starting ChromaDB and Ollama setup tests...")
        
        try:
            await self.setup()
            
            # Run tests in sequence
            tests = [
                ("ChromaDB Health", self.test_chromadb_health),
                ("Ollama Health", self.test_ollama_health),
                ("Models Availability", self.test_models_availability),
                ("Embedding Generation", self.test_embedding_generation),
                ("Chat Generation", self.test_chat_generation),
                ("ChromaDB Storage", self.test_chromadb_storage),
                ("Tenant Isolation", self.test_tenant_isolation),
                ("Full Integration", self.test_integration)
            ]
            
            for test_name, test_func in tests:
                logger.info(f"\n{'='*60}")
                logger.info(f"Running: {test_name}")
                logger.info(f"{'='*60}")
                
                try:
                    success = await test_func()
                    if success:
                        logger.info(f"✅ {test_name}: PASSED")
                    else:
                        logger.error(f"❌ {test_name}: FAILED")
                except Exception as e:
                    logger.error(f"💥 {test_name}: ERROR - {str(e)}")
            
            # Summary
            passed_tests = sum(1 for result in self.test_results.values() if result)
            total_tests = len(self.test_results)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"TEST SUMMARY")
            logger.info(f"{'='*60}")
            logger.info(f"Passed: {passed_tests}/{total_tests}")
            logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            for test_name, result in self.test_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"  {test_name}: {status}")
            
            return {
                "success": passed_tests == total_tests,
                "passed": passed_tests,
                "total": total_tests,
                "results": self.test_results
            }
            
        except Exception as e:
            logger.error(f"💥 Test suite failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": self.test_results
            }
        
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up resources...")
        
        try:
            if self.chromadb_manager:
                await self.chromadb_manager.close()
            
            if self.ollama_manager:
                await self.ollama_manager.close()
                
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {str(e)}")


async def main():
    """Main test execution"""
    tester = ChromaDBOllamaSetupTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())