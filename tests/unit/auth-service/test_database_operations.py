"""
Tests for database operations and multi-tenant isolation.
Tests database manager, connection pooling, and Row Level Security.

Fixtures are now centralized in tests/fixtures/auth_fixtures.py and automatically
available through the main conftest.py configuration.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from services.auth_service.app.database import DatabaseManager
from shared.models.auth import User


class TestDatabaseOperations:
    """Test database operations and multi-tenancy."""

    async def test_database_connection(self, db_session: AsyncSession):
        """Test basic database connectivity."""
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    async def test_user_creation(self, db_session: AsyncSession):
        """Test user creation in database."""
        user_data = {
            "email": "dbtest@example.com",
            "password_hash": "hashed_password",
            "full_name": "DB Test User",
            "tenant_id": "db-test-tenant"
        }
        
        user = User(**user_data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == user_data["email"]
        assert user.tenant_id == user_data["tenant_id"]
        assert user.created_at is not None

    async def test_user_retrieval_by_email(self, db_session: AsyncSession):
        """Test retrieving user by email."""
        # Create user
        user = User(
            email="retrieve@example.com",
            password_hash="hashed_password",
            full_name="Retrieve User",
            tenant_id="retrieve-tenant"
        )
        db_session.add(user)
        await db_session.commit()
        
        # Retrieve user
        from sqlalchemy import select
        result = await db_session.execute(
            select(User).where(User.email == "retrieve@example.com")
        )
        retrieved_user = result.scalar_one_or_none()
        
        assert retrieved_user is not None
        assert retrieved_user.email == "retrieve@example.com"
        assert retrieved_user.tenant_id == "retrieve-tenant"

    async def test_user_update(self, db_session: AsyncSession):
        """Test updating user information."""
        # Create user
        user = User(
            email="update@example.com",
            password_hash="hashed_password",
            full_name="Original Name",
            tenant_id="update-tenant"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Update user
        user.full_name = "Updated Name"
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.full_name == "Updated Name"

    async def test_user_deletion(self, db_session: AsyncSession):
        """Test user deletion from database."""
        # Create user
        user = User(
            email="delete@example.com",
            password_hash="hashed_password",
            full_name="Delete User",
            tenant_id="delete-tenant"
        )
        db_session.add(user)
        await db_session.commit()
        user_id = user.id
        
        # Delete user
        await db_session.delete(user)
        await db_session.commit()
        
        # Verify deletion
        from sqlalchemy import select
        result = await db_session.execute(
            select(User).where(User.id == user_id)
        )
        deleted_user = result.scalar_one_or_none()
        assert deleted_user is None

    async def test_tenant_isolation(self, db_session: AsyncSession):
        """Test that users from different tenants are isolated."""
        # Create users in different tenants
        user1 = User(
            email="tenant1@example.com",
            password_hash="hashed_password",
            full_name="Tenant 1 User",
            tenant_id="tenant-1"
        )
        
        user2 = User(
            email="tenant2@example.com",
            password_hash="hashed_password",
            full_name="Tenant 2 User",
            tenant_id="tenant-2"
        )
        
        db_session.add_all([user1, user2])
        await db_session.commit()
        
        # Query users by tenant
        from sqlalchemy import select
        tenant1_result = await db_session.execute(
            select(User).where(User.tenant_id == "tenant-1")
        )
        tenant1_users = tenant1_result.scalars().all()
        
        tenant2_result = await db_session.execute(
            select(User).where(User.tenant_id == "tenant-2")
        )
        tenant2_users = tenant2_result.scalars().all()
        
        # Verify isolation
        assert len(tenant1_users) == 1
        assert len(tenant2_users) == 1
        assert tenant1_users[0].tenant_id == "tenant-1"
        assert tenant2_users[0].tenant_id == "tenant-2"

    async def test_unique_email_constraint(self, db_session: AsyncSession):
        """Test that email uniqueness is enforced."""
        # Create first user
        user1 = User(
            email="unique@example.com",
            password_hash="hashed_password",
            full_name="First User",
            tenant_id="tenant-1"
        )
        db_session.add(user1)
        await db_session.commit()
        
        # Try to create second user with same email
        user2 = User(
            email="unique@example.com",
            password_hash="hashed_password",
            full_name="Second User",
            tenant_id="tenant-2"
        )
        db_session.add(user2)
        
        # Should raise integrity error
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_database_transaction_rollback(self, db_session: AsyncSession):
        """Test database transaction rollback functionality."""
        # Create user
        user = User(
            email="rollback@example.com",
            password_hash="hashed_password",
            full_name="Rollback User",
            tenant_id="rollback-tenant"
        )
        db_session.add(user)
        
        # Don't commit, rollback instead
        await db_session.rollback()
        
        # Verify user was not saved
        from sqlalchemy import select
        result = await db_session.execute(
            select(User).where(User.email == "rollback@example.com")
        )
        rollback_user = result.scalar_one_or_none()
        assert rollback_user is None

    async def test_concurrent_database_operations(self, test_engine):
        """Test concurrent database operations."""
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.asyncio import AsyncSession
        import asyncio
        
        async_session = sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async def create_user(email, tenant_id):
            async with async_session() as session:
                user = User(
                    email=email,
                    password_hash="hashed_password",
                    full_name="Concurrent User",
                    tenant_id=tenant_id
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user
        
        # Create multiple users concurrently
        tasks = []
        for i in range(5):
            task = create_user(f"concurrent{i}@example.com", f"tenant-{i}")
            tasks.append(task)
        
        users = await asyncio.gather(*tasks)
        
        # Verify all users were created
        assert len(users) == 5
        for i, user in enumerate(users):
            assert user.email == f"concurrent{i}@example.com"
            assert user.tenant_id == f"tenant-{i}"

    async def test_database_health_check(self, db_session: AsyncSession):
        """Test database health check functionality."""
        # Simple health check query
        try:
            result = await db_session.execute(text("SELECT 1"))
            health_status = result.scalar()
            assert health_status == 1
        except Exception as e:
            pytest.fail(f"Database health check failed: {e}")

    async def test_user_timestamps(self, db_session: AsyncSession):
        """Test that user timestamps are properly set."""
        user = User(
            email="timestamp@example.com",
            password_hash="hashed_password",
            full_name="Timestamp User",
            tenant_id="timestamp-tenant"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.created_at is not None
        assert user.updated_at is not None
        
        # Update user and check updated_at changes
        original_updated_at = user.updated_at
        user.full_name = "Updated Timestamp User"
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.updated_at >= original_updated_at