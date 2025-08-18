"""
Visual Program Builder - Condition Evaluator
Advanced condition evaluation engine for complex program flow logic
"""

import re
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .program_engine import ExecutionContext
from .step_models import ConditionalConfig, StepCondition
from .program_models import ProgramDefinition

logger = logging.getLogger(__name__)


# ==================== CONDITION EVALUATION CONTEXT ====================

@dataclass
class ConditionContext:
    """Context for condition evaluation"""
    execution_context: ExecutionContext
    program: ProgramDefinition
    step_results: Dict[str, Any]
    user_variables: Dict[str, Any]
    system_variables: Dict[str, Any]
    time_context: Dict[str, datetime]
    
    def get_variable(self, variable_name: str) -> Any:
        """Get variable value from any context"""
        # Priority: user_variables > execution_context.variables > system_variables
        if variable_name in self.user_variables:
            return self.user_variables[variable_name]
        elif variable_name in self.execution_context.variables:
            return self.execution_context.variables[variable_name]
        elif variable_name in self.system_variables:
            return self.system_variables[variable_name]
        else:
            return None
    
    def set_variable(self, variable_name: str, value: Any):
        """Set variable value"""
        self.execution_context.variables[variable_name] = value


class ConditionEvaluationResult:
    """Result of condition evaluation"""
    
    def __init__(
        self, 
        result: bool, 
        confidence: float = 1.0,
        explanation: str = "",
        variables_used: List[str] = None,
        execution_time_ms: float = 0.0,
        cached: bool = False
    ):
        self.result = result
        self.confidence = confidence
        self.explanation = explanation
        self.variables_used = variables_used or []
        self.execution_time_ms = execution_time_ms
        self.cached = cached
        self.evaluated_at = datetime.utcnow()


# ==================== CONDITION OPERATORS ====================

class ConditionOperator(ABC):
    """Abstract base class for condition operators"""
    
    @abstractmethod
    def evaluate(self, left: Any, right: Any, context: ConditionContext) -> bool:
        """Evaluate the operator"""
        pass
    
    @abstractmethod
    def get_operator_symbol(self) -> str:
        """Get operator symbol"""
        pass


class EqualsOperator(ConditionOperator):
    def evaluate(self, left: Any, right: Any, context: ConditionContext) -> bool:
        return left == right
    
    def get_operator_symbol(self) -> str:
        return "=="


class NotEqualsOperator(ConditionOperator):
    def evaluate(self, left: Any, right: Any, context: ConditionContext) -> bool:
        return left != right
    
    def get_operator_symbol(self) -> str:
        return "!="


class GreaterThanOperator(ConditionOperator):
    def evaluate(self, left: Any, right: Any, context: ConditionContext) -> bool:
        try:
            return float(left) > float(right)
        except (ValueError, TypeError):
            return False
    
    def get_operator_symbol(self) -> str:
        return ">"


class GreaterThanEqualOperator(ConditionOperator):
    def evaluate(self, left: Any, right: Any, context: ConditionContext) -> bool:
        try:
            return float(left) >= float(right)
        except (ValueError, TypeError):
            return False
    
    def get_operator_symbol(self) -> str:
        return ">="


class LessThanOperator(ConditionOperator):
    def evaluate(self, left: Any, right: Any, context: ConditionContext) -> bool:
        try:
            return float(left) < float(right)
        except (ValueError, TypeError):
            return False
    
    def get_operator_symbol(self) -> str:
        return "<"


class LessThanEqualOperator(ConditionOperator):
    def evaluate(self, left: Any, right: Any, context: ConditionContext) -> bool:
        try:
            return float(left) <= float(right)
        except (ValueError, TypeError):
            return False
    
    def get_operator_symbol(self) -> str:
        return "<="


class ContainsOperator(ConditionOperator):
    def evaluate(self, left: Any, right: Any, context: ConditionContext) -> bool:
        try:
            return str(right) in str(left)
        except (ValueError, TypeError):
            return False
    
    def get_operator_symbol(self) -> str:
        return "CONTAINS"


class InOperator(ConditionOperator):
    def evaluate(self, left: Any, right: Any, context: ConditionContext) -> bool:
        try:
            if isinstance(right, (list, tuple, set)):
                return left in right
            else:
                return str(left) in str(right)
        except (ValueError, TypeError):
            return False
    
    def get_operator_symbol(self) -> str:
        return "IN"


