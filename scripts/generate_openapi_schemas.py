#!/usr/bin/env python3
"""
Generate OpenAPI schemas for all services and save to docs/api/
This script is used by CI to detect API changes without documentation updates.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any

import aiohttp
import yaml


class OpenAPISchemaGenerator:
    """Generate and save OpenAPI schemas for all services"""
    
    def __init__(self):
        self.services = {
            'auth-service': 'http://localhost:8001',
            'creator-hub-service': 'http://localhost:8002', 
            'ai-engine-service': 'http://localhost:8003',
            'channel-service': 'http://localhost:8004'
        }
        self.output_dir = Path('docs/api')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def fetch_schema(self, service_name: str, base_url: str) -> Dict[str, Any]:
        """Fetch OpenAPI schema from service"""
        schema_url = f"{base_url}/openapi.json"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(schema_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        schema = await response.json()
                        print(f"✅ Fetched schema for {service_name}")
                        return schema
                    else:
                        print(f"❌ Failed to fetch schema for {service_name}: HTTP {response.status}")
                        return {}
        except Exception as e:
            print(f"❌ Error fetching schema for {service_name}: {e}")
            return {}
    
    def save_schema(self, service_name: str, schema: Dict[str, Any]) -> None:
        """Save schema to both JSON and YAML formats"""
        if not schema:
            return
        
        # Save as JSON
        json_path = self.output_dir / f"{service_name}.openapi.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, sort_keys=True)
        
        # Save as YAML for better readability
        yaml_path = self.output_dir / f"{service_name}.openapi.yaml"
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(schema, f, default_flow_style=False, sort_keys=True)
        
        print(f"📄 Saved schema for {service_name}")
    
    def generate_api_index(self) -> None:
        """Generate API documentation index"""
        index_content = """# API Documentation

This directory contains auto-generated OpenAPI schemas for all services.

## Services

"""
        
        for service_name in self.services.keys():
            json_file = f"{service_name}.openapi.json"
            yaml_file = f"{service_name}.openapi.yaml"
            
            if (self.output_dir / json_file).exists():
                index_content += f"""
### {service_name.title().replace('-', ' ')}
- **JSON Schema**: [{json_file}](./{json_file})
- **YAML Schema**: [{yaml_file}](./{yaml_file})
- **Swagger UI**: Available at service `/docs` endpoint
"""
        
        index_content += """
## Usage

These schemas are automatically generated and used for:
- API documentation
- Client SDK generation  
- Contract testing
- Breaking change detection

⚠️ **Do not edit these files manually** - they are auto-generated from service code.
"""
        
        index_path = self.output_dir / "README.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print("📚 Generated API documentation index")
    
    async def generate_all_schemas(self) -> None:
        """Generate schemas for all services"""
        print("🚀 Generating OpenAPI schemas for all services...")
        
        tasks = []
        for service_name, base_url in self.services.items():
            task = self.fetch_schema(service_name, base_url)
            tasks.append((service_name, task))
        
        # Fetch all schemas concurrently
        for service_name, task in tasks:
            schema = await task
            self.save_schema(service_name, schema)
        
        self.generate_api_index()
        print("✅ Schema generation completed")


async def main():
    """Main entry point"""
    generator = OpenAPISchemaGenerator()
    await generator.generate_all_schemas()


if __name__ == "__main__":
    asyncio.run(main())