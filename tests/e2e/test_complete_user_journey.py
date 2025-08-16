"""
End-to-end tests for complete user journeys.
Tests full workflows from user registration to AI interactions.
"""

import asyncio


class TestCompleteUserJourney:
    """Test complete user journeys through the platform."""

    async def test_new_user_onboarding_journey(self, service_clients):
        """Test complete new user onboarding flow."""
        auth_client = service_clients["auth"]
        creator_hub_client = service_clients["creator_hub"]
        ai_client = service_clients["ai_engine"]
        
        # Step 1: User registration
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
            "tenant_id": "new-tenant"
        }
        
        register_response = await auth_client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        user_info = register_response.json()
        assert user_info["email"] == user_data["email"]
        
        # Step 2: User login
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Step 3: Access creator hub (authenticated)
        hub_response = await creator_hub_client.get("/api/v1/health", headers=headers)
        assert hub_response.status_code != 401  # Should be authenticated
        
        # Step 4: Test AI interaction
        ai_response = await ai_client.post("/api/v1/ai/ollama/test-chat", json={
            "message": "Hello, I'm a new user. Can you help me get started?"
        })
        assert ai_response.status_code == 200
        
        ai_result = ai_response.json()
        assert "response" in ai_result
        assert len(ai_result["response"]) > 0

    async def test_creator_content_workflow(self, service_clients):
        """Test creator content creation and AI processing workflow."""
        auth_client = service_clients["auth"]
        ai_client = service_clients["ai_engine"]
        
        # Step 1: Creator registration
        creator_data = {
            "email": "creator@example.com",
            "password": "CreatorPass123!",
            "full_name": "Content Creator",
            "tenant_id": "creator-tenant"
        }
        
        await auth_client.post("/api/v1/auth/register", json=creator_data)
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": creator_data["email"],
            "password": creator_data["password"]
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Create content for AI processing
        content_text = """
        Welcome to my coaching program! This is a comprehensive guide to personal development.
        We'll cover goal setting, time management, and building positive habits.
        """
        
        # Step 3: Generate embeddings for content
        embedding_response = await ai_client.post("/api/v1/ai/ollama/test-embedding", json={
            "text": content_text
        })
        assert embedding_response.status_code == 200
        
        embedding_data = embedding_response.json()
        assert "embedding" in embedding_data
        assert len(embedding_data["embedding"]) > 0
        
        # Step 4: Test AI chat with context
        chat_response = await ai_client.post("/api/v1/ai/ollama/test-chat", json={
            "message": "What topics does this coaching program cover?",
            "context": content_text
        })
        assert chat_response.status_code == 200
        
        chat_data = chat_response.json()
        response_text = chat_data["response"].lower()
        
        # Verify AI understood the content context
        expected_topics = ["goal", "time", "habit"]
        topic_mentioned = any(topic in response_text for topic in expected_topics)
        assert topic_mentioned, "AI response should mention coaching topics"

    async def test_multi_user_interaction_workflow(self, service_clients):
        """Test workflow with multiple users interacting with the system."""
        auth_client = service_clients["auth"]
        ai_client = service_clients["ai_engine"]
        
        # Create multiple users
        users = [
            {
                "email": "user1@example.com",
                "password": "Password123!",
                "full_name": "User One",
                "tenant_id": "tenant-1"
            },
            {
                "email": "user2@example.com",
                "password": "Password123!",
                "full_name": "User Two",
                "tenant_id": "tenant-2"
            }
        ]
        
        user_tokens = []
        
        # Register and login all users
        for user_data in users:
            await auth_client.post("/api/v1/auth/register", json=user_data)
            login_response = await auth_client.post("/api/v1/auth/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            
            token = login_response.json()["access_token"]
            user_tokens.append(token)
        
        # Test concurrent AI interactions from different users
        tasks = []
        for i, token in enumerate(user_tokens):
            task = ai_client.post("/api/v1/ai/ollama/test-chat", json={
                "message": f"Hello, I'm user {i+1}. What can you help me with?"
            })
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All users should get responses
        for response in responses:
            assert response.status_code == 200
            result = response.json()
            assert "response" in result
            assert len(result["response"]) > 0

    async def test_error_recovery_workflow(self, service_clients):
        """Test user workflow with error scenarios and recovery."""
        auth_client = service_clients["auth"]
        ai_client = service_clients["ai_engine"]
        
        # Step 1: Attempt login with invalid credentials
        invalid_login = await auth_client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert invalid_login.status_code == 401
        
        # Step 2: Register user properly
        user_data = {
            "email": "recovery@example.com",
            "password": "RecoveryPass123!",
            "full_name": "Recovery User",
            "tenant_id": "recovery-tenant"
        }
        
        register_response = await auth_client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # Step 3: Login successfully
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        
        # Step 4: Test AI service with invalid input, then valid input
        invalid_ai_response = await ai_client.post("/api/v1/ai/ollama/test-chat", json={
            "message": ""  # Empty message should fail
        })
        assert invalid_ai_response.status_code == 422
        
        # Step 5: Recover with valid AI request
        valid_ai_response = await ai_client.post("/api/v1/ai/ollama/test-chat", json={
            "message": "Now this is a valid message"
        })
        assert valid_ai_response.status_code == 200

    async def test_service_availability_workflow(self, service_clients):
        """Test complete workflow ensuring all services are available."""
        # Test all services are responding
        services_to_test = ["auth", "creator_hub", "ai_engine", "channel"]
        
        for service_name in services_to_test:
            client = service_clients[service_name]
            response = await client.get("/api/v1/health")
            assert response.status_code == 200, f"{service_name} service is not available"
            
            health_data = response.json()
            assert health_data["status"] == "healthy", f"{service_name} service is not healthy"

    async def test_performance_workflow(self, service_clients):
        """Test system performance under typical user load."""
        auth_client = service_clients["auth"]
        ai_client = service_clients["ai_engine"]
        
        # Register a test user
        user_data = {
            "email": "perf@example.com",
            "password": "PerfTest123!",
            "full_name": "Performance User",
            "tenant_id": "perf-tenant"
        }
        
        await auth_client.post("/api/v1/auth/register", json=user_data)
        
        # Test multiple rapid requests (simulating active user)
        tasks = []
        for i in range(5):
            # Alternate between different types of requests
            if i % 2 == 0:
                task = auth_client.post("/api/v1/auth/login", json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
            else:
                task = ai_client.post("/api/v1/ai/ollama/test-chat", json={
                    "message": f"Performance test message {i}"
                })
            tasks.append(task)
        
        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that most requests succeeded (allowing for some failures under load)
        successful_responses = [r for r in responses if not isinstance(r, Exception) and r.status_code < 400]
        success_rate = len(successful_responses) / len(responses)
        
        assert success_rate >= 0.8, f"Success rate {success_rate} is too low for performance test"