class MatchesOperator(ConditionOperator):
    def evaluate(self, left: Any, right: Any, context: ConditionContext) -> bool:
        try:
            pattern = str(right)
            text = str(left)
            return bool(re.search(pattern, text, re.IGNORECASE))
        except (ValueError, TypeError, re.error):
            return False
    
    def get_operator_symbol(self) -> str:
        return "MATCHES"


# ==================== BUILT-IN FUNCTIONS ====================

class BuiltinFunction(ABC):
    """Abstract base class for built-in functions"""
    
    @abstractmethod
    async def execute(self, args: List[Any], context: ConditionContext) -> Any:
        """Execute the function"""
        pass
    
    @abstractmethod
    def get_function_name(self) -> str:
        """Get function name"""
        pass
    
    @abstractmethod
    def get_arg_count(self) -> int:
        """Get expected argument count"""
        pass


class CountFunction(BuiltinFunction):
    async def execute(self, args: List[Any], context: ConditionContext) -> Any:
        if len(args) != 1:
            raise ValueError("COUNT function requires exactly 1 argument")
        
        collection = args[0]
        if isinstance(collection, (list, tuple, set)):
            return len(collection)
        elif isinstance(collection, str):
            return len(collection.split())
        else:
            return 0
    
    def get_function_name(self) -> str:
        return "COUNT"
    
    def get_arg_count(self) -> int:
        return 1


class SumFunction(BuiltinFunction):
    async def execute(self, args: List[Any], context: ConditionContext) -> Any:
        if len(args) != 1:
            raise ValueError("SUM function requires exactly 1 argument")
        
        collection = args[0]
        if isinstance(collection, (list, tuple)):
            try:
                return sum(float(x) for x in collection)
            except (ValueError, TypeError):
                return 0
        else:
            return 0
    
    def get_function_name(self) -> str:
        return "SUM"
    
    def get_arg_count(self) -> int:
        return 1


class AvgFunction(BuiltinFunction):
    async def execute(self, args: List[Any], context: ConditionContext) -> Any:
        if len(args) != 1:
            raise ValueError("AVG function requires exactly 1 argument")
        
        collection = args[0]
        if isinstance(collection, (list, tuple)) and collection:
            try:
                return sum(float(x) for x in collection) / len(collection)
            except (ValueError, TypeError):
                return 0
        else:
            return 0
    
    def get_function_name(self) -> str:
        return "AVG"
    
    def get_arg_count(self) -> int:
        return 1


class NowFunction(BuiltinFunction):
    async def execute(self, args: List[Any], context: ConditionContext) -> Any:
        if len(args) != 0:
            raise ValueError("NOW function requires no arguments")
        return datetime.utcnow()
    
    def get_function_name(self) -> str:
        return "NOW"
    
    def get_arg_count(self) -> int:
        return 0


class DaysAgoFunction(BuiltinFunction):
    async def execute(self, args: List[Any], context: ConditionContext) -> Any:
        if len(args) != 1:
            raise ValueError("DAYS_AGO function requires exactly 1 argument")
        
        try:
            days = int(args[0])
            return datetime.utcnow() - timedelta(days=days)
        except (ValueError, TypeError):
            return datetime.utcnow()
    
    def get_function_name(self) -> str:
        return "DAYS_AGO"
    
    def get_arg_count(self) -> int:
        return 1


class GetStepResultFunction(BuiltinFunction):
    async def execute(self, args: List[Any], context: ConditionContext) -> Any:
        if len(args) != 2:
            raise ValueError("GET_STEP_RESULT function requires exactly 2 arguments: step_id, field")
        
        step_id = str(args[0])
        field = str(args[1])
        
        if step_id in context.step_results:
            step_result = context.step_results[step_id]
            if isinstance(step_result, dict) and field in step_result:
                return step_result[field]
        
        return None
    
    def get_function_name(self) -> str:
        return "GET_STEP_RESULT"
    
    def get_arg_count(self) -> int:
        return 2


# ==================== CONDITION PARSER ====================

