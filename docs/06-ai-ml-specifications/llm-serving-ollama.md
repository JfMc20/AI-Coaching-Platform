# LLM Serving with Ollama Specification

## Overview

Ollama serves as the primary LLM inference engine, providing local model serving capabilities for cost-effective, privacy-preserving, and high-performance language model operations. This specification covers model selection, deployment, optimization, and scaling strategies.

## Ollama Architecture and Setup

### Installation and Configuration
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull recommended models
ollama pull llama3:8b
ollama pull llama3:70b
ollama pull mistral:7b
ollama pull phi3:mini
ollama pull nomic-embed-text
```

### Model Configuration
```python
import ollama
from typing import Dict, List, Optional
import asyncio
import json
from dataclasses import dataclass

@dataclass
class ModelConfig:
    name: str
    context_length: int
    temperature: float
    top_p: float
    top_k: int
    repeat_penalty: float
    gpu_layers: int
    memory_limit: str

class OllamaModelManager:
    def __init__(self):
        self.client = ollama.Client()
        self.available_models = {}
        self.model_configs = self._initialize_model_configs()
        self.current_model = None
    
    def _initialize_model_configs(self) -> Dict[str, ModelConfig]:
        """Initialize configurations for different models"""
        return {
            "llama3:8b": ModelConfig(
                name="llama3:8b",
                context_length=8192,
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1,
                gpu_layers=35,
                memory_limit="8GB"
            ),
            "llama3:70b": ModelConfig(
                name="llama3:70b", 
                context_length=8192,
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1,
                gpu_layers=80,
                memory_limit="48GB"
            ),
            "mistral:7b": ModelConfig(
                name="mistral:7b",
                context_length=4096,
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1,
                gpu_layers=32,
                memory_limit="6GB"
            ),
            "phi3:mini": ModelConfig(
                name="phi3:mini",
                context_length=2048,
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1,
                gpu_layers=20,
                memory_limit="3GB"
            )
        }
    
    async def initialize_models(self):
        """Initialize and validate available models"""
        try:
            models = self.client.list()
            for model in models['models']:
                model_name = model['name']
                if model_name in self.model_configs:
                    self.available_models[model_name] = {
                        'config': self.model_configs[model_name],
                        'size': model['size'],
                        'modified_at': model['modified_at'],
                        'status': 'available'
                    }
            
            # Set default model
            if 'llama3:8b' in self.available_models:
                self.current_model = 'llama3:8b'
            elif self.available_models:
                self.current_model = list(self.available_models.keys())[0]
            
            return self.available_models
        except Exception as e:
            raise Exception(f"Failed to initialize models: {str(e)}")

