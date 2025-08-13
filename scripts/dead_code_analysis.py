#!/usr/bin/env python3
"""
Dead code analysis script.
Identifies unused imports, functions, classes, and environment variables.
"""

import ast
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import argparse

# Try to import centralized regex patterns
try:
    from shared.config.regex_patterns import (
        TODO_FIXME_PATTERN,
        COMMENTED_CODE_PATTERN,
        IF_FALSE_PATTERN,
        EMPTY_EXCEPT_PATTERN,
        LOCALHOST_URL_PATTERN,
        HARDCODED_SECRET_PATTERN,
        COMPILED_PATTERNS
    )
    HAS_REGEX_PATTERNS = True
except ImportError:
    HAS_REGEX_PATTERNS = False


class DeadCodeAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze Python code for dead code."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports: Dict[str, int] = {}  # import_name -> line_number
        self.functions: Dict[str, int] = {}  # function_name -> line_number
        self.classes: Dict[str, int] = {}  # class_name -> line_number
        self.variables: Dict[str, int] = {}  # variable_name -> line_number
        self.used_names: Set[str] = set()
        self.current_class = None
        self.current_function = None
    
    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node.lineno
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import statements."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node.lineno
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions."""
        if not node.name.startswith('_') or node.name in ['__init__', '__str__', '__repr__']:
            self.functions[node.name] = node.lineno
        
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions."""
        if not node.name.startswith('_') or node.name in ['__init__', '__str__', '__repr__']:
            self.functions[node.name] = node.lineno
        
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions."""
        self.classes[node.name] = node.lineno
        
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit variable assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                # Skip private variables and constants
                if not target.id.startswith('_') and not target.id.isupper():
                    self.variables[target.id] = node.lineno
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name) -> None:
        """Visit name references."""
        if isinstance(node.ctx, (ast.Load, ast.Del)):
            self.used_names.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visit attribute access."""
        self.used_names.add(node.attr)
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls."""
        if isinstance(node.func, ast.Name):
            self.used_names.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.used_names.add(node.func.attr)
        self.generic_visit(node)


class ProjectDeadCodeAnalyzer:
    """Analyze dead code across the entire project."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.python_files: List[Path] = []
        self.file_analyzers: Dict[str, DeadCodeAnalyzer] = {}
        self.global_used_names: Set[str] = set()
        
    def find_python_files(self) -> None:
        """Find all Python files in the project."""
        exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv', 'build', 'dist'}
        exclude_files = {'setup.py', 'conftest.py'}
        
        for py_file in self.project_root.rglob("*.py"):
            # Skip excluded directories
            if any(excluded in py_file.parts for excluded in exclude_dirs):
                continue
            
            # Skip excluded files
            if py_file.name in exclude_files:
                continue
                
            self.python_files.append(py_file)
    
    def analyze_file(self, file_path: Path) -> DeadCodeAnalyzer:
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            analyzer = DeadCodeAnalyzer(str(file_path))
            analyzer.visit(tree)
            
            return analyzer
            
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
            return DeadCodeAnalyzer(str(file_path))
    
    def analyze_project(self) -> None:
        """Analyze the entire project for dead code."""
        print("🔍 Finding Python files...")
        self.find_python_files()
        print(f"📁 Found {len(self.python_files)} Python files")
        
        print("🔍 Analyzing files for dead code...")
        for file_path in self.python_files:
            analyzer = self.analyze_file(file_path)
            self.file_analyzers[str(file_path)] = analyzer
            
            # Collect all used names globally
            self.global_used_names.update(analyzer.used_names)
    
    def find_unused_imports(self) -> Dict[str, List[Tuple[str, int]]]:
        """Find unused imports across all files."""
        unused_imports = {}
        
        for file_path, analyzer in self.file_analyzers.items():
            file_unused = []
            
            for import_name, line_no in analyzer.imports.items():
                # Skip common imports that might be used in ways we can't detect
                if import_name in ['os', 'sys', 'logging', 'pytest', 'asyncio']:
                    continue
                
                # Check if import is used in this file
                if import_name not in analyzer.used_names:
                    file_unused.append((import_name, line_no))
            
            if file_unused:
                unused_imports[file_path] = file_unused
        
        return unused_imports
    
    def find_unused_functions(self) -> Dict[str, List[Tuple[str, int]]]:
        """Find unused functions across all files."""
        unused_functions = {}
        
        for file_path, analyzer in self.file_analyzers.items():
            file_unused = []
            
            for func_name, line_no in analyzer.functions.items():
                # Skip special methods and test functions
                if (func_name.startswith('test_') or 
                    func_name.startswith('__') or 
                    func_name in ['main', 'setup', 'teardown']):
                    continue
                
                # Check if function is used globally
                if func_name not in self.global_used_names:
                    file_unused.append((func_name, line_no))
            
            if file_unused:
                unused_functions[file_path] = file_unused
        
        return unused_functions
    
    def find_unused_classes(self) -> Dict[str, List[Tuple[str, int]]]:
        """Find unused classes across all files."""
        unused_classes = {}
        
        for file_path, analyzer in self.file_analyzers.items():
            file_unused = []
            
            for class_name, line_no in analyzer.classes.items():
                # Skip test classes and exception classes
                if (class_name.startswith('Test') or 
                    class_name.endswith('Error') or 
                    class_name.endswith('Exception')):
                    continue
                
                # Check if class is used globally
                if class_name not in self.global_used_names:
                    file_unused.append((class_name, line_no))
            
            if file_unused:
                unused_classes[file_path] = file_unused
        
        return unused_classes
    
    def find_hardcoded_values(self) -> Dict[str, List[Tuple[str, int]]]:
        """Find hardcoded values using regex patterns."""
        if not HAS_REGEX_PATTERNS:
            return {}
            
        hardcoded_values = {}
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_issues = []
                
                # Find localhost URLs
                for match in re.finditer(LOCALHOST_URL_PATTERN, content):
                    line_no = content[:match.start()].count('\n') + 1
                    file_issues.append((f"Hardcoded localhost URL: {match.group()}", line_no))
                
                # Find potential secrets
                for match in re.finditer(HARDCODED_SECRET_PATTERN, content):
                    line_no = content[:match.start()].count('\n') + 1
                    file_issues.append((f"Potential hardcoded secret: {match.group()}", line_no))
                
                if file_issues:
                    hardcoded_values[str(file_path)] = file_issues
                    
            except (UnicodeDecodeError, PermissionError):
                continue
                
        return hardcoded_values
    
    def find_todo_comments(self) -> Dict[str, List[Tuple[str, int]]]:
        """Find TODO/FIXME comments using regex patterns."""
        if not HAS_REGEX_PATTERNS:
            return {}
            
        todo_comments = {}
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_todos = []
                
                for match in re.finditer(TODO_FIXME_PATTERN, content):
                    line_no = content[:match.start()].count('\n') + 1
                    file_todos.append((match.group().strip(), line_no))
                
                if file_todos:
                    todo_comments[str(file_path)] = file_todos
                    
            except (UnicodeDecodeError, PermissionError):
                continue
                
        return todo_comments

    def generate_report(self) -> str:
        """Generate a dead code analysis report."""
        unused_imports = self.find_unused_imports()
        unused_functions = self.find_unused_functions()
        unused_classes = self.find_unused_classes()
        hardcoded_values = self.find_hardcoded_values()
        todo_comments = self.find_todo_comments()
        
        report = []
        report.append("# Dead Code Analysis Report")
        report.append(f"Generated on: {os.popen('date').read().strip()}")
        report.append("")
        
        # Summary
        total_unused_imports = sum(len(items) for items in unused_imports.values())
        total_unused_functions = sum(len(items) for items in unused_functions.values())
        total_unused_classes = sum(len(items) for items in unused_classes.values())
        total_hardcoded_values = sum(len(items) for items in hardcoded_values.values())
        total_todo_comments = sum(len(items) for items in todo_comments.values())
        
        report.append("## Summary")
        report.append(f"- **Files analyzed**: {len(self.python_files)}")
        report.append(f"- **Unused imports**: {total_unused_imports}")
        report.append(f"- **Unused functions**: {total_unused_functions}")
        report.append(f"- **Unused classes**: {total_unused_classes}")
        report.append(f"- **Hardcoded values**: {total_hardcoded_values}")
        report.append(f"- **TODO/FIXME comments**: {total_todo_comments}")
        report.append("")
        
        # Unused imports
        if unused_imports:
            report.append("## Unused Imports")
            report.append("")
            for file_path, imports in unused_imports.items():
                rel_path = os.path.relpath(file_path, self.project_root)
                report.append(f"### {rel_path}")
                for import_name, line_no in imports:
                    report.append(f"- Line {line_no}: `{import_name}`")
                report.append("")
        
        # Unused functions
        if unused_functions:
            report.append("## Unused Functions")
            report.append("")
            for file_path, functions in unused_functions.items():
                rel_path = os.path.relpath(file_path, self.project_root)
                report.append(f"### {rel_path}")
                for func_name, line_no in functions:
                    report.append(f"- Line {line_no}: `{func_name}()`")
                report.append("")
        
        # Unused classes
        if unused_classes:
            report.append("## Unused Classes")
            report.append("")
            for file_path, classes in unused_classes.items():
                rel_path = os.path.relpath(file_path, self.project_root)
                report.append(f"### {rel_path}")
                for class_name, line_no in classes:
                    report.append(f"- Line {line_no}: `class {class_name}`")
                report.append("")
        
        # Hardcoded values
        if hardcoded_values:
            report.append("## Hardcoded Values")
            report.append("")
            for file_path, values in hardcoded_values.items():
                rel_path = os.path.relpath(file_path, self.project_root)
                report.append(f"### {rel_path}")
                for value_desc, line_no in values:
                    report.append(f"- Line {line_no}: {value_desc}")
                report.append("")
        
        # TODO comments
        if todo_comments:
            report.append("## TODO/FIXME Comments")
            report.append("")
            for file_path, todos in todo_comments.items():
                rel_path = os.path.relpath(file_path, self.project_root)
                report.append(f"### {rel_path}")
                for todo_text, line_no in todos:
                    report.append(f"- Line {line_no}: `{todo_text}`")
                report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        report.append("")
        
        if total_unused_imports > 0:
            report.append("### Remove Unused Imports")
            report.append("Remove unused imports to reduce file size and improve clarity.")
            report.append("")
        
        if total_unused_functions > 0:
            report.append("### Review Unused Functions")
            report.append("Review unused functions - they might be:")
            report.append("- Dead code that can be removed")
            report.append("- API functions that should be kept")
            report.append("- Functions used dynamically (false positives)")
            report.append("")
        
        if total_unused_classes > 0:
            report.append("### Review Unused Classes")
            report.append("Review unused classes - they might be:")
            report.append("- Dead code that can be removed")
            report.append("- Model classes used by frameworks")
            report.append("- Classes used dynamically (false positives)")
            report.append("")
        
        return "\n".join(report)
    
    def run_analysis(self, check_only: bool = False) -> bool:
        """Run the complete dead code analysis."""
        print("🚀 Starting dead code analysis...")
        print("=" * 60)
        
        self.analyze_project()
        
        unused_imports = self.find_unused_imports()
        unused_functions = self.find_unused_functions()
        unused_classes = self.find_unused_classes()
        
        total_issues = (
            sum(len(items) for items in unused_imports.values()) +
            sum(len(items) for items in unused_functions.values()) +
            sum(len(items) for items in unused_classes.values())
        )
        
        if check_only:
            if total_issues > 0:
                print(f"❌ Found {total_issues} potential dead code issues")
                return False
            else:
                print("✅ No dead code issues found")
                return True
        
        # Generate and save report
        report = self.generate_report()
        report_file = self.project_root / "dead_code_analysis_report.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📊 Dead code analysis report saved to: {report_file}")
        print("=" * 60)
        print("✅ Dead code analysis completed!")
        
        # Print summary
        print(f"\n📈 Summary:")
        print(f"   - Files analyzed: {len(self.python_files)}")
        print(f"   - Unused imports: {sum(len(items) for items in unused_imports.values())}")
        print(f"   - Unused functions: {sum(len(items) for items in unused_functions.values())}")
        print(f"   - Unused classes: {sum(len(items) for items in unused_classes.values())}")
        
        return total_issues == 0


def main():
    """Main function to run the dead code analysis."""
    parser = argparse.ArgumentParser(description="Analyze dead code in Python project")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Path to project root directory"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for issues, don't generate report"
    )
    
    args = parser.parse_args()
    
    analyzer = ProjectDeadCodeAnalyzer(args.project_root)
    success = analyzer.run_analysis(args.check_only)
    
    if args.check_only:
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()