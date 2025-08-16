#!/usr/bin/env python3
"""
Database Migration Manager
Robust migration handling for development and production environments
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext
from alembic import command
from shared.config.settings import get_database_url_with_validation
from shared.config.env_constants import get_env_value, DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseMigrationManager:
    """
    Robust database migration manager for development and production
    """
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.alembic_cfg = Config(str(project_root / "alembic.ini"))
        self.alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))
        
        # Get database URL
        try:
            self.database_url = get_database_url_with_validation(async_url=True, required=True)
        except Exception as e:
            logger.error(f"Failed to get database URL: {e}")
            raise
            
        self.sync_database_url = self.database_url.replace("+asyncpg", "")
        self.engine = create_async_engine(self.database_url, echo=False)
        
    async def check_database_connection(self) -> bool:
        """Check if database is accessible"""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def get_database_state(self) -> Dict[str, any]:
        """Get current database state"""
        try:
            async with self.engine.connect() as conn:
                # Check if alembic_version table exists
                result = await conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'alembic_version'
                    )
                """))
                alembic_exists = result.scalar()
                
                current_revision = None
                if alembic_exists:
                    try:
                        result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                        current_revision = result.scalar()
                    except:
                        current_revision = None
                
                # Get list of tables
                result = await conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result.fetchall()]
                
                return {
                    "alembic_initialized": alembic_exists,
                    "current_revision": current_revision,
                    "tables": tables,
                    "table_count": len(tables)
                }
                
        except Exception as e:
            logger.error(f"Failed to get database state: {e}")
            return {
                "alembic_initialized": False,
                "current_revision": None,
                "tables": [],
                "table_count": 0
            }
    
    def get_migration_history(self) -> List[str]:
        """Get list of available migrations"""
        try:
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            revisions = []
            for revision in script_dir.walk_revisions():
                revisions.append(f"{revision.revision}: {revision.doc}")
            return revisions
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []
    
    async def initialize_alembic(self) -> bool:
        """Initialize alembic for existing database"""
        try:
            state = await self.get_database_state()
            
            if state["alembic_initialized"]:
                logger.info("Alembic already initialized")
                return True
            
            # Stamp current revision based on existing tables
            if state["tables"]:
                if "documents" in state["tables"]:
                    # We have Creator Hub tables, stamp as 003
                    command.stamp(self.alembic_cfg, "003")
                    logger.info("✅ Stamped database as revision 003")
                elif "creators" in state["tables"]:
                    # We have auth tables, stamp as 001
                    command.stamp(self.alembic_cfg, "001")
                    logger.info("✅ Stamped database as revision 001")
                else:
                    # Empty database, stamp as head
                    command.stamp(self.alembic_cfg, "head")
                    logger.info("✅ Stamped database as head")
            else:
                # Empty database
                command.stamp(self.alembic_cfg, "head")
                logger.info("✅ Initialized empty database")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize alembic: {e}")
            return False
    
    async def run_migrations(self, target_revision: str = "head") -> bool:
        """Run migrations to target revision"""
        try:
            # Ensure alembic is initialized
            await self.initialize_alembic()
            
            # Set database URL in config
            self.alembic_cfg.set_main_option("sqlalchemy.url", self.sync_database_url)
            
            # Run migration
            logger.info(f"Running migrations to {target_revision}...")
            command.upgrade(self.alembic_cfg, target_revision)
            logger.info("✅ Migrations completed successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    async def create_migration(self, message: str, autogenerate: bool = True) -> bool:
        """Create a new migration"""
        try:
            self.alembic_cfg.set_main_option("sqlalchemy.url", self.sync_database_url)
            
            if autogenerate:
                command.revision(self.alembic_cfg, message=message, autogenerate=True)
            else:
                command.revision(self.alembic_cfg, message=message)
            
            logger.info(f"✅ Created migration: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            return False
    
    async def rollback_migration(self, target_revision: str) -> bool:
        """Rollback to specific revision"""
        if self.environment == "production":
            logger.error("❌ Rollback not allowed in production environment")
            return False
        
        try:
            self.alembic_cfg.set_main_option("sqlalchemy.url", self.sync_database_url)
            command.downgrade(self.alembic_cfg, target_revision)
            logger.info(f"✅ Rolled back to revision {target_revision}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    async def validate_migration_safety(self) -> Dict[str, any]:
        """Validate that migrations are safe to run"""
        issues = []
        warnings = []
        
        # Check database connection
        if not await self.check_database_connection():
            issues.append("Cannot connect to database")
        
        # Check for pending migrations
        try:
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            state = await self.get_database_state()
            current = state.get("current_revision")
            head = script_dir.get_current_head()
            
            if current != head:
                warnings.append(f"Pending migrations: {current} -> {head}")
        except Exception as e:
            issues.append(f"Cannot check migration status: {e}")
        
        # Production specific checks
        if self.environment == "production":
            warnings.append("Production environment - extra caution required")
        
        return {
            "safe": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
    
    async def backup_database(self) -> Optional[str]:
        """Create database backup (development only)"""
        if self.environment == "production":
            logger.warning("Database backup in production should use dedicated backup tools")
            return None
        
        try:
            import subprocess
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"backup_{timestamp}.sql"
            
            # Extract connection details
            db_url = self.sync_database_url.replace("postgresql://", "")
            parts = db_url.split("@")
            auth_part = parts[0]
            host_part = parts[1].split("/")
            
            user_pass = auth_part.split(":")
            username = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ""
            
            host_port = host_part[0].split(":")
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else "5432"
            database = host_part[1]
            
            # Run pg_dump
            env = os.environ.copy()
            env["PGPASSWORD"] = password
            
            cmd = [
                "pg_dump",
                "-h", host,
                "-p", port,
                "-U", username,
                "-d", database,
                "-f", backup_file,
                "--verbose"
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Database backup created: {backup_file}")
                return backup_file
            else:
                logger.error(f"Backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    async def close(self):
        """Close database connections"""
        await self.engine.dispose()


async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Migration Manager")
    parser.add_argument("--env", default="development", choices=["development", "production"],
                       help="Environment (development/production)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    subparsers.add_parser("status", help="Show database and migration status")
    
    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Run migrations")
    migrate_parser.add_argument("--target", default="head", help="Target revision")
    
    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create new migration")
    create_parser.add_argument("message", help="Migration message")
    create_parser.add_argument("--no-autogenerate", action="store_true",
                              help="Don't use autogenerate")
    
    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback migration")
    rollback_parser.add_argument("revision", help="Target revision")
    
    # Backup command
    subparsers.add_parser("backup", help="Create database backup")
    
    # Validate command
    subparsers.add_parser("validate", help="Validate migration safety")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize manager
    manager = DatabaseMigrationManager(environment=args.env)
    
    try:
        if args.command == "status":
            state = await manager.get_database_state()
            history = manager.get_migration_history()
            
            print(f"\n📊 Database Status ({args.env}):")
            print(f"  Connection: {'✅ OK' if await manager.check_database_connection() else '❌ Failed'}")
            print(f"  Alembic initialized: {'✅ Yes' if state['alembic_initialized'] else '❌ No'}")
            print(f"  Current revision: {state['current_revision'] or 'None'}")
            print(f"  Tables: {state['table_count']} ({', '.join(state['tables'][:5])}{'...' if len(state['tables']) > 5 else ''})")
            
            print(f"\n📋 Migration History:")
            for revision in history[:5]:
                print(f"  {revision}")
            
        elif args.command == "migrate":
            validation = await manager.validate_migration_safety()
            
            if not validation["safe"]:
                print(f"❌ Migration validation failed:")
                for issue in validation["issues"]:
                    print(f"  - {issue}")
                return
            
            if validation["warnings"]:
                print(f"⚠️  Warnings:")
                for warning in validation["warnings"]:
                    print(f"  - {warning}")
                
                if args.env == "production":
                    confirm = input("Continue with production migration? (yes/no): ")
                    if confirm.lower() != "yes":
                        print("Migration cancelled")
                        return
            
            success = await manager.run_migrations(args.target)
            if success:
                print("✅ Migration completed successfully")
            else:
                print("❌ Migration failed")
        
        elif args.command == "create":
            success = await manager.create_migration(
                args.message, 
                autogenerate=not args.no_autogenerate
            )
            if success:
                print(f"✅ Migration created: {args.message}")
            else:
                print("❌ Failed to create migration")
        
        elif args.command == "rollback":
            success = await manager.rollback_migration(args.revision)
            if success:
                print(f"✅ Rolled back to: {args.revision}")
            else:
                print("❌ Rollback failed")
        
        elif args.command == "backup":
            backup_file = await manager.backup_database()
            if backup_file:
                print(f"✅ Backup created: {backup_file}")
            else:
                print("❌ Backup failed")
        
        elif args.command == "validate":
            validation = await manager.validate_migration_safety()
            
            if validation["safe"]:
                print("✅ Migration validation passed")
            else:
                print("❌ Migration validation failed:")
                for issue in validation["issues"]:
                    print(f"  - {issue}")
            
            if validation["warnings"]:
                print("⚠️  Warnings:")
                for warning in validation["warnings"]:
                    print(f"  - {warning}")
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"❌ Command failed: {e}")
    
    finally:
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())