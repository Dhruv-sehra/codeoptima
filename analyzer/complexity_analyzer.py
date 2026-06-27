"""
Complexity Analyzer for CodeOptima
Calculates code metrics and complexity scores
"""

import ast
import math
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class ComplexityLevel(Enum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


@dataclass
class ComplexityMetrics:
    """Container for all complexity metrics"""
    lines_of_code: int
    comment_lines: int
    blank_lines: int
    function_count: int
    class_count: int
    cyclomatic_complexity: float
    maintainability_index: float
    halstead_volume: float
    cognitive_complexity: int
    duplication_rate: float


class ComplexityAnalyzer:
    """Analyzes code complexity using various metrics"""
    
    def __init__(self):
        self.metrics = None
    
    def analyze(self, code: str) -> ComplexityMetrics:
        """Calculate all complexity metrics for the code"""
        lines = code.split('\n')
        
        loc = len(lines)
        comment_lines = self._count_comment_lines(lines)
        blank_lines = self._count_blank_lines(lines)
        
        # Parse AST for structural analysis
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Return basic metrics if parsing fails
            return ComplexityMetrics(
                lines_of_code=loc,
                comment_lines=comment_lines,
                blank_lines=blank_lines,
                function_count=0,
                class_count=0,
                cyclomatic_complexity=0,
                maintainability_index=0,
                halstead_volume=0,
                cognitive_complexity=0,
                duplication_rate=0
            )
        
        function_count = self._count_functions(tree)
        class_count = self._count_classes(tree)
        cyclomatic = self._calculate_cyclomatic_complexity(code, tree)
        maintainability = self._calculate_maintainability_index(
            loc, comment_lines, cyclomatic
        )
        halstead = self._calculate_halstead_metrics(code)
        cognitive = self._calculate_cognitive_complexity(tree)
        duplication = self._estimate_duplication(code)
        
        self.metrics = ComplexityMetrics(
            lines_of_code=loc,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=function_count,
            class_count=class_count,
            cyclomatic_complexity=cyclomatic,
            maintainability_index=maintainability,
            halstead_volume=halstead,
            cognitive_complexity=cognitive,
            duplication_rate=duplication
        )
        
        return self.metrics
    
    def _count_comment_lines(self, lines: List[str]) -> int:
        """Count comment lines (single line and inline)"""
        count = 0
        in_multiline = False
        
        for line in lines:
            stripped = line.strip()
            
            # Check for multiline comments
            if '"""' in line or "'''" in line:
                in_multiline = not in_multiline
                count += 1
                continue
            
            if in_multiline:
                count += 1
            elif stripped.startswith('#') or (not stripped and '#' in line):
                count += 1
        
        return count
    
    def _count_blank_lines(self, lines: List[str]) -> int:
        """Count blank/empty lines"""
        return sum(1 for line in lines if not line.strip())
    
    def _count_functions(self, tree: ast.AST) -> int:
        """Count function definitions"""
        return len([node for node in ast.walk(tree) 
                   if isinstance(node, ast.FunctionDef)])
    
    def _count_classes(self, tree: ast.AST) -> int:
        """Count class definitions"""
        return len([node for node in ast.walk(tree) 
                   if isinstance(node, ast.ClassDef)])
    
    def _calculate_cyclomatic_complexity(self, code: str, tree: ast.AST) -> float:
        """Calculate McCabe's cyclomatic complexity"""
        # Count decision points
        decision_points = 0
        
        # Keywords that increase complexity
        decision_keywords = [
            'if', 'elif', 'else', 'for', 'while', 'and', 'or',
            'except', 'finally', 'with', 'assert', 'async', 'await'
        ]
        
        for node in ast.walk(tree):
            node_type = type(node).__name__
            if node_type in ['If', 'For', 'While', 'AsyncFor', 'AsyncWith']:
                decision_points += 1
            elif node_type in ['BoolOp', 'Try', 'With', 'Assert']:
                decision_points += 1
            elif node_type == 'ExceptHandler':
                decision_points += 1
        
        # Add 1 for the function entry point
        complexity = decision_points + 1
        
        # Normalize by lines of code (prevent division by zero)
        lines = len(code.split('\n'))
        if lines > 0:
            complexity = complexity / lines * 10  # Scale for readability
        
        return round(complexity, 2)
    
    def _calculate_maintainability_index(self, loc: int, 
                                        comments: int, 
                                        cyclomatic: float) -> float:
        """Calculate maintainability index (simplified)"""
        if loc == 0:
            return 100.0
        
        # Calculate comment percentage
        comment_percentage = (comments / loc * 100) if loc > 0 else 0
        
        # Simplified MI formula (based on original: 171 - 5.2*ln(HV) - 0.23*CC - 16.2*ln(LOC))
        # We'll use a simpler approximation
        normalized_cyclomatic = min(cyclomatic * 10, 50)  # Cap at 50
        
        # Higher is better (max 100)
        mi = 100 - (normalized_cyclomatic * 0.5) + (comment_percentage * 0.3)
        
        # Ensure within bounds
        mi = max(0, min(100, mi))
        return round(mi, 1)
    
    def _calculate_halstead_metrics(self, code: str) -> float:
        """Calculate simplified Halstead volume"""
        # Tokenize the code (simplified)
        operators = ['+', '-', '*', '/', '=', '==', '!=', '<', '>', '<=', '>=',
                    'and', 'or', 'not', 'in', 'is', '+=', '-=', '*=', '/=']
        
        operands = []
        operators_found = []
        
        # Simple token counting
        tokens = code.replace('\n', ' ').replace('(', ' ').replace(')', ' ').split()
        
        for token in tokens:
            if token in operators:
                operators_found.append(token)
            elif token.isidentifier() and token not in ['def', 'class', 'if', 'else']:
                operands.append(token)
        
        # Unique counts
        n1 = len(set(operators_found))  # Distinct operators
        n2 = len(set(operands))          # Distinct operands
        N1 = len(operators_found)        # Total operators
        N2 = len(operands)               # Total operands
        
        if n1 == 0 or n2 == 0:
            return 0.0
        
        # Halstead Volume: V = N * log2(n)
        N = N1 + N2
        n = n1 + n2
        volume = N * math.log2(n) if n > 0 else 0
        
        return round(volume, 2)
    
    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """Calculate cognitive complexity (simplified SonarQube metric)"""
        complexity = 0
        
        for node in ast.walk(tree):
            # Increment for control flow structures
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
                # Nested structures add more
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                        complexity += 1
            
            # Increment for try-except
            elif isinstance(node, ast.Try):
                complexity += 1
            
            # Increment for boolean operators
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _estimate_duplication(self, code: str) -> float:
        """Estimate code duplication rate (simplified)"""
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        
        if len(lines) < 2:
            return 0.0
        
        # Count unique lines
        unique_lines = set(lines)
        
        # Calculate duplication rate
        duplication_rate = 1 - (len(unique_lines) / len(lines))
        return round(duplication_rate * 100, 2)  # As percentage
    
    def get_complexity_level(self, metrics: ComplexityMetrics) -> ComplexityLevel:
        """Determine overall complexity level"""
        score = 0
        
        # Weight different metrics
        if metrics.cyclomatic_complexity > 15:
            score += 3
        elif metrics.cyclomatic_complexity > 10:
            score += 2
        elif metrics.cyclomatic_complexity > 5:
            score += 1
        
        if metrics.maintainability_index < 40:
            score += 3
        elif metrics.maintainability_index < 60:
            score += 2
        elif metrics.maintainability_index < 80:
            score += 1
        
        if metrics.cognitive_complexity > 20:
            score += 3
        elif metrics.cognitive_complexity > 10:
            score += 2
        elif metrics.cognitive_complexity > 5:
            score += 1
        
        if metrics.lines_of_code > 200:
            score += 2
        elif metrics.lines_of_code > 100:
            score += 1
        
        # Determine level
        if score >= 8:
            return ComplexityLevel.VERY_HIGH
        elif score >= 6:
            return ComplexityLevel.HIGH
        elif score >= 4:
            return ComplexityLevel.MEDIUM
        elif score >= 2:
            return ComplexityLevel.LOW
        else:
            return ComplexityLevel.VERY_LOW
    
    def generate_report(self, metrics: ComplexityMetrics) -> Dict[str, Any]:
        """Generate a comprehensive complexity report"""
        level = self.get_complexity_level(metrics)
        
        return {
            'overall_level': level.value,
            'basic_metrics': {
                'lines_of_code': metrics.lines_of_code,
                'comment_lines': metrics.comment_lines,
                'comment_percentage': round(metrics.comment_lines / max(metrics.lines_of_code, 1) * 100, 1),
                'blank_lines': metrics.blank_lines,
                'code_lines': metrics.lines_of_code - metrics.comment_lines - metrics.blank_lines,
                'functions': metrics.function_count,
                'classes': metrics.class_count
            },
            'complexity_metrics': {
                'cyclomatic_complexity': {
                    'value': metrics.cyclomatic_complexity,
                    'interpretation': self._interpret_cyclomatic(metrics.cyclomatic_complexity)
                },
                'maintainability_index': {
                    'value': metrics.maintainability_index,
                    'interpretation': self._interpret_maintainability(metrics.maintainability_index)
                },
                'cognitive_complexity': {
                    'value': metrics.cognitive_complexity,
                    'interpretation': self._interpret_cognitive(metrics.cognitive_complexity)
                },
                'halstead_volume': {
                    'value': metrics.halstead_volume,
                    'interpretation': self._interpret_halstead(metrics.halstead_volume)
                }
            },
            'duplication': {
                'rate': metrics.duplication_rate,
                'interpretation': self._interpret_duplication(metrics.duplication_rate)
            },
            'recommendations': self._generate_recommendations(metrics, level)
        }
    
    def _interpret_cyclomatic(self, value: float) -> str:
        if value < 5:
            return "Excellent - Simple and testable"
        elif value < 10:
            return "Good - Moderate complexity"
        elif value < 15:
            return "Fair - Consider refactoring"
        else:
            return "Poor - High risk, needs refactoring"
    
    def _interpret_maintainability(self, value: float) -> str:
        if value >= 85:
            return "Excellent - Very maintainable"
        elif value >= 65:
            return "Good - Maintainable"
        elif value >= 50:
            return "Fair - Needs attention"
        else:
            return "Poor - Difficult to maintain"
    
    def _interpret_cognitive(self, value: int) -> str:
        if value < 5:
            return "Excellent - Easy to understand"
        elif value < 15:
            return "Good - Understandable"
        elif value < 25:
            return "Fair - Somewhat complex"
        else:
            return "Poor - Very difficult to understand"
    
    def _interpret_halstead(self, value: float) -> str:
        if value < 100:
            return "Very simple"
        elif value < 1000:
            return "Simple"
        elif value < 10000:
            return "Moderate"
        else:
            return "Complex"
    
    def _interpret_duplication(self, rate: float) -> str:
        if rate < 5:
            return "Excellent - Minimal duplication"
        elif rate < 15:
            return "Good - Acceptable duplication"
        elif rate < 30:
            return "Fair - Some duplication"
        else:
            return "Poor - High duplication, needs refactoring"
    
    def _generate_recommendations(self, metrics: ComplexityMetrics, 
                                 level: ComplexityLevel) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []
        
        # Check cyclomatic complexity
        if metrics.cyclomatic_complexity > 10:
            recommendations.append(
                "🔍 Break down complex functions into smaller, single-purpose functions"
            )
        
        # Check maintainability
        if metrics.maintainability_index < 60:
            recommendations.append(
                "📝 Add more comments and documentation to improve maintainability"
            )
        
        # Check cognitive complexity
        if metrics.cognitive_complexity > 15:
            recommendations.append(
                "🧠 Simplify nested conditions and loops to reduce cognitive load"
            )
        
        # Check duplication
        if metrics.duplication_rate > 10:
            recommendations.append(
                "♻️ Extract duplicated code into reusable functions or classes"
            )
        
        # Check comment ratio
        comment_ratio = metrics.comment_lines / max(metrics.lines_of_code, 1)
        if comment_ratio < 0.1:  # Less than 10% comments
            recommendations.append(
                "💬 Increase code comments to at least 20% for better readability"
            )
        
        # Check function count
        if metrics.function_count == 0 and metrics.lines_of_code > 20:
            recommendations.append(
                "⚡ Consider organizing code into functions for better modularity"
            )
        
        # Add general recommendation based on level
        if level == ComplexityLevel.VERY_HIGH:
            recommendations.append(
                "🚨 High complexity detected. Consider major refactoring or breaking into modules."
            )
        
        return recommendations


# Test function
def test_complexity_analyzer():
    """Test the complexity analyzer"""
    test_code = """
def calculate_fibonacci(n):
    \"\"\"Calculate nth Fibonacci number\"\"\"
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def process_data(data):
    result = []
    for item in data:
        if item > 0:
            for subitem in item:
                if subitem % 2 == 0:
                    result.append(subitem * 2)
                else:
                    result.append(subitem * 3)
    return result

# This is a comment
def another_function():
    pass
    """
    
    analyzer = ComplexityAnalyzer()
    metrics = analyzer.analyze(test_code)
    report = analyzer.generate_report(metrics)
    
    print("=== COMPLEXITY ANALYSIS REPORT ===")
    print(f"Overall Level: {report['overall_level']}")
    
    print("\n📊 Basic Metrics:")
    for key, value in report['basic_metrics'].items():
        print(f"  {key}: {value}")
    
    print("\n⚡ Complexity Metrics:")
    for key, metric in report['complexity_metrics'].items():
        print(f"  {key}: {metric['value']} - {metric['interpretation']}")
    
    print(f"\n📈 Duplication Rate: {report['duplication']['rate']}% - {report['duplication']['interpretation']}")
    
    print("\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    return report


if __name__ == "__main__":
    test_complexity_analyzer()