"""
Comprehensive regex patterns for code search, cleanup, and migration.

This module provides regex patterns for identifying environment variable usage,
hardcoded values, dead code, and migration candidates throughout the codebase.
"""

import re
from typing import Pattern, Dict, List, Optional, Tuple


# ============================================================================
# ENVIRONMENT VARIABLE DETECTION PATTERNS
# ============================================================================

# Pattern to find all os.getenv() calls with variable names and optional defaults
# Matches: os.getenv("VAR_NAME"), os.getenv("VAR_NAME", "default"), os.getenv('VAR_NAME', default_value)
OS_GETENV_PATTERN = r'os\.getenv\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*([^)]+))?\s*\)'

# Pattern to find all os.environ.get() calls
# Matches: os.environ.get("VAR_NAME"), os.environ.get("VAR_NAME", "default")
OS_ENVIRON_GET_PATTERN = r'os\.environ\.get\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*([^)]+))?\s*\)'

# Pattern to find direct os.environ[] access
# Matches: os.environ["VAR_NAME"], os.environ['VAR_NAME']
OS_ENVIRON_DIRECT_PATTERN = r'os\.environ\s*\[\s*["\']([^"\']+)["\']\s*\]'

# Pattern to find all Field(..., env="...") definitions in Pydantic models
# Matches: Field(default="value", env="VAR_NAME"), Field(..., env="VAR_NAME")
FIELD_ENV_PATTERN = r'Field\s*\([^)]*\benv\s*=\s*["\']([^"\']+)["\'][^)]*\)'

# Pattern to find environment variable references in strings
# Matches: "${VAR_NAME}", "$VAR_NAME", %VAR_NAME%
ENV_VAR_USAGE_PATTERN = r'(?:\$\{([A-Z_][A-Z0-9_]*)\}|\$([A-Z_][A-Z0-9_]*)|%([A-Z_][A-Z0-9_]*)%)'

# Combined pattern for any environment variable access
ANY_ENV_ACCESS_PATTERN = r'(?:' + '|'.join([
    OS_GETENV_PATTERN,
    OS_ENVIRON_GET_PATTERN,
    OS_ENVIRON_DIRECT_PATTERN,
    FIELD_ENV_PATTERN
]) + r')'


# ============================================================================
# HARDCODED VALUES PATTERNS
# ============================================================================

# Pattern to find hardcoded localhost URLs
# Matches: http://localhost:8000, https://localhost:3000, http://127.0.0.1:5432
LOCALHOST_URL_PATTERN = r'https?://(?:localhost|127\.0\.0\.1)(?::\d+)?(?:/[^\s"\']*)?' 

# Pattern to find hardcoded database URLs
# Matches: postgresql://..., postgres://..., mysql://..., mongodb://...
DATABASE_URL_PATTERN = r'(?:postgresql|postgres|mysql|mongodb|sqlite)(?:\+[a-z]+)?://[^\s"\']+'

# Pattern to find hardcoded Redis URLs
# Matches: redis://localhost:6379, redis://127.0.0.1:6379/0
REDIS_URL_PATTERN = r'redis://[^\s"\']+'

# Pattern to find hardcoded API keys or secrets
# Matches: strings that look like API keys, tokens, or secrets
HARDCODED_SECRET_PATTERN = r'(?:api[_-]?key|secret[_-]?key|token|password)\s*[:=]\s*["\'][^"\']{16,}["\']'

# Pattern to find hardcoded port numbers
# Matches: :8000, :3000, :5432 (common development ports)
HARDCODED_PORT_PATTERN = r'(?::|port\s*=\s*)(?:3000|3001|5000|5432|6379|8000|8001|8002|8080|11434)\b'

# Pattern to find common hardcoded default values
# Matches: "development", "debug", "test", "localhost", etc.
HARDCODED_DEFAULTS_PATTERN = r'(?:default\s*=\s*)?["\'](?:development|debug|test|localhost|changeme|secret|password|admin)["\']'