### Model Selection Strategy
```python
class ModelSelector:
    def __init__(self, model_manager: OllamaModelManager):
        self.model_manager = model_manager
        self.performance_tracker = ModelPerformanceTracker()
        self.resource_monitor = ResourceMonitor()
    
    async def select_optimal_model(
        self,
        request_context: Dict,
        performance_requirements: Dict = None
    ) -> str:
        """Select the optimal model based on request context and requirements"""
        
        # Default requirements
        if not performance_requirements:
            performance_requirements = {
                'max_response_time': 5.0,  # seconds
                'min_quality_score': 0.8,
                'max_memory_usage': 0.8,   # 80% of available memory
                'context_length_needed': 2048
            }
        
        # Get available models
        available_models = self.model_manager.available_models
        
        # Score each model
        model_scores = {}
        for model_name, model_info in available_models.items():
            score = await self._score_model(
                model_name, model_info, request_context, performance_requirements
            )
            model_scores[model_name] = score
        
        # Select best model
        if not model_scores:
            raise Exception("No suitable models available")
        
        best_model = max(model_scores.items(), key=lambda x: x[1])
        return best_model[0]
    
    async def _score_model(
        self,
        model_name: str,
        model_info: Dict,
        request_context: Dict,
        requirements: Dict
    ) -> float:
        """Score a model based on suitability for the request"""
        
        config = model_info['config']
        score = 0.0
        
        # Context length score
        needed_context = requirements.get('context_length_needed', 2048)
        if config.context_length >= needed_context:
            score += 0.3
        else:
            score -= 0.5  # Penalty for insufficient context
        
        # Performance score based on historical data
        performance_data = await self.performance_tracker.get_performance(model_name)
        if performance_data:
            avg_response_time = performance_data.get('avg_response_time', 10.0)
            if avg_response_time <= requirements.get('max_response_time', 5.0):
                score += 0.3
            
            quality_score = performance_data.get('avg_quality_score', 0.5)
            if quality_score >= requirements.get('min_quality_score', 0.8):
                score += 0.2
        
        # Resource usage score
        current_memory_usage = await self.resource_monitor.get_memory_usage()
        model_memory_req = self._estimate_memory_requirement(config)
        
        if (current_memory_usage + model_memory_req) <= requirements.get('max_memory_usage', 0.8):
            score += 0.2
        else:
            score -= 0.3
        
        return max(0.0, score)  # Ensure non-negative score

### Inference Engine
```python
class OllamaInferenceEngine:
    def __init__(self, model_manager: OllamaModelManager):
        self.model_manager = model_manager
        self.model_selector = ModelSelector(model_manager)
        self.response_cache = ResponseCache()
        self.batch_processor = BatchProcessor()
        self.performance_monitor = PerformanceMonitor()
    
    async def generate_response(
        self,
        prompt: str,
        model_name: str = None,
        generation_config: Dict = None,
        use_cache: bool = True
    ) -> Dict:
        """Generate response using Ollama"""
        
        # Check cache first
        if use_cache:
            cached_response = await self.response_cache.get(prompt, model_name)
            if cached_response:
                return cached_response
        
        # Select model if not specified
        if not model_name:
            model_name = await self.model_selector.select_optimal_model({
                'prompt_length': len(prompt),
                'complexity': self._estimate_complexity(prompt)
            })
        
        # Prepare generation config
        config = self._prepare_generation_config(model_name, generation_config)
        
        # Generate response
        start_time = time.time()
        try:
            response = await self._generate_with_ollama(prompt, model_name, config)
            generation_time = time.time() - start_time
            
            # Process response
            processed_response = {
                'text': response['response'],
                'model_used': model_name,
                'generation_time': generation_time,
                'tokens_generated': response.get('eval_count', 0),
                'tokens_per_second': response.get('eval_count', 0) / generation_time if generation_time > 0 else 0,
                'context_used': response.get('prompt_eval_count', 0),
                'metadata': {
                    'total_duration': response.get('total_duration', 0),
                    'load_duration': response.get('load_duration', 0),
                    'prompt_eval_duration': response.get('prompt_eval_duration', 0),
                    'eval_duration': response.get('eval_duration', 0)
                }
            }
            
            # Cache response
            if use_cache:
                await self.response_cache.set(prompt, model_name, processed_response)
            
            # Record performance metrics
            await self.performance_monitor.record_generation(
                model_name, generation_time, len(prompt), response.get('eval_count', 0)
            )
            
            return processed_response
            
        except Exception as e:
            await self.performance_monitor.record_error(model_name, str(e))
            raise Exception(f"Generation failed with {model_name}: {str(e)}")
    
    async def _generate_with_ollama(
        self,
        prompt: str,
        model_name: str,
        config: Dict
    ) -> Dict:
        """Generate response using Ollama client"""
        
        try:
            response = self.model_manager.client.generate(
                model=model_name,
                prompt=prompt,
                options={
                    'temperature': config.get('temperature', 0.7),
                    'top_p': config.get('top_p', 0.9),
                    'top_k': config.get('top_k', 40),
                    'repeat_penalty': config.get('repeat_penalty', 1.1),
                    'num_ctx': config.get('context_length', 4096)
                },
                stream=False
            )
            return response
        except Exception as e:
            raise Exception(f"Ollama generation error: {str(e)}")

