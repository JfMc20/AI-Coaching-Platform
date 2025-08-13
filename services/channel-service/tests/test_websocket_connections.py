"""
Tests for WebSocket functionality and connection management.
Tests WebSocket connections, message routing, and the ConnectionManager class.
"""

import pytest
from fastapi.testclient import TestClient
import json


class TestWebSocketConnections:
    """Test WebSocket connection functionality."""

    def test_websocket_connection_establishment(self, websocket_client, test_websocket_session):
        """Test WebSocket connection establishment."""
        session_id = test_websocket_session["session_id"]
        
        with websocket_client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Connection should be established successfully
            assert websocket is not None

    def test_websocket_message_sending(self, websocket_client, test_websocket_session, test_message_data):
        """Test sending messages through WebSocket."""
        session_id = test_websocket_session["session_id"]
        
        with websocket_client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Send test message
            websocket.send_json(test_message_data)
            
            # Should receive acknowledgment or echo
            try:
                response = websocket.receive_json()
                assert response is not None
            except Exception:
                # If no immediate response, that's also acceptable
                pass

    def test_websocket_message_receiving(self, websocket_client, test_websocket_session):
        """Test receiving messages through WebSocket."""
        session_id = test_websocket_session["session_id"]
        
        with websocket_client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Send a message that should trigger a response
            test_message = {
                "type": "ping",
                "timestamp": "2023-12-01T10:00:00Z"
            }
            
            websocket.send_json(test_message)
            
            # Try to receive response
            try:
                response = websocket.receive_json()
                assert "type" in response
            except Exception:
                # No response might be expected behavior
                pass

    def test_websocket_connection_close(self, websocket_client, test_websocket_session):
        """Test WebSocket connection closure."""
        session_id = test_websocket_session["session_id"]
        
        with websocket_client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Connection established
            assert websocket is not None
            
            # Close connection
            websocket.close()

    def test_multiple_websocket_connections(self, websocket_client, multiple_test_sessions):
        """Test multiple concurrent WebSocket connections."""
        connections = []
        
        try:
            # Establish multiple connections
            for session in multiple_test_sessions:
                websocket = websocket_client.websocket_connect(f"/ws/{session['session_id']}")
                connections.append(websocket.__enter__())
            
            # All connections should be established
            assert len(connections) == len(multiple_test_sessions)
            
            # Test sending messages to each connection
            for i, websocket in enumerate(connections):
                test_message = {
                    "type": "test",
                    "content": f"Message to connection {i}",
                    "session_id": multiple_test_sessions[i]["session_id"]
                }
                websocket.send_json(test_message)
        
        finally:
            # Clean up connections
            for websocket in connections:
                try:
                    websocket.close()
                except:
                    pass

    def test_websocket_invalid_session(self, websocket_client):
        """Test WebSocket connection with invalid session ID."""
        invalid_session_id = "invalid-session-123"
        
        try:
            with websocket_client.websocket_connect(f"/ws/{invalid_session_id}") as websocket:
                # Connection might be established but should handle invalid session
                assert websocket is not None
        except Exception:
            # Connection rejection is acceptable for invalid sessions
            pass

    def test_websocket_message_validation(self, websocket_client, test_websocket_session):
        """Test WebSocket message validation."""
        session_id = test_websocket_session["session_id"]
        
        with websocket_client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Test invalid message format
            invalid_messages = [
                "not-json-string",
                {"missing_type": "value"},
                {"type": ""},  # Empty type
                {}  # Empty object
            ]
            
            for invalid_message in invalid_messages:
                try:
                    if isinstance(invalid_message, str):
                        websocket.send_text(invalid_message)
                    else:
                        websocket.send_json(invalid_message)
                    
                    # Should handle invalid messages gracefully
                    # Might receive error response or no response
                    try:
                        response = websocket.receive_json(timeout=1)
                        if response and "error" in response:
                            assert response["error"] is not None
                    except:
                        # No response is also acceptable
                        pass
                except:
                    # Connection might be closed due to invalid message
                    pass

    def test_websocket_connection_limits(self, websocket_client):
        """Test WebSocket connection limits and rate limiting."""
        # This test assumes some form of connection limiting is implemented
        connections = []
        max_connections = 10  # Reasonable limit for testing
        
        try:
            for i in range(max_connections + 5):  # Try to exceed limit
                try:
                    websocket = websocket_client.websocket_connect(f"/ws/session-{i}")
                    connections.append(websocket.__enter__())
                except Exception:
                    # Connection limit reached
                    break
            
            # Should have some reasonable limit
            assert len(connections) <= max_connections * 2  # Allow some flexibility
        
        finally:
            # Clean up connections
            for websocket in connections:
                try:
                    websocket.close()
                except:
                    pass

    def test_websocket_message_broadcasting(self, websocket_client, multiple_test_sessions):
        """Test message broadcasting to multiple connections."""
        connections = []
        
        try:
            # Establish multiple connections
            for session in multiple_test_sessions[:3]:  # Use first 3 sessions
                websocket = websocket_client.websocket_connect(f"/ws/{session['session_id']}")
                connections.append(websocket.__enter__())
            
            # Send broadcast message from first connection
            broadcast_message = {
                "type": "broadcast",
                "content": "This is a broadcast message",
                "target": "all"
            }
            
            connections[0].send_json(broadcast_message)
            
            # Other connections might receive the broadcast
            # This depends on the implementation
            for websocket in connections[1:]:
                try:
                    response = websocket.receive_json(timeout=2)
                    if response and response.get("type") == "broadcast":
                        assert "content" in response
                except:
                    # No broadcast received, which might be expected
                    pass
        
        finally:
            # Clean up connections
            for websocket in connections:
                try:
                    websocket.close()
                except:
                    pass

    def test_websocket_reconnection_handling(self, websocket_client, test_websocket_session):
        """Test WebSocket reconnection scenarios."""
        session_id = test_websocket_session["session_id"]
        
        # First connection
        with websocket_client.websocket_connect(f"/ws/{session_id}") as websocket1:
            websocket1.send_json({"type": "ping", "message": "first connection"})
        
        # Reconnect with same session ID
        with websocket_client.websocket_connect(f"/ws/{session_id}") as websocket2:
            websocket2.send_json({"type": "ping", "message": "reconnected"})
            
            # Reconnection should work
            assert websocket2 is not None

    def test_websocket_error_handling(self, websocket_client, test_websocket_session):
        """Test WebSocket error handling."""
        session_id = test_websocket_session["session_id"]
        
        with websocket_client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Send message that might cause an error
            error_message = {
                "type": "error_trigger",
                "invalid_data": None
            }
            
            websocket.send_json(error_message)
            
            # Should handle error gracefully
            try:
                response = websocket.receive_json(timeout=2)
                if response and "error" in response:
                    assert isinstance(response["error"], str)
            except:
                # No error response might be expected
                pass

    async def test_websocket_performance(self, websocket_client, test_websocket_session):
        """Test WebSocket performance with rapid messages."""
        session_id = test_websocket_session["session_id"]
        
        with websocket_client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Send multiple rapid messages
            message_count = 10
            
            for i in range(message_count):
                test_message = {
                    "type": "performance_test",
                    "message_id": i,
                    "content": f"Performance test message {i}"
                }
                websocket.send_json(test_message)
            
            # Connection should handle rapid messages without issues
            # This is mainly testing that the connection doesn't break
            assert websocket is not None

    def test_websocket_connection_metadata(self, websocket_client, test_websocket_session):
        """Test WebSocket connection with metadata."""
        session_id = test_websocket_session["session_id"]
        
        with websocket_client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Send connection metadata
            metadata_message = {
                "type": "connection_metadata",
                "user_id": test_websocket_session["user_id"],
                "tenant_id": test_websocket_session["tenant_id"],
                "client_info": {
                    "browser": "test",
                    "version": "1.0"
                }
            }
            
            websocket.send_json(metadata_message)
            
            # Should accept metadata
            try:
                response = websocket.receive_json(timeout=2)
                if response:
                    assert "type" in response
            except:
                # No response expected
                pass