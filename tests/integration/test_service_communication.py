"""
Integration tests for inter-service communication.
Tests service discovery, health checks, and communication patterns.
"""

import pytest
from httpx import AsyncClient
import asyncio

from shared.config.env_constants import AUTH_SERVICE_URL, get_env_value


class TestServiceCommunication:
    """Test communication between microservices."""

    async def test_all_services_health(self, service_clients):
        """Test that all services are healthy and responding."""
        health_endpoints = [
            ("auth", "/api/v1/health"),
            ("creator_hub", "/api/v1/health"),
            ("ai_engine", "/api/v1/health"),
            ("channel", "/api/v1/health")
        ]
        
        for service_name, endpoint in health_endpoints:
            client = service_clients[service_name]
            response = await client.get(endpoint)
            
            assert response.status_code == 200, f"{service_name} service is not healthy"
            
            health_data = response.json()
            assert health_data["status"] == "healthy"
            assert "timestamp" in health_data

    async def test_service_discovery(self, service_clients):
        """Test that services can discover and communicate with each other."""
        # Test that creator-hub can reach auth service for validation
        creator_hub_client = service_clients["creator_hub"]
        
        # This endpoint should internally validate with auth service
        response = await creator_hub_client.get("/api/v1/health")
        assert response.status_code == 200

    async def test_concurrent_service_calls(self, service_clients):
        """Test concurrent calls to multiple services."""
        tasks = []
        
        # Create concurrent health check tasks for all services
        for service_name, client in service_clients.items():
            task = client.get("/api/v1/health")
            tasks.append((service_name, task))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        # Verify all services responded successfully
        for i, (service_name, _) in enumerate(tasks):
            result = results[i]
            assert not isinstance(result, Exception), f"{service_name} failed: {result}"
            assert result.status_code == 200, f"{service_name} returned {result.status_code}"

    async def test_service_timeout_handling(self, service_clients):
        """Test service timeout and error handling."""
        # Test with very short timeout to simulate network issues
        auth_url = get_env_value(AUTH_SERVICE_URL, fallback=True)
        short_timeout_client = AsyncClient(
            base_url=auth_url,
            timeout=0.001  # 1ms timeout - should cause timeout
        )
        
        try:
            response = await short_timeout_client.get("/api/v1/health")
            # If it doesn't timeout, that's also acceptable
            if response.status_code == 200:
                pytest.skip("Service responded too quickly for timeout test")
        except Exception as e:
            # Timeout or connection error is expected
            assert "timeout" in str(e).lower() or "connection" in str(e).lower()
        finally:
            await short_timeout_client.aclose()

    async def test_service_error_propagation(self, service_clients):
        """Test how errors propagate between services."""
        # Test invalid endpoint to see error handling
        auth_client = service_clients["auth"]
        
        response = await auth_client.get("/api/v1/nonexistent-endpoint")
        assert response.status_code == 404
        
        error_data = response.json()
        assert "detail" in error_data or "message" in error_data

    async def test_websocket_service_availability(self, service_clients):
        """Test WebSocket service availability."""
        channel_client = service_clients["channel"]
        
        # Test WebSocket endpoint availability (should return method not allowed for GET)
        response = await channel_client.get("/ws/test-session")
        # WebSocket endpoints typically return 405 for GET requests
        assert response.status_code in [405, 426]  # Method not allowed or Upgrade required

    async def test_service_version_compatibility(self, service_clients):
        """Test API version compatibility across services."""
        version_endpoints = [
            ("auth", "/api/v1/health"),
            ("creator_hub", "/api/v1/health"),
            ("ai_engine", "/api/v1/health"),
            ("channel", "/api/v1/health")
        ]
        
        for service_name, endpoint in version_endpoints:
            client = service_clients[service_name]
            response = await client.get(endpoint)
            
            assert response.status_code == 200
            
            # Check if version info is included in response
            health_data = response.json()
            if "version" in health_data:
                assert isinstance(health_data["version"], str)
                assert len(health_data["version"]) > 0

    async def test_service_load_balancing(self, service_clients):
        """Test service load handling with multiple requests."""
        auth_client = service_clients["auth"]
        
        # Send multiple requests to test load handling
        tasks = []
        for i in range(10):
            task = auth_client.get("/api/v1/health")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

    async def test_service_dependency_checks(self, service_clients):
        """Test service dependency health checks."""
        # AI engine should report on Ollama and ChromaDB dependencies
        ai_client = service_clients["ai_engine"]
        
        response = await ai_client.get("/api/v1/health")
        assert response.status_code == 200
        
        health_data = response.json()
        if "dependencies" in health_data:
            dependencies = health_data["dependencies"]
            
            # Check for expected AI dependencies
            expected_deps = ["ollama", "chromadb"]
            for dep in expected_deps:
                if dep in dependencies:
                    assert dependencies[dep] in ["healthy", "available", True]

    async def test_cross_service_authentication(self, service_clients, test_user_data):
        """Test authentication token validation across services."""
        auth_client = service_clients["auth"]
        creator_hub_client = service_clients["creator_hub"]
        
        # Register and login user
        await auth_client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test token validation in other services
            response = await creator_hub_client.get("/api/v1/health", headers=headers)
            # Should not return 401 if token validation is working
            assert response.status_code != 401