class ConditionParser:
    """Parser for condition expressions"""
    
    def __init__(self):
        self.operators = {
            "==": EqualsOperator(),
            "!=": NotEqualsOperator(),
            ">": GreaterThanOperator(),
            ">=": GreaterThanEqualOperator(),
            "<": LessThanOperator(),
            "<=": LessThanEqualOperator(),
            "CONTAINS": ContainsOperator(),
            "IN": InOperator(),
            "MATCHES": MatchesOperator()
        }
        
        self.functions = {
            "COUNT": CountFunction(),
            "SUM": SumFunction(),
            "AVG": AvgFunction(),
            "NOW": NowFunction(),
            "DAYS_AGO": DaysAgoFunction(),
            "GET_STEP_RESULT": GetStepResultFunction()
        }
    
    def parse_expression(self, expression: str) -> Dict[str, Any]:
        """Parse condition expression into components"""
        
        # Remove extra whitespace
        expression = re.sub(r'\s+', ' ', expression.strip())
        
        # Handle parentheses for complex expressions
        if '(' in expression and ')' in expression:
            return self._parse_complex_expression(expression)
        
        # Handle simple expressions
        return self._parse_simple_expression(expression)
    
    def _parse_simple_expression(self, expression: str) -> Dict[str, Any]:
        """Parse simple expression (no parentheses)"""
        
        # Handle logical operators (AND, OR)
        if ' AND ' in expression:
            parts = expression.split(' AND ')
            return {
                "type": "logical",
                "operator": "AND",
                "left": self._parse_simple_expression(parts[0].strip()),
                "right": self._parse_simple_expression(' AND '.join(parts[1:]).strip())
            }
        
        if ' OR ' in expression:
            parts = expression.split(' OR ')
            return {
                "type": "logical",
                "operator": "OR",
                "left": self._parse_simple_expression(parts[0].strip()),
                "right": self._parse_simple_expression(' OR '.join(parts[1:]).strip())
            }
        
        # Handle comparison operators
        for op_symbol in sorted(self.operators.keys(), key=len, reverse=True):
            if op_symbol in expression:
                parts = expression.split(op_symbol, 1)
                if len(parts) == 2:
                    return {
                        "type": "comparison",
                        "operator": op_symbol,
                        "left": self._parse_value(parts[0].strip()),
                        "right": self._parse_value(parts[1].strip())
                    }
        
        # Handle single value or function
        return self._parse_value(expression)
    
    def _parse_complex_expression(self, expression: str) -> Dict[str, Any]:
        """Parse complex expression with parentheses"""
        
        # Find matching parentheses
        paren_level = 0
        paren_start = -1
        
        for i, char in enumerate(expression):
            if char == '(':
                if paren_level == 0:
                    paren_start = i
                paren_level += 1
            elif char == ')':
                paren_level -= 1
                if paren_level == 0:
                    # Extract content within parentheses
                    inner_expr = expression[paren_start + 1:i]
                    # Replace parentheses group with placeholder
                    placeholder = f"__PAREN_{paren_start}__"
                    new_expression = expression[:paren_start] + placeholder + expression[i + 1:]
                    # Recursively parse
                    parsed_inner = self.parse_expression(inner_expr)
                    result = self.parse_expression(new_expression)
                    # Replace placeholder with parsed inner expression
                    self._replace_placeholder(result, placeholder, parsed_inner)
                    return result
        
        # No valid parentheses found, parse as simple
        return self._parse_simple_expression(expression)
    
    def _parse_value(self, value: str) -> Dict[str, Any]:
        """Parse individual value (variable, literal, or function)"""
        
        value = value.strip()
        
        # Handle function calls
        if '(' in value and value.endswith(')'):
            func_match = re.match(r'(\w+)\((.*)\)', value)
            if func_match:
                func_name = func_match.group(1)
                args_str = func_match.group(2)
                
                # Parse function arguments
                args = []
                if args_str.strip():
                    arg_parts = self._split_function_args(args_str)
                    for arg in arg_parts:
                        args.append(self._parse_value(arg.strip()))
                
                return {
                    "type": "function",
                    "function": func_name,
                    "args": args
                }
        
        # Handle string literals
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            return {
                "type": "literal",
                "value": value[1:-1],
                "data_type": "string"
            }
        
        # Handle numeric literals
        try:
            if '.' in value:
                return {
                    "type": "literal",
                    "value": float(value),
                    "data_type": "float"
                }
            else:
                return {
                    "type": "literal",
                    "value": int(value),
                    "data_type": "int"
                }
        except ValueError:
            pass
        
        # Handle boolean literals
        if value.lower() in ['true', 'false']:
            return {
                "type": "literal",
                "value": value.lower() == 'true',
                "data_type": "boolean"
            }
        
        # Handle list literals
        if value.startswith('[') and value.endswith(']'):
            list_content = value[1:-1].strip()
            if list_content:
                items = [item.strip() for item in list_content.split(',')]
                parsed_items = [self._parse_value(item) for item in items]
                return {
                    "type": "literal",
                    "value": [item["value"] for item in parsed_items],
                    "data_type": "list"
                }
            else:
                return {
                    "type": "literal",
                    "value": [],
                    "data_type": "list"
                }
        
        # Default to variable
        return {
            "type": "variable",
            "name": value
        }
    
    def _split_function_args(self, args_str: str) -> List[str]:
        """Split function arguments respecting nested parentheses and quotes"""
        
        args = []
        current_arg = ""
        paren_level = 0
        in_quotes = False
        quote_char = None
        
        for char in args_str:
            if char in ['"', "'"] and not in_quotes:
                in_quotes = True
                quote_char = char
                current_arg += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                current_arg += char
            elif char == '(' and not in_quotes:
                paren_level += 1
                current_arg += char
            elif char == ')' and not in_quotes:
                paren_level -= 1
                current_arg += char
            elif char == ',' and paren_level == 0 and not in_quotes:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char
        
        if current_arg.strip():
            args.append(current_arg.strip())
        
        return args
    
    def _replace_placeholder(self, parsed: Dict[str, Any], placeholder: str, replacement: Dict[str, Any]):
        """Replace placeholder in parsed structure with replacement"""
        
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                if isinstance(value, dict):
                    if value.get("type") == "variable" and value.get("name") == placeholder:
                        parsed[key] = replacement
                    else:
                        self._replace_placeholder(value, placeholder, replacement)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            self._replace_placeholder(item, placeholder, replacement)