### Batch Processing
```python
class BatchProcessor:
    def __init__(self, inference_engine: OllamaInferenceEngine):
        self.inference_engine = inference_engine
        self.max_batch_size = 10
        self.batch_timeout = 30  # seconds
    
    async def process_batch(
        self,
        requests: List[Dict],
        model_name: str = None
    ) -> List[Dict]:
        """Process multiple requests in batch"""
        
        if len(requests) > self.max_batch_size:
            # Split into smaller batches
            batches = [
                requests[i:i + self.max_batch_size] 
                for i in range(0, len(requests), self.max_batch_size)
            ]
            
            all_results = []
            for batch in batches:
                batch_results = await self._process_single_batch(batch, model_name)
                all_results.extend(batch_results)
            
            return all_results
        else:
            return await self._process_single_batch(requests, model_name)
    
    async def _process_single_batch(
        self,
        requests: List[Dict],
        model_name: str = None
    ) -> List[Dict]:
        """Process a single batch of requests"""
        
        # Create tasks for concurrent processing
        tasks = []
        for request in requests:
            task = self.inference_engine.generate_response(
                prompt=request['prompt'],
                model_name=model_name,
                generation_config=request.get('config'),
                use_cache=request.get('use_cache', True)
            )
            tasks.append(task)
        
        # Execute tasks concurrently with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.batch_timeout
            )
            
            # Process results and handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        'request_id': requests[i].get('id'),
                        'error': str(result),
                        'success': False
                    })
                else:
                    processed_results.append({
                        'request_id': requests[i].get('id'),
                        'response': result,
                        'success': True
                    })
            
            return processed_results
            
        except asyncio.TimeoutError:
            raise Exception(f"Batch processing timeout after {self.batch_timeout} seconds")

### Performance Optimization
```python
class PerformanceOptimizer:
    def __init__(self, model_manager: OllamaModelManager):
        self.model_manager = model_manager
        self.resource_monitor = ResourceMonitor()
        self.load_balancer = LoadBalancer()
    
    async def optimize_model_loading(self):
        """Optimize model loading and memory usage"""
        
        # Monitor resource usage
        resource_stats = await self.resource_monitor.get_current_stats()
        
        # Determine optimal model configuration
        if resource_stats['memory_usage'] > 0.8:
            # High memory usage - consider lighter models
            await self._switch_to_lighter_model()
        elif resource_stats['gpu_utilization'] < 0.3:
            # Low GPU usage - can handle heavier models
            await self._consider_heavier_model()
        
        # Optimize GPU layers based on available VRAM
        await self._optimize_gpu_layers()
    
    async def _optimize_gpu_layers(self):
        """Optimize GPU layer allocation based on available VRAM"""
        
        available_vram = await self.resource_monitor.get_available_vram()
        
        for model_name, model_info in self.model_manager.available_models.items():
            config = model_info['config']
            
            # Calculate optimal GPU layers
            estimated_vram_per_layer = self._estimate_vram_per_layer(model_name)
            optimal_layers = min(
                config.gpu_layers,
                int(available_vram * 0.8 / estimated_vram_per_layer)
            )
            
            # Update configuration
            config.gpu_layers = optimal_layers
    
    async def implement_model_quantization(self, model_name: str, quantization_level: str):
        """Implement model quantization for better performance"""
        
        quantization_configs = {
            'q4_0': {'bits': 4, 'memory_reduction': 0.5, 'quality_loss': 0.05},
            'q5_0': {'bits': 5, 'memory_reduction': 0.4, 'quality_loss': 0.03},
            'q8_0': {'bits': 8, 'memory_reduction': 0.2, 'quality_loss': 0.01}
        }
        
        if quantization_level not in quantization_configs:
            raise ValueError(f"Unsupported quantization level: {quantization_level}")
        
        # Apply quantization (this would typically involve model conversion)
        quantized_model_name = f"{model_name}-{quantization_level}"
        
        # Update model registry
        self.model_manager.available_models[quantized_model_name] = {
            'config': self._create_quantized_config(
                self.model_manager.model_configs[model_name],
                quantization_configs[quantization_level]
            ),
            'quantization': quantization_level,
            'base_model': model_name
        }
        
        return quantized_model_name

