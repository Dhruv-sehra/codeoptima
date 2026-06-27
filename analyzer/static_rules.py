"""
Static Rule Engine for CodeOptima
Detects code issues based on predefined rules
"""

import re
import ast
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Category(Enum):
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    BEST_PRACTICE = "BEST_PRACTICE"
    STYLE = "STYLE"
    BUG_RISK = "BUG_RISK"


@dataclass
class Issue:
    """Represents a code issue found by analyzer"""
    category: Category
    severity: Severity
    title: str
    description: str
    line: int
    suggestion: str
    rule_id: str


class StaticRuleEngine:
    """Main static analysis engine with rule registry"""
    
    def __init__(self):
        self.rules = []
        self._register_default_rules()
    
    def analyze(self, code: str) -> List[Issue]:
            """Run all registered rules on the code"""
            
            # 🚨 THE TRUE GATEKEEPER: Parse before running any rules
            # If this fails, it automatically throws the SyntaxError back to app.py
            import ast
            ast.parse(code) 
            
            issues = []
            lines = code.split('\n')
            
            for rule in self.rules:
                rule_issues = rule['function'](code, lines)
                issues.extend(rule_issues)
            
            return sorted(issues, key=lambda x: (x.severity.value, x.line))
    
    def add_rule(self, rule_id: str, description: str, 
                 category: Category, severity: Severity,
                 rule_func: Callable[[str, List[str]], List[Issue]]):
        """Register a new analysis rule"""
        self.rules.append({
            'id': rule_id,
            'description': description,
            'category': category,
            'severity': severity,
            'function': rule_func
        })
    
    def _register_default_rules(self):
        """Register all default rules"""
        
        # ML Rules
        self.add_rule(
            rule_id="ML001",
            description="Detect inefficient DataFrame iteration",
            category=Category.PERFORMANCE,
            severity=Severity.HIGH,
            rule_func=self._rule_pandas_iterrows
        )
        # Security Rules
        # Add this to _register_default_rules()
        self.add_rule(
            rule_id="ML001",
            description="Detect inefficient DataFrame iteration",
            category=Category.PERFORMANCE,
            severity=Severity.HIGH,
            rule_func=self._rule_pandas_iterrows
        )
        self.add_rule(
            rule_id="SEC001",
            description="Detect hardcoded passwords/API keys",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            rule_func=self._rule_hardcoded_credentials
        )
        
        self.add_rule(
            rule_id="SEC002",
            description="Detect potential SQL injection",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            rule_func=self._rule_sql_injection
        )
        
        self.add_rule(
            rule_id="SEC003",
            description="Detect dangerous function usage (eval, exec)",
            category=Category.SECURITY,
            severity=Severity.HIGH,
            rule_func=self._rule_dangerous_functions
        )
        
        # Performance Rules
        self.add_rule(
            rule_id="PERF001",
            description="Detect string concatenation in loops",
            category=Category.PERFORMANCE,
            severity=Severity.MEDIUM,
            rule_func=self._rule_string_concat_in_loop
        )
        
        self.add_rule(
            rule_id="PERF002",
            description="Detect nested loops (O(n²) complexity)",
            category=Category.PERFORMANCE,
            severity=Severity.MEDIUM,
            rule_func=self._rule_nested_loops
        )
        
        self.add_rule(
            rule_id="PERF003",
            description="Detect unnecessary list copying",
            category=Category.PERFORMANCE,
            severity=Severity.LOW,
            rule_func=self._rule_unnecessary_copy
        )
        
        # Best Practice Rules
        self.add_rule(
            rule_id="BP001",
            description="Detect missing docstrings",
            category=Category.BEST_PRACTICE,
            severity=Severity.LOW,
            rule_func=self._rule_missing_docstrings
        )
        
        self.add_rule(
            rule_id="BP002",
            description="Detect bare except clauses",
            category=Category.BEST_PRACTICE,
            severity=Severity.MEDIUM,
            rule_func=self._rule_bare_except
        )
        
        self.add_rule(
            rule_id="BP003",
            description="Detect mutable default arguments",
            category=Category.BUG_RISK,
            severity=Severity.MEDIUM,
            rule_func=self._rule_mutable_default_args
        )
        
        # Style Rules
        self.add_rule(
            rule_id="STYLE001",
            description="Check line length (max 79 chars)",
            category=Category.STYLE,
            severity=Severity.LOW,
            rule_func=self._rule_line_length
        )
        
        self.add_rule(
            rule_id="STYLE002",
            description="Check for print statements in production code",
            category=Category.STYLE,
            severity=Severity.LOW,
            rule_func=self._rule_print_statements
        )
    
    # =============== RULE IMPLEMENTATIONS ===============
    
    def _rule_hardcoded_credentials(self, code: str, lines: List[str]) -> List[Issue]:
        """SEC001: Detect hardcoded passwords or API keys"""
        issues = []
        sensitive_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']',
        ]
        
        for i, line in enumerate(lines):
            for pattern in sensitive_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(Issue(
                        category=Category.SECURITY,
                        severity=Severity.CRITICAL,
                        title="Hardcoded Credentials",
                        description=f"Found hardcoded sensitive value in line {i+1}",
                        line=i+1,
                        suggestion="Use environment variables or secure configuration management",
                        rule_id="SEC001"
                    ))
                    break  # Only report once per line
        
        return issues
    
    def _rule_sql_injection(self, code: str, lines: List[str]) -> List[Issue]:
        """SEC002: Detect potential SQL injection vulnerabilities"""
        issues = []
        
        # Look for string concatenation in execute() calls
        sql_patterns = [
            r'execute\(.*\+.*\)',
            r'executemany\(.*\+.*\)',
            r'cursor\.execute\(.*\+.*\)',
            r'f"SELECT.*{.*}.*"',
            r'f"INSERT.*{.*}.*"',
            r'f"UPDATE.*{.*}.*"',
            r'f"DELETE.*{.*}.*"',
        ]
        
        for i, line in enumerate(lines):
            for pattern in sql_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(Issue(
                        category=Category.SECURITY,
                        severity=Severity.CRITICAL,
                        title="Potential SQL Injection",
                        description=f"String concatenation in SQL query at line {i+1}",
                        line=i+1,
                        suggestion="Use parameterized queries: cursor.execute(\"SELECT * FROM users WHERE id = %s\", (user_id,))",
                        rule_id="SEC002"
                    ))
                    break
        
        return issues
    
    def _rule_dangerous_functions(self, code: str, lines: List[str]) -> List[Issue]:
        """SEC003: Detect dangerous function usage"""
        issues = []
        dangerous_functions = ['eval(', 'exec(', 'compile(', 'execfile(', '__import__(']
        
        for i, line in enumerate(lines):
            for func in dangerous_functions:
                if func in line and not line.strip().startswith('#'):
                    issues.append(Issue(
                        category=Category.SECURITY,
                        severity=Severity.HIGH,
                        title="Dangerous Function Usage",
                        description=f"Found {func.rstrip('(')}() function call at line {i+1}",
                        line=i+1,
                        suggestion="Avoid eval() and exec(). Use safer alternatives like ast.literal_eval()",
                        rule_id="SEC003"
                    ))
                    break
        
        return issues
    
    def _rule_string_concat_in_loop(self, code: str, lines: List[str]) -> List[Issue]:
        """PERF001: Detect string concatenation in loops"""
        issues = []
        
        # Simple pattern matching for loops with string concatenation
        for i in range(len(lines)):
            line = lines[i]
            if 'for ' in line or 'while ' in line:
                # Check next few lines for string concatenation
                for j in range(i, min(i+5, len(lines))):
                    if '+=' in lines[j] and ('"' in lines[j] or "'" in lines[j]):
                        issues.append(Issue(
                            category=Category.PERFORMANCE,
                            severity=Severity.MEDIUM,
                            title="Inefficient String Concatenation",
                            description=f"String concatenation in loop at line {j+1}",
                            line=j+1,
                            suggestion="Use ''.join() or list comprehension for better performance",
                            rule_id="PERF001"
                        ))
                        break
        
        return issues
    
    def _rule_nested_loops(self, code: str, lines: List[str]) -> List[Issue]:
        """PERF002: Detect deeply nested loops"""
        issues = []
        loop_stack = 0
        
        for i, line in enumerate(lines):
            if 'for ' in line or 'while ' in line:
                loop_stack += 1
                if loop_stack >= 3:
                    issues.append(Issue(
                        category=Category.PERFORMANCE,
                        severity=Severity.MEDIUM,
                        title="Deeply Nested Loops",
                        description=f"Found {loop_stack} levels of nested loops at line {i+1}",
                        line=i+1,
                        suggestion="Consider refactoring to reduce complexity or use vectorized operations",
                        rule_id="PERF002"
                    ))
            elif line.strip() and not line.startswith((' ', '\t')):
                # Reset on dedent (simplified check)
                loop_stack = max(0, loop_stack - 1)
        
        return issues
    
    def _rule_unnecessary_copy(self, code: str, lines: List[str]) -> List[Issue]:
        """PERF003: Detect unnecessary list copying"""
        issues = []
        unnecessary_patterns = [
            r'\.copy\(\)\s*$',
            r'list\(.*\)\s*$',
            r'\[\s*.*\s*for.*\s*in.*\s*\]\s*\.copy\(\)',
        ]
        
        for i, line in enumerate(lines):
            for pattern in unnecessary_patterns:
                if re.search(pattern, line):
                    issues.append(Issue(
                        category=Category.PERFORMANCE,
                        severity=Severity.LOW,
                        title="Unnecessary Copy",
                        description=f"Unnecessary list copy at line {i+1}",
                        line=i+1,
                        suggestion="Consider using slicing or avoid copying if not needed",
                        rule_id="PERF003"
                    ))
                    break
        
        return issues
    
    def _rule_missing_docstrings(self, code: str, lines: List[str]) -> List[Issue]:
        """BP001: Detect missing function/class docstrings"""
        issues = []
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    docstring = ast.get_docstring(node)
                    if not docstring and node.name != '<module>':
                        issues.append(Issue(
                            category=Category.BEST_PRACTICE,
                            severity=Severity.LOW,
                            title="Missing Docstring",
                            description=f"Function/class '{node.name}' is missing a docstring",
                            line=node.lineno,
                            suggestion="Add a docstring describing purpose, parameters, and return value",
                            rule_id="BP001"
                        ))
        except:
            pass  # Skip if parsing fails
        
        return issues
    
    def _rule_bare_except(self, code: str, lines: List[str]) -> List[Issue]:
        """BP002: Detect bare except clauses"""
        issues = []
        
        for i, line in enumerate(lines):
            if 'except:' in line or 'except Exception:' in line:
                issues.append(Issue(
                    category=Category.BEST_PRACTICE,
                    severity=Severity.MEDIUM,
                    title="Bare Except Clause",
                    description=f"Bare except clause at line {i+1}",
                    line=i+1,
                    suggestion="Catch specific exceptions instead: except ValueError as e:",
                    rule_id="BP002"
                ))
        
        return issues
    
    def _rule_mutable_default_args(self, code: str, lines: List[str]) -> List[Issue]:
        """BP003: Detect mutable default arguments"""
        issues = []
        
        for i, line in enumerate(lines):
            if 'def ' in line and ('=[]' in line or '={}' in line):
                issues.append(Issue(
                    category=Category.BUG_RISK,
                    severity=Severity.MEDIUM,
                    title="Mutable Default Argument",
                    description=f"Mutable default argument at line {i+1}",
                    line=i+1,
                    suggestion="Use None as default: def func(arg=None): arg = arg if arg is not None else []",
                    rule_id="BP003"
                ))
        
        return issues
    
    def _rule_line_length(self, code: str, lines: List[str]) -> List[Issue]:
        """STYLE001: Check line length"""
        issues = []
        
        for i, line in enumerate(lines):
            if len(line) > 79:
                issues.append(Issue(
                    category=Category.STYLE,
                    severity=Severity.LOW,
                    title="Line Too Long",
                    description=f"Line {i+1} exceeds 79 characters ({len(line)} chars)",
                    line=i+1,
                    suggestion="Break long lines for better readability",
                    rule_id="STYLE001"
                ))
        
        return issues
    
    def _rule_print_statements(self, code: str, lines: List[str]) -> List[Issue]:
        """STYLE002: Detect print statements in production code"""
        issues = []
        
        for i, line in enumerate(lines):
            if 'print(' in line and not line.strip().startswith(('#', '"', "'")):
                issues.append(Issue(
                    category=Category.STYLE,
                    severity=Severity.LOW,
                    title="Print Statement",
                    description=f"Print statement found at line {i+1}",
                    line=i+1,
                    suggestion="Use logging module for production code: import logging; logging.info()",
                    rule_id="STYLE002"
                ))
        
        return issues
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about registered rules"""
        stats = {
            'total_rules': len(self.rules),
            'by_category': {},
            'by_severity': {}
        }
        
        for rule in self.rules:
            cat = rule['category'].value
            sev = rule['severity'].value
            
            stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1
            stats['by_severity'][sev] = stats['by_severity'].get(sev, 0) + 1
        
        return stats

    def _rule_pandas_iterrows(self, code: str, lines: List[str]) -> List[Issue]:
            """ML001: Detect use of .iterrows() which is slow in Pandas"""
            issues = []
            for i, line in enumerate(lines):
                if '.iterrows()' in line:
                    issues.append(Issue(
                        category=Category.PERFORMANCE,
                        severity=Severity.HIGH,
                        title="Inefficient ML Loop",
                        description=f"Found .iterrows() at line {i+1}",
                        line=i+1,
                        suggestion="Use .apply(), vectorized operations, or .itertuples() for 10x speedup.",
                        rule_id="ML001"
                    ))
            return issues
# Quick test function
def test_static_rules():
    """Test the static rule engine"""
    test_code = """
def insecure_function(user_input):
    password = "secret123"
    query = "SELECT * FROM users WHERE id = " + user_input
    result = eval("2 + 2")
    return result

def slow_function():
    result = ""
    for i in range(100):
        result += str(i)
    return result

def buggy_function(items=[]):
    items.append(1)
    return items
    """
    
    engine = StaticRuleEngine()
    issues = engine.analyze(test_code)
    
    print(f"Found {len(issues)} issues:")
    for issue in issues:
        print(f"\n[{issue.severity.value}] {issue.title}")
        print(f"  Line {issue.line}: {issue.description}")
        print(f"  💡 {issue.suggestion}")
    
    return issues


if __name__ == "__main__":
    test_static_rules()