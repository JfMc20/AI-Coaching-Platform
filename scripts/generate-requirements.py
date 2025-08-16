#!/usr/bin/env python3
"""
Centralized Requirements Generator
Generates service-specific requirements.txt from pyproject.toml
"""

import tomllib
from pathlib import Path
from typing import Dict, List, Set

def load_pyproject() -> Dict:
    """Load and parse pyproject.toml"""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)

def format_dependency(name: str, spec: str | Dict) -> str:
    """Format a dependency specification into pip-compatible format"""
    if isinstance(spec, str):
        # Simple version spec like "^2.5.0"
        if spec.startswith("^"):
            version = spec[1:]  # Remove caret
            return f"{name}=={version}"
        elif spec.startswith(">="):
            return f"{name}{spec}"
        else:
            return f"{name}=={spec}"
    elif isinstance(spec, dict):
        # Complex spec like {extras = ["email"], version = "^2.5.0"}
        version = spec.get("version", "")
        extras = spec.get("extras", [])
        
        if version.startswith("^"):
            version = version[1:]  # Remove caret
            
        if extras:
            extras_str = "[" + ",".join(extras) + "]"
            return f"{name}{extras_str}=={version}"
        else:
            return f"{name}=={version}"
    else:
        return f"{name}"

def generate_service_requirements(service_name: str, base_deps: Set[str], extra_deps: Set[str] = None) -> List[str]:
    """Generate requirements for a specific service"""
    pyproject = load_pyproject()
    dependencies = pyproject["tool"]["poetry"]["dependencies"]
    
    # Skip python version constraint
    if "python" in dependencies:
        del dependencies["python"]
    
    requirements = []
    
    # Add base dependencies that all services need
    for dep_name in base_deps:
        if dep_name in dependencies:
            req = format_dependency(dep_name, dependencies[dep_name])
            requirements.append(req)
    
    # Add service-specific extra dependencies
    if extra_deps:
        for dep_name in extra_deps:
            if dep_name in dependencies:
                req = format_dependency(dep_name, dependencies[dep_name])
                requirements.append(req)
    
    return sorted(requirements)

def main():
    """Generate requirements for all services"""
    
    # Common dependencies for all services
    base_deps = {
        "fastapi", "uvicorn", "sqlalchemy", "asyncpg", "redis", "pydantic", 
        "pydantic-settings", "httpx", "aiohttp", "python-jose", "python-multipart", 
        "passlib", "argon2-cffi"
    }
    
    # Service-specific dependency mapping
    service_configs = {
        "auth-service": {
            "extra_deps": {"alembic", "psycopg2-binary"}
        },
        "creator-hub-service": {
            "extra_deps": {"aiofiles", "python-magic", "PyPDF2", "python-docx", "python-dotenv"}
        },
        "ai-engine-service": {
            "extra_deps": {
                "chromadb", "ollama", "numpy", "python-magic", "PyPDF2", "python-docx", 
                "markdown", "opentelemetry-api", "opentelemetry-sdk", "opentelemetry-exporter-jaeger",
                "opentelemetry-exporter-jaeger-thrift", "opentelemetry-instrumentation-httpx",
                "opentelemetry-instrumentation-redis", "opentelemetry-instrumentation-fastapi",
                "prometheus-client", "cryptography"
            }
        },
        "channel-service": {
            "extra_deps": {"websockets", "aiofiles"}
        }
    }
    
    # Generate requirements for each service
    for service_name, config in service_configs.items():
        extra_deps = config.get("extra_deps", set())
        requirements = generate_service_requirements(service_name, base_deps, extra_deps)
        
        # Create requirements content
        content = "# Generated from pyproject.toml - DO NOT EDIT MANUALLY\n"
        content += "# Use scripts/generate-requirements.py to update\n\n"
        content += "\n".join(requirements)
        
        # Write to service directory
        service_dir = Path(__file__).parent.parent / "services" / service_name
        if service_dir.exists():
            req_file = service_dir / "requirements.txt"
            with open(req_file, "w") as f:
                f.write(content)
            print(f"Generated {req_file}")

if __name__ == "__main__":
    main()