### Monitoring and Health Checks
```python
class OllamaHealthMonitor:
    def __init__(self, model_manager: OllamaModelManager):
        self.model_manager = model_manager
        self.health_checks = []
        self.alert_manager = AlertManager()
    
    async def perform_health_check(self) -> Dict:
        """Perform comprehensive health check"""
        
        health_status = {
            'overall_status': 'healthy',
            'timestamp': datetime.utcnow(),
            'checks': {}
        }
        
        # Check Ollama service
        service_status = await self._check_ollama_service()
        health_status['checks']['ollama_service'] = service_status
        
        # Check model availability
        model_status = await self._check_model_availability()
        health_status['checks']['model_availability'] = model_status
        
        # Check resource usage
        resource_status = await self._check_resource_usage()
        health_status['checks']['resource_usage'] = resource_status
        
        # Check response times
        performance_status = await self._check_performance()
        health_status['checks']['performance'] = performance_status
        
        # Determine overall status
        if any(check['status'] == 'critical' for check in health_status['checks'].values()):
            health_status['overall_status'] = 'critical'
        elif any(check['status'] == 'warning' for check in health_status['checks'].values()):
            health_status['overall_status'] = 'warning'
        
        # Send alerts if necessary
        if health_status['overall_status'] in ['critical', 'warning']:
            await self.alert_manager.send_alert(health_status)
        
        return health_status
    
    async def _check_ollama_service(self) -> Dict:
        """Check if Ollama service is running and responsive"""
        
        try:
            # Test basic connectivity
            models = self.model_manager.client.list()
            
            return {
                'status': 'healthy',
                'message': 'Ollama service is responsive',
                'models_available': len(models.get('models', []))
            }
        except Exception as e:
            return {
                'status': 'critical',
                'message': f'Ollama service is not responsive: {str(e)}',
                'models_available': 0
            }
    
    async def _check_performance(self) -> Dict:
        """Check model performance metrics"""
        
        try:
            # Test generation with a simple prompt
            test_prompt = "Hello, how are you?"
            start_time = time.time()
            
            response = self.model_manager.client.generate(
                model=self.model_manager.current_model,
                prompt=test_prompt
            )
            
            response_time = time.time() - start_time
            
            status = 'healthy'
            if response_time > 10:
                status = 'warning'
            elif response_time > 30:
                status = 'critical'
            
            return {
                'status': status,
                'response_time': response_time,
                'model_used': self.model_manager.current_model,
                'tokens_generated': response.get('eval_count', 0)
            }
        except Exception as e:
            return {
                'status': 'critical',
                'message': f'Performance check failed: {str(e)}',
                'response_time': None
            }

### Scaling and Load Balancing
```python
class OllamaScaler:
    def __init__(self):
        self.instances = []
        self.load_balancer = LoadBalancer()
        self.auto_scaler = AutoScaler()
    
    async def scale_horizontally(self, target_instances: int):
        """Scale Ollama instances horizontally"""
        
        current_instances = len(self.instances)
        
        if target_instances > current_instances:
            # Scale up
            for i in range(target_instances - current_instances):
                instance = await self._create_ollama_instance()
                self.instances.append(instance)
                await self.load_balancer.add_instance(instance)
        
        elif target_instances < current_instances:
            # Scale down
            instances_to_remove = current_instances - target_instances
            for i in range(instances_to_remove):
                instance = self.instances.pop()
                await self.load_balancer.remove_instance(instance)
                await self._terminate_ollama_instance(instance)
    
    async def auto_scale_based_on_load(self):
        """Automatically scale based on current load"""
        
        current_load = await self.load_balancer.get_current_load()
        
        scaling_decision = await self.auto_scaler.make_scaling_decision(
            current_load, len(self.instances)
        )
        
        if scaling_decision['action'] == 'scale_up':
            await self.scale_horizontally(len(self.instances) + scaling_decision['instances'])
        elif scaling_decision['action'] == 'scale_down':
            await self.scale_horizontally(len(self.instances) - scaling_decision['instances'])
        
        return scaling_decision
```

This comprehensive Ollama serving specification provides a robust foundation for local LLM deployment with optimal performance, scalability, and reliability while maintaining cost-effectiveness and data privacy.