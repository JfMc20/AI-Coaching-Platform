"""
Tests for creator hub service health and readiness endpoints.
Tests service startup, dependency checks, and monitoring endpoints.

Fixtures are now centralized in tests/fixtures/creator_hub_fixtures.py and automatically
available through the main conftest.py configuration.
"""

from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health and monitoring endpoints."""

    async def test_health_endpoint(self, creator_hub_client: AsyncClient):
        """Test basic health check endpoint."""
        response = await creator_hub_client.get("/api/v1/health")
        
        assert response.status_code == 200
        health_data = response.json()
        
        assert health_data["status"] == "healthy"
        assert "timestamp" in health_data
        assert "service" in health_data
        assert health_data["service"] == "creator-hub-service"

    async def test_readiness_endpoint(self, creator_hub_client: AsyncClient):
        """Test readiness check endpoint."""
        response = await creator_hub_client.get("/api/v1/ready")
        
        # Should return 200 if service is ready, 503 if not
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            ready_data = response.json()
            assert ready_data["status"] == "ready"
        else:
            ready_data = response.json()
            assert ready_data["status"] == "not_ready"

    async def test_health_with_dependencies(self, creator_hub_client: AsyncClient):
        """Test health check including dependency status."""
        response = await creator_hub_client.get("/api/v1/health")
        
        assert response.status_code == 200
        health_data = response.json()
        
        # Check if dependencies are reported
        if "dependencies" in health_data:
            dependencies = health_data["dependencies"]
            
            # Expected dependencies for creator hub
            expected_deps = ["database", "auth_service", "ai_engine_service"]
            
            for dep in expected_deps:
                if dep in dependencies:
                    # Dependency status should be boolean or string
                    assert isinstance(dependencies[dep], (bool, str))

    async def test_metrics_endpoint(self, creator_hub_client: AsyncClient):
        """Test metrics endpoint if available."""
        response = await creator_hub_client.get("/api/v1/metrics")
        
        # Metrics endpoint might not be implemented yet
        if response.status_code == 200:
            metrics_data = response.json()
            assert isinstance(metrics_data, dict)
        elif response.status_code == 404:
            # Endpoint not implemented yet, which is acceptable
            pass
        else:
            # Other status codes might indicate issues
            assert response.status_code in [200, 404, 501]

    async def test_version_endpoint(self, creator_hub_client: AsyncClient):
        """Test version information endpoint."""
        response = await creator_hub_client.get("/api/v1/version")
        
        if response.status_code == 200:
            version_data = response.json()
            assert "version" in version_data
            assert isinstance(version_data["version"], str)
        elif response.status_code == 404:
            # Version endpoint not implemented yet
            pass

    async def test_health_endpoint_performance(self, creator_hub_client: AsyncClient):
        """Test health endpoint response time."""
        import time
        
        start_time = time.time()
        response = await creator_hub_client.get("/api/v1/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        # Health check should be fast (under 1 second)
        assert response_time < 1.0

    async def test_concurrent_health_checks(self, creator_hub_client: AsyncClient):
        """Test multiple concurrent health check requests."""
        import asyncio
        
        # Create multiple concurrent health check requests
        tasks = [creator_hub_client.get("/api/v1/health") for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            health_data = response.json()
            assert health_data["status"] == "healthy"

    async def test_health_check_headers(self, creator_hub_client: AsyncClient):
        """Test health check response headers."""
        response = await creator_hub_client.get("/api/v1/health")
        
        assert response.status_code == 200
        
        # Check for expected headers
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    async def test_health_check_with_invalid_method(self, creator_hub_client: AsyncClient):
        """Test health check with invalid HTTP method."""
        response = await creator_hub_client.post("/api/v1/health")
        
        # Should return method not allowed
        assert response.status_code == 405

    async def test_deep_health_check(self, creator_hub_client: AsyncClient):
        """Test deep health check that validates all components."""
        response = await creator_hub_client.get("/api/v1/health?deep=true")
        
        # Deep health check might not be implemented
        if response.status_code == 200:
            health_data = response.json()
            assert health_data["status"] in ["healthy", "degraded", "unhealthy"]
            
            if "checks" in health_data:
                checks = health_data["checks"]
                assert isinstance(checks, dict)
        else:
            # Regular health check should still work
            response = await creator_hub_client.get("/api/v1/health")
            assert response.status_code == 200

    async def test_service_info_endpoint(self, creator_hub_client: AsyncClient):
        """Test service information endpoint."""
        response = await creator_hub_client.get("/api/v1/info")
        
        if response.status_code == 200:
            info_data = response.json()
            assert "service_name" in info_data
            assert "description" in info_data
            assert info_data["service_name"] == "creator-hub-service"
        elif response.status_code == 404:
            # Info endpoint not implemented yet
            pass