"""
AST Parser for CodeOptima
Converts Python code into Abstract Syntax Tree for analysis
"""

import ast
import astunparse
from typing import Dict, List, Any, Optional


class ASTParser:
    """Parses Python code into AST and extracts useful information"""
    
    def __init__(self):
        self.tree = None
        self.code_lines = []
        self.functions = []
        self.classes = []
        self.imports = []
        self.errors = []
        # Add this line in __init__ method:
        self.max_lines = 300  # Our new limit

        # Update the parse method:
        def parse(self, code: str) -> bool:
            """Parse Python code into AST"""
            self.code_lines = code.split('\n')
            
            # Check line limit
            if len(self.code_lines) > self.max_lines:
                self.errors.append({
                    'type': 'LINE_LIMIT_EXCEEDED',
                    'msg': f'Code exceeds {self.max_lines} lines (found {len(self.code_lines)}). Please reduce to {self.max_lines} or fewer.',
                    'severity': 'HIGH'
                })
                return False
            # ... rest of the code
    
    def parse(self, code: str) -> bool:
        """
        Parse Python code into AST
        Returns: True if successful, False if syntax error
        """
        try:
            self.code_lines = code.split('\n')
            self.tree = ast.parse(code)
            self._extract_info()
            return True
        except SyntaxError as e:
            self.errors.append({
                'type': 'SYNTAX_ERROR',
                'line': e.lineno,
                'col': e.offset,
                'msg': str(e),
                'severity': 'CRITICAL'
            })
            return False
        except Exception as e:
            self.errors.append({
                'type': 'PARSER_ERROR',
                'msg': str(e),
                'severity': 'HIGH'
            })
            return False
    
    def _extract_info(self):
        """Extract functions, classes, and imports from AST"""
        self.functions = []
        self.classes = []
        self.imports = []
        
        for node in ast.walk(self.tree):
            # Extract function definitions
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'args': len(node.args.args),
                    'kwargs': len(node.args.kwonlyargs),
                    'defaults': len(node.args.defaults),
                    'docstring': ast.get_docstring(node),
                    'returns': self._get_return_type(node)
                }
                self.functions.append(func_info)
            
            # Extract class definitions
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                    'docstring': ast.get_docstring(node)
                }
                self.classes.append(class_info)
            
            # Extract imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports.append({
                        'module': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    self.imports.append({
                        'module': node.module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
    
    def _get_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        """Extract return type annotation if present"""
        if node.returns:
            try:
                return astunparse.unparse(node.returns).strip()
            except:
                return None
        return None
    
    def get_line_content(self, line_number: int) -> str:
        """Get content of specific line (1-indexed)"""
        if 1 <= line_number <= len(self.code_lines):
            return self.code_lines[line_number - 1]
        return ""
    
    def get_ast_dump(self) -> str:
        """Get string representation of AST"""
        return ast.dump(self.tree, indent=2) if self.tree else ""
    
    def get_code_metrics(self) -> Dict[str, Any]:
        """Calculate basic code metrics"""
        if not self.tree:
            return {}
        
        # Count different node types
        node_counts = {}
        for node in ast.walk(self.tree):
            node_type = type(node).__name__
            node_counts[node_type] = node_counts.get(node_type, 0) + 1
        
        return {
            'total_lines': len(self.code_lines),
            'total_functions': len(self.functions),
            'total_classes': len(self.classes),
            'total_imports': len(self.imports),
            'node_distribution': node_counts
        }
    
    def find_pattern(self, pattern: str) -> List[Dict[str, Any]]:
        """
        Find specific AST patterns in code
        Pattern examples: 'FunctionDef', 'For', 'While', 'If', 'Try'
        """
        matches = []
        for node in ast.walk(self.tree):
            if type(node).__name__ == pattern:
                matches.append({
                    'type': pattern,
                    'line': getattr(node, 'lineno', None),
                    'col': getattr(node, 'col_offset', None)
                })
        return matches
    
    def get_issues_by_category(self) -> Dict[str, List[str]]:
        """Categorize and return parsing issues"""
        issues = {
            'syntax_errors': [],
            'warnings': [],
            'info': []
        }
        
        for error in self.errors:
            if error['severity'] == 'CRITICAL':
                issues['syntax_errors'].append(f"Line {error.get('line', '?')}: {error['msg']}")
            elif error['severity'] == 'HIGH':
                issues['warnings'].append(error['msg'])
            else:
                issues['info'].append(error['msg'])
        
        return issues


# Helper function for quick parsing
def parse_code(code: str) -> ASTParser:
    """Quick utility function to parse code"""
    parser = ASTParser()
    parser.parse(code)
    return parser


if __name__ == "__main__":
    # Test the parser
    test_code = """
import os
from typing import List

def calculate_sum(numbers: List[int]) -> int:
    \"\"\"Calculate sum of numbers\"\"\"
    total = 0
    for num in numbers:
        total += num
    return total

class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b
    """
    
    parser = ASTParser()
    success = parser.parse(test_code)
    
    if success:
        print("✅ Parsing successful!")
        print(f"Functions found: {len(parser.functions)}")
        for func in parser.functions:
            print(f"  - {func['name']} (line {func['line']})")
        
        print(f"\nClasses found: {len(parser.classes)}")
        for cls in parser.classes:
            print(f"  - {cls['name']} with {len(cls['methods'])} methods")
        
        print(f"\nImports found: {len(parser.imports)}")
        for imp in parser.imports:
            print(f"  - {imp}")
    else:
        print("❌ Parsing failed!")
        for error in parser.errors:
            print(f"  {error['type']}: {error['msg']}")