# ==================== CORE CONDITION EVALUATOR ====================

class ConditionEvaluator:
    """Core condition evaluation engine"""
    
    def __init__(self):
        self.parser = ConditionParser()
        self.cache: Dict[str, ConditionEvaluationResult] = {}
        self.cache_max_size = 1000
        self.custom_functions: Dict[str, BuiltinFunction] = {}
        
        logger.info("Condition Evaluator initialized")
    
    def register_custom_function(self, function: BuiltinFunction):
        """Register custom function for condition evaluation"""
        self.custom_functions[function.get_function_name()] = function
        logger.info(f"Registered custom function: {function.get_function_name()}")
    
    async def evaluate_condition(
        self, 
        condition_config: ConditionalConfig, 
        context: ConditionContext
    ) -> ConditionEvaluationResult:
        """Evaluate a conditional configuration"""
        
        start_time = datetime.utcnow()
        
        try:
            # Check cache if enabled
            cache_key = self._get_cache_key(condition_config, context)
            if condition_config.cache_evaluation_result and cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if self._is_cache_valid(cached_result, condition_config):
                    cached_result.cached = True
                    return cached_result
            
            # Parse the condition expression
            parsed_expression = self.parser.parse_expression(condition_config.condition_expression)
            
            # Evaluate the parsed expression
            result = await self._evaluate_parsed_expression(parsed_expression, context)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Create evaluation result
            evaluation_result = ConditionEvaluationResult(
                result=bool(result),
                confidence=1.0,  # Simple conditions have full confidence
                explanation=f"Evaluated: {condition_config.condition_expression} = {result}",
                variables_used=self._extract_variables_used(parsed_expression),
                execution_time_ms=execution_time,
                cached=False
            )
            
            # Cache result if enabled
            if condition_config.cache_evaluation_result:
                self._cache_result(cache_key, evaluation_result)
            
            logger.debug(f"Condition evaluated: {condition_config.condition_expression} = {result}")
            return evaluation_result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Condition evaluation failed: {str(e)}")
            
            return ConditionEvaluationResult(
                result=False,
                confidence=0.0,
                explanation=f"Evaluation failed: {str(e)}",
                execution_time_ms=execution_time
            )
    
    async def _evaluate_parsed_expression(self, parsed: Dict[str, Any], context: ConditionContext) -> Any:
        """Evaluate parsed expression recursively"""
        
        expr_type = parsed.get("type")
        
        if expr_type == "literal":
            return parsed["value"]
        
        elif expr_type == "variable":
            variable_name = parsed["name"]
            return context.get_variable(variable_name)
        
        elif expr_type == "function":
            return await self._evaluate_function(parsed, context)
        
        elif expr_type == "comparison":
            return await self._evaluate_comparison(parsed, context)
        
        elif expr_type == "logical":
            return await self._evaluate_logical(parsed, context)
        
        else:
            raise ValueError(f"Unknown expression type: {expr_type}")
    
    async def _evaluate_function(self, func_expr: Dict[str, Any], context: ConditionContext) -> Any:
        """Evaluate function call"""
        
        func_name = func_expr["function"]
        args_exprs = func_expr["args"]
        
        # Find function implementation
        func_impl = None
        if func_name in self.parser.functions:
            func_impl = self.parser.functions[func_name]
        elif func_name in self.custom_functions:
            func_impl = self.custom_functions[func_name]
        
        if not func_impl:
            raise ValueError(f"Unknown function: {func_name}")
        
        # Evaluate arguments
        evaluated_args = []
        for arg_expr in args_exprs:
            arg_value = await self._evaluate_parsed_expression(arg_expr, context)
            evaluated_args.append(arg_value)
        
        # Execute function
        return await func_impl.execute(evaluated_args, context)
    
    async def _evaluate_comparison(self, comp_expr: Dict[str, Any], context: ConditionContext) -> bool:
        """Evaluate comparison expression"""
        
        operator_symbol = comp_expr["operator"]
        left_expr = comp_expr["left"]
        right_expr = comp_expr["right"]
        
        # Get operator implementation
        operator = self.parser.operators.get(operator_symbol)
        if not operator:
            raise ValueError(f"Unknown operator: {operator_symbol}")
        
        # Evaluate operands
        left_value = await self._evaluate_parsed_expression(left_expr, context)
        right_value = await self._evaluate_parsed_expression(right_expr, context)
        
        # Perform comparison
        return operator.evaluate(left_value, right_value, context)
    
    async def _evaluate_logical(self, logical_expr: Dict[str, Any], context: ConditionContext) -> bool:
        """Evaluate logical expression"""
        
        operator = logical_expr["operator"]
        left_expr = logical_expr["left"]
        right_expr = logical_expr["right"]
        
        # Evaluate left operand
        left_value = await self._evaluate_parsed_expression(left_expr, context)
        
        if operator == "AND":
            # Short-circuit evaluation for AND
            if not left_value:
                return False
            right_value = await self._evaluate_parsed_expression(right_expr, context)
            return bool(left_value) and bool(right_value)
        
        elif operator == "OR":
            # Short-circuit evaluation for OR
            if left_value:
                return True
            right_value = await self._evaluate_parsed_expression(right_expr, context)
            return bool(left_value) or bool(right_value)
        
        else:
            raise ValueError(f"Unknown logical operator: {operator}")
    
    def _extract_variables_used(self, parsed: Dict[str, Any]) -> List[str]:
        """Extract list of variables used in expression"""
        
        variables = set()
        
        def extract_recursive(expr):
            if isinstance(expr, dict):
                if expr.get("type") == "variable":
                    variables.add(expr["name"])
                else:
                    for value in expr.values():
                        if isinstance(value, (dict, list)):
                            extract_recursive(value)
            elif isinstance(expr, list):
                for item in expr:
                    extract_recursive(item)
        
        extract_recursive(parsed)
        return list(variables)
    
    def _get_cache_key(self, condition_config: ConditionalConfig, context: ConditionContext) -> str:
        """Generate cache key for condition evaluation"""
        
        # Include relevant context in cache key
        context_data = {
            "expression": condition_config.condition_expression,
            "user_id": context.execution_context.user_id,
            "program_id": context.execution_context.program_id,
            "completed_steps": len(context.execution_context.completed_steps),
            "variables_hash": hash(str(sorted(context.execution_context.variables.items())))
        }
        
        return f"condition_{hash(str(context_data))}"
    
    def _is_cache_valid(self, cached_result: ConditionEvaluationResult, condition_config: ConditionalConfig) -> bool:
        """Check if cached result is still valid"""
        
        cache_age = (datetime.utcnow() - cached_result.evaluated_at).total_seconds()
        return cache_age < condition_config.cache_duration_seconds
    
    def _cache_result(self, cache_key: str, result: ConditionEvaluationResult):
        """Cache evaluation result"""
        
        # Implement LRU cache with size limit
        if len(self.cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].evaluated_at)
            del self.cache[oldest_key]
        
        self.cache[cache_key] = result
    
    async def validate_condition_expression(self, expression: str) -> Dict[str, Any]:
        """Validate condition expression syntax"""
        
        validation_result = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "variables_used": [],
            "functions_used": []
        }
        
        try:
            # Parse expression
            parsed = self.parser.parse_expression(expression)
            
            # Extract variables and functions
            validation_result["variables_used"] = self._extract_variables_used(parsed)
            validation_result["functions_used"] = self._extract_functions_used(parsed)
            
            # Check for unknown functions
            for func_name in validation_result["functions_used"]:
                if (func_name not in self.parser.functions and 
                    func_name not in self.custom_functions):
                    validation_result["errors"].append(f"Unknown function: {func_name}")
            
            # If no errors, mark as valid
            if not validation_result["errors"]:
                validation_result["is_valid"] = True
            
        except Exception as e:
            validation_result["errors"].append(f"Parse error: {str(e)}")
        
        return validation_result
    
    def _extract_functions_used(self, parsed: Dict[str, Any]) -> List[str]:
        """Extract list of functions used in expression"""
        
        functions = set()
        
        def extract_recursive(expr):
            if isinstance(expr, dict):
                if expr.get("type") == "function":
                    functions.add(expr["function"])
                else:
                    for value in expr.values():
                        if isinstance(value, (dict, list)):
                            extract_recursive(value)
            elif isinstance(expr, list):
                for item in expr:
                    extract_recursive(item)
        
        extract_recursive(parsed)
        return list(functions)


# ==================== CONDITION TEMPLATES ====================

class ConditionTemplate:
    """Pre-built condition templates for common use cases"""
    
    @staticmethod
    def user_completed_steps(min_steps: int) -> str:
        """Template: User has completed minimum number of steps"""
        return f"COUNT(completed_steps) >= {min_steps}"
    
    @staticmethod
    def user_engagement_score(min_score: float) -> str:
        """Template: User engagement score above threshold"""
        return f"AVG(engagement_scores) >= {min_score}"
    
    @staticmethod
    def time_since_start(hours: int) -> str:
        """Template: Time since program start"""
        return f"NOW() >= DAYS_AGO({hours / 24})"
    
    @staticmethod
    def step_success_rate(min_rate: float) -> str:
        """Template: Step success rate above threshold"""
        return f"(COUNT(successful_steps) / COUNT(completed_steps)) >= {min_rate}"
    
    @staticmethod
    def user_has_trait(trait_name: str) -> str:
        """Template: User has specific trait or characteristic"""
        return f"user_traits CONTAINS '{trait_name}'"
    
    @staticmethod
    def program_milestone_reached(milestone_name: str) -> str:
        """Template: Specific program milestone reached"""
        return f"milestones_reached CONTAINS '{milestone_name}'"


# ==================== GLOBAL CONDITION EVALUATOR ====================

_condition_evaluator: Optional[ConditionEvaluator] = None


def get_condition_evaluator() -> ConditionEvaluator:
    """Get global condition evaluator instance"""
    global _condition_evaluator
    if _condition_evaluator is None:
        _condition_evaluator = ConditionEvaluator()
    return _condition_evaluator


# ==================== UTILITY FUNCTIONS ====================

async def evaluate_simple_condition(
    expression: str, 
    context: ExecutionContext,
    program: ProgramDefinition = None
) -> bool:
    """Utility function for simple condition evaluation"""
    
    from .step_models import ConditionalConfig
    
    # Create minimal conditional config
    condition_config = ConditionalConfig(
        condition_expression=expression,
        cache_evaluation_result=False
    )
    
    # Create condition context
    condition_context = ConditionContext(
        execution_context=context,
        program=program,
        step_results={},
        user_variables={},
        system_variables={},
        time_context={"now": datetime.utcnow()}
    )
    
    # Evaluate condition
    evaluator = get_condition_evaluator()
    result = await evaluator.evaluate_condition(condition_config, condition_context)
    
    return result.result


def create_condition_from_template(template_func: Callable, *args) -> str:
    """Create condition expression from template"""
    return template_func(*args)