# Pattern to find hardcoded file paths
# Matches: /tmp/..., ./uploads/..., C:\..., /var/lib/...
HARDCODED_PATH_PATTERN = r'["\'](?:/tmp/|/var/|/etc/|/home/|\.{1,2}/|[A-Z]:\\)[^"\']+["\']'


# ============================================================================
# DEAD CODE DETECTION PATTERNS
# ============================================================================

# Pattern to find commented out code blocks (Python)
# Matches: # code_line, """ commented block """, ''' commented block '''
COMMENTED_CODE_PATTERN = r'(?:^\s*#[^#\n]*(?:def |class |import |from |if |for |while |try |except |return |raise )|"""[^"]*(?:def |class |import |from |if |for |while |try |except |return |raise )[^"]*"""|\'\'\'[^\']*(?:def |class |import |from |if |for |while |try |except |return |raise )[^\']*\'\'\')'

# Pattern to find TODO/FIXME/HACK/XXX comments
# Matches: # TODO: ..., # FIXME: ..., # HACK: ..., # XXX: ...
TODO_FIXME_PATTERN = r'#\s*(?:TODO|FIXME|HACK|XXX|BUG|DEPRECATED|REFACTOR|OPTIMIZE|NOTE)\s*:?\s*[^\n]*'

# Pattern to find unused imports (basic detection)
# Matches: import statements where the module might not be used
UNUSED_IMPORT_PATTERN = r'^(?:from\s+[^\s]+\s+)?import\s+([^\s,]+(?:\s*,\s*[^\s,]+)*)'

# Pattern to find if False blocks
# Matches: if False:, if 0:, if None:
IF_FALSE_PATTERN = r'^\s*if\s+(?:False|0|None)\s*:'

# Pattern to find unreachable code after return/raise/break/continue
# Matches: code after return, raise, break, or continue statements
UNREACHABLE_CODE_PATTERN = r'^\s*(?:return|raise|break|continue)\b[^\n]*\n\s+(?!#|\s*$)[^\n]+'

# Pattern to find empty except blocks
# Matches: except: pass, except Exception: pass
EMPTY_EXCEPT_PATTERN = r'except(?:\s+[^\:]+)?\s*:\s*(?:pass|\.\.\.)\s*(?:\n|$)'

# Pattern to find duplicate function/class definitions (basic)
# Matches: multiple definitions with the same name
DUPLICATE_DEFINITION_PATTERN = r'(?:def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)'

# Combined dead code patterns
DEAD_CODE_PATTERNS = '|'.join([
    COMMENTED_CODE_PATTERN,
    IF_FALSE_PATTERN,
    UNREACHABLE_CODE_PATTERN,
    EMPTY_EXCEPT_PATTERN
])


# ============================================================================
# MIGRATION HELPER PATTERNS
# ============================================================================

# Pattern to find the fallback pattern: config.value or os.getenv() or default
# Matches: config.database_url or os.getenv("DATABASE_URL") or "default"
FALLBACK_CHAIN_PATTERN = r'(?:[a-zA-Z_][a-zA-Z0-9_\.]*\s+or\s+)?os\.getenv\s*\([^)]+\)\s+or\s+[^,\)\n]+'

# Pattern to find direct config attribute access that could use env vars
# Matches: config.database_url, settings.redis_url, etc.
CONFIG_ATTRIBUTE_PATTERN = r'(?:config|settings|cfg|conf)\s*\.\s*([a-z_][a-z0-9_]*)'

# Pattern to find string formatting with environment variables
# Matches: f"{os.getenv('VAR')}", "{}".format(os.getenv('VAR'))
ENV_STRING_FORMAT_PATTERN = r'(?:f["\'][^"\']*\{[^}]*os\.getenv[^}]+\}[^"\']*["\']|["\'][^"\']*\{\}[^"\']*["\']\.format\s*\([^)]*os\.getenv[^)]+\))'

# Pattern to find environment variable assignments
# Matches: VAR_NAME = os.getenv("VAR_NAME")
ENV_ASSIGNMENT_PATTERN = r'^([A-Z_][A-Z0-9_]*)\s*=\s*os\.(?:getenv|environ\.get)\s*\([^)]+\)'

# Pattern to find conditional environment checks
# Matches: if os.getenv("DEBUG"), if "ENVIRONMENT" in os.environ
ENV_CONDITIONAL_PATTERN = r'if\s+(?:os\.getenv\s*\([^)]+\)|["\'][^"\']+["\']\s+in\s+os\.environ)'

# Combined migration candidate patterns
MIGRATION_CANDIDATES = '|'.join([
    FALLBACK_CHAIN_PATTERN,
    ENV_STRING_FORMAT_PATTERN,
    ENV_ASSIGNMENT_PATTERN,
    ENV_CONDITIONAL_PATTERN
])


# ============================================================================
# SEARCH AND REPLACE HELPERS
# ============================================================================

def create_replacement_pattern(old_var: str, new_constant: str) -> str:
    """
    Generate a regex pattern for safe replacement of environment variable references.
    
    Args:
        old_var: The old variable name (e.g., "DATABASE_URL")
        new_constant: The new constant reference (e.g., "env_constants.DATABASE_URL")
    
    Returns:
        str: A regex replacement pattern
    
    Example:
        >>> pattern = create_replacement_pattern("DATABASE_URL", "env_constants.DATABASE_URL")
        >>> # This will create a pattern to replace os.getenv("DATABASE_URL") with get_env_value(env_constants.DATABASE_URL)
    """
    # Escape special regex characters in the old variable name
    escaped_var = re.escape(old_var)
    
    # Create patterns for different usage contexts
    patterns = [
        # os.getenv("VAR") -> get_env_value(CONSTANT)
        (f'os\\.getenv\\s*\\(\\s*["\']({escaped_var})["\']\\s*\\)', f'get_env_value({new_constant})'),
        
        # os.getenv("VAR", default) -> get_env_value(CONSTANT, default=default)
        (f'os\\.getenv\\s*\\(\\s*["\']({escaped_var})["\']\\s*,\\s*([^)]+)\\)', f'get_env_value({new_constant}, default=\\2)'),
        
        # os.environ.get("VAR") -> get_env_value(CONSTANT)
        (f'os\\.environ\\.get\\s*\\(\\s*["\']({escaped_var})["\']\\s*\\)', f'get_env_value({new_constant})'),
        
        # os.environ["VAR"] -> get_env_value(CONSTANT)
        (f'os\\.environ\\s*\\[\\s*["\']({escaped_var})["\']\\s*\\]', f'get_env_value({new_constant})'),
        
        # Field(env="VAR") -> Field(env=CONSTANT)
        (f'Field\\s*\\([^)]*\\benv\\s*=\\s*["\']({escaped_var})["\']', f'Field(\\g<0>env={new_constant}'),
    ]
    
    return patterns


def validate_pattern_match(pattern: str, text: str) -> List[Tuple[str, int, int]]:
    """
    Validate that a regex pattern matches the given text and return all matches.
    
    Args:
        pattern: The regex pattern to test
        text: The text to search in
    
    Returns:
        List[Tuple[str, int, int]]: List of (matched_text, start_pos, end_pos)
    
    Example:
        >>> matches = validate_pattern_match(OS_GETENV_PATTERN, 'db_url = os.getenv("DATABASE_URL", "localhost")')
        >>> # Returns: [('os.getenv("DATABASE_URL", "localhost")', 9, 47)]
    """
    try:
        compiled_pattern = re.compile(pattern, re.MULTILINE)
        matches = []
        for match in compiled_pattern.finditer(text):
            matches.append((match.group(0), match.start(), match.end()))
        return matches
    except re.error as e:
        print(f"Invalid regex pattern: {e}")
        return []


def find_env_vars_in_file(file_content: str) -> Dict[str, List[str]]:
    """
    Find all environment variable references in a file.
    
    Args:
        file_content: The content of the file to analyze
    
    Returns:
        Dict[str, List[str]]: Dictionary mapping pattern types to found variables
    
    Example:
        >>> content = 'db = os.getenv("DATABASE_URL")\\nredis = os.environ.get("REDIS_URL")'
        >>> vars = find_env_vars_in_file(content)
        >>> # Returns: {'os.getenv': ['DATABASE_URL'], 'os.environ.get': ['REDIS_URL']}
    """
    results = {
        'os.getenv': [],
        'os.environ.get': [],
        'os.environ[]': [],
        'Field(env=)': []
    }
    
    # Find os.getenv() calls
    for match in re.finditer(OS_GETENV_PATTERN, file_content):
        results['os.getenv'].append(match.group(1))
    
    # Find os.environ.get() calls
    for match in re.finditer(OS_ENVIRON_GET_PATTERN, file_content):
        results['os.environ.get'].append(match.group(1))
    
    # Find os.environ[] access
    for match in re.finditer(OS_ENVIRON_DIRECT_PATTERN, file_content):
        results['os.environ[]'].append(match.group(1))
    
    # Find Field(env=) definitions
    for match in re.finditer(FIELD_ENV_PATTERN, file_content):
        results['Field(env=)'].append(match.group(1))
    
    # Remove duplicates while preserving order
    for key in results:
        results[key] = list(dict.fromkeys(results[key]))
    
    return results


# ============================================================================
# USAGE EXAMPLES AND DOCUMENTATION
# ============================================================================

"""
USAGE EXAMPLES:

1. Finding all environment variable usage:
   ```bash
   # Using grep with the patterns
   grep -r -E 'os\.getenv\s*\(\s*["\'][^"\']+["\']\s*(?:,\s*[^)]+)?\s*\)' .
   
   # Finding all Field(env=...) definitions
   grep -r -E 'Field\s*\([^)]*\benv\s*=\s*["\'][^"\']+["\'][^)]*\)' .
   ```

2. Identifying hardcoded values:
   ```bash
   # Find localhost URLs
   grep -r -E 'https?://(?:localhost|127\.0\.0\.1)(?::\d+)?(?:/[^\s"\']*)?' .
   
   # Find hardcoded database URLs
   grep -r -E '(?:postgresql|postgres|mysql|mongodb)://[^\s"\']+' .
   ```

3. Detecting dead code:
   ```bash
   # Find TODO/FIXME comments
   grep -r -E '#\s*(?:TODO|FIXME|HACK|XXX)\s*:?\s*[^\n]*' .
   
   # Find if False blocks
   grep -r -E '^\s*if\s+(?:False|0|None)\s*:' .
   ```

4. Using in Python code:
   ```python
   import re
   from shared.config.regex_patterns import (
       OS_GETENV_PATTERN,
       find_env_vars_in_file,
       validate_pattern_match
   )
   
   # Read a file and find environment variables
   with open('config.py', 'r') as f:
       content = f.read()
       env_vars = find_env_vars_in_file(content)
       print(f"Found environment variables: {env_vars}")
   
   # Validate a pattern
   text = 'db_url = os.getenv("DATABASE_URL", "localhost")'
   matches = validate_pattern_match(OS_GETENV_PATTERN, text)
   for match, start, end in matches:
       print(f"Found: {match} at position {start}-{end}")
   ```

5. Migration assistance:
   ```python
   # Generate replacement patterns for migration
   from shared.config.regex_patterns import create_replacement_pattern
   
   patterns = create_replacement_pattern("DATABASE_URL", "env_constants.DATABASE_URL")
   for old_pattern, new_pattern in patterns:
       # Use these patterns with re.sub() for migration
       pass
   ```

PATTERN DESCRIPTIONS:

- OS_GETENV_PATTERN: Finds os.getenv() calls with variable names and optional defaults
- OS_ENVIRON_GET_PATTERN: Finds os.environ.get() calls
- OS_ENVIRON_DIRECT_PATTERN: Finds direct os.environ[] access
- FIELD_ENV_PATTERN: Finds Pydantic Field definitions with env parameter
- ENV_VAR_USAGE_PATTERN: Finds environment variable references in strings (${VAR}, $VAR, %VAR%)
- LOCALHOST_URL_PATTERN: Finds hardcoded localhost URLs
- DATABASE_URL_PATTERN: Finds hardcoded database connection strings
- REDIS_URL_PATTERN: Finds hardcoded Redis URLs
- HARDCODED_SECRET_PATTERN: Finds potential hardcoded API keys or secrets
- HARDCODED_PORT_PATTERN: Finds hardcoded port numbers
- HARDCODED_DEFAULTS_PATTERN: Finds common hardcoded default values
- HARDCODED_PATH_PATTERN: Finds hardcoded file system paths
- COMMENTED_CODE_PATTERN: Finds commented out code blocks
- TODO_FIXME_PATTERN: Finds TODO, FIXME, HACK, XXX comments
- UNUSED_IMPORT_PATTERN: Finds potentially unused imports
- IF_FALSE_PATTERN: Finds if False/0/None blocks
- UNREACHABLE_CODE_PATTERN: Finds code after return/raise/break/continue
- EMPTY_EXCEPT_PATTERN: Finds empty except blocks
- FALLBACK_CHAIN_PATTERN: Finds chained fallback patterns (x or y or z)
- CONFIG_ATTRIBUTE_PATTERN: Finds config/settings attribute access
- ENV_STRING_FORMAT_PATTERN: Finds string formatting with environment variables
- ENV_ASSIGNMENT_PATTERN: Finds environment variable assignments
- ENV_CONDITIONAL_PATTERN: Finds conditional checks on environment variables
"""

# ============================================================================
# COMPILED PATTERNS FOR PERFORMANCE
# ============================================================================

# Pre-compile frequently used patterns for better performance
COMPILED_PATTERNS: Dict[str, Pattern] = {
    'os_getenv': re.compile(OS_GETENV_PATTERN, re.MULTILINE),
    'os_environ_get': re.compile(OS_ENVIRON_GET_PATTERN, re.MULTILINE),
    'os_environ_direct': re.compile(OS_ENVIRON_DIRECT_PATTERN, re.MULTILINE),
    'field_env': re.compile(FIELD_ENV_PATTERN, re.MULTILINE),
    'localhost_url': re.compile(LOCALHOST_URL_PATTERN, re.MULTILINE),
    'database_url': re.compile(DATABASE_URL_PATTERN, re.MULTILINE),
    'redis_url': re.compile(REDIS_URL_PATTERN, re.MULTILINE),
    'todo_fixme': re.compile(TODO_FIXME_PATTERN, re.MULTILINE),
    'if_false': re.compile(IF_FALSE_PATTERN, re.MULTILINE),
    'empty_except': re.compile(EMPTY_EXCEPT_PATTERN, re.MULTILINE),
}


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    # Environment variable patterns
    'OS_GETENV_PATTERN',
    'OS_ENVIRON_GET_PATTERN', 
    'OS_ENVIRON_DIRECT_PATTERN',
    'FIELD_ENV_PATTERN',
    'ENV_VAR_USAGE_PATTERN',
    'ANY_ENV_ACCESS_PATTERN',
    
    # Hardcoded value patterns
    'LOCALHOST_URL_PATTERN',
    'DATABASE_URL_PATTERN',
    'REDIS_URL_PATTERN',
    'HARDCODED_SECRET_PATTERN',
    'HARDCODED_PORT_PATTERN',
    'HARDCODED_DEFAULTS_PATTERN',
    'HARDCODED_PATH_PATTERN',
    
    # Dead code patterns
    'COMMENTED_CODE_PATTERN',
    'TODO_FIXME_PATTERN',
    'UNUSED_IMPORT_PATTERN',
    'IF_FALSE_PATTERN',
    'UNREACHABLE_CODE_PATTERN',
    'EMPTY_EXCEPT_PATTERN',
    'DEAD_CODE_PATTERNS',
    
    # Migration patterns
    'FALLBACK_CHAIN_PATTERN',
    'CONFIG_ATTRIBUTE_PATTERN',
    'ENV_STRING_FORMAT_PATTERN',
    'ENV_ASSIGNMENT_PATTERN',
    'ENV_CONDITIONAL_PATTERN',
    'MIGRATION_CANDIDATES',
    
    # Helper functions
    'create_replacement_pattern',
    'validate_pattern_match',
    'find_env_vars_in_file',
    
    # Compiled patterns
    'COMPILED_PATTERNS',
]