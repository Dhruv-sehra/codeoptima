"""
Code Scoring System for CodeOptima
Evaluates code quality and assigns scores
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from analyzer.static_rules import Issue, Category, Severity
from analyzer.complexity_analyzer import ComplexityMetrics, ComplexityLevel


class ScoreCategory(Enum):
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    BEST_PRACTICES = "BEST_PRACTICES"
    COMPLEXITY = "COMPLEXITY"
    OVERALL = "OVERALL"


@dataclass
class CategoryScore:
    """Score for a specific category"""
    category: ScoreCategory
    score: float  # 0-100
    weight: float
    issues_found: int
    max_issues: int


@dataclass
class CodeScore:
    """Complete scoring result"""
    overall_score: float  # 0-100
    category_scores: Dict[str, CategoryScore]
    grade: str  # A, B, C, D, F
    timestamp: datetime
    passed_threshold: bool


class CodeScoringSystem:
    """Main scoring system that combines all analyses"""
    
    def __init__(self):
        self.weights = {
            ScoreCategory.SECURITY: 0.30,      # 30% weight
            ScoreCategory.PERFORMANCE: 0.20,   # 20% weight
            ScoreCategory.BEST_PRACTICES: 0.25, # 25% weight
            ScoreCategory.COMPLEXITY: 0.25      # 25% weight
        }
        
        self.grade_thresholds = {
            'A': 90,
            'B': 80,
            'C': 70,
            'D': 60,
            'F': 0
        }
        
        self.pass_threshold = 70  # Minimum passing score
    
    def calculate_score(self, 
                       issues: List[Issue],
                       complexity_metrics: ComplexityMetrics,
                       complexity_level: ComplexityLevel) -> CodeScore:
        """
        Calculate overall score based on issues and complexity
        """
        # Calculate category scores
        security_score = self._calculate_security_score(issues)
        performance_score = self._calculate_performance_score(issues)
        practices_score = self._calculate_practices_score(issues)
        complexity_score = self._calculate_complexity_score(
            complexity_metrics, complexity_level
        )
        
        # Create category score objects
        category_scores = {
            ScoreCategory.SECURITY.value: CategoryScore(
                category=ScoreCategory.SECURITY,
                score=security_score,
                weight=self.weights[ScoreCategory.SECURITY],
                issues_found=len([i for i in issues if i.category.value == "SECURITY"]),
                max_issues=5  # Threshold for severe issues
            ),
            ScoreCategory.PERFORMANCE.value: CategoryScore(
                category=ScoreCategory.PERFORMANCE,
                score=performance_score,
                weight=self.weights[ScoreCategory.PERFORMANCE],
                issues_found=len([i for i in issues if i.category.value == "PERFORMANCE"]),
                max_issues=10
            ),
            ScoreCategory.BEST_PRACTICES.value: CategoryScore(
                category=ScoreCategory.BEST_PRACTICES,
                score=practices_score,
                weight=self.weights[ScoreCategory.BEST_PRACTICES],
                issues_found=len([i for i in issues if i.category.value == "BEST_PRACTICE"]),
                max_issues=15
            ),
            ScoreCategory.COMPLEXITY.value: CategoryScore(
                category=ScoreCategory.COMPLEXITY,
                score=complexity_score,
                weight=self.weights[ScoreCategory.COMPLEXITY],
                issues_found=0,  # Not based on issues
                max_issues=0
            )
        }
        
        # Calculate weighted overall score
        overall_score = 0
        for cat_score in category_scores.values():
            overall_score += cat_score.score * cat_score.weight
        
        # Ensure within bounds
        overall_score = max(0, min(100, overall_score))
        
        # Determine grade
        grade = self._determine_grade(overall_score)
        
        # Check if passes threshold
        passed = overall_score >= self.pass_threshold
        
        return CodeScore(
            overall_score=round(overall_score, 1),
            category_scores=category_scores,
            grade=grade,
            timestamp=datetime.now(),
            passed_threshold=passed
        )
    
    def _calculate_security_score(self, issues: List[Issue]) -> float:
        """Calculate security score (critical issues heavily penalized)"""
        security_issues = [i for i in issues if i.category.value == "SECURITY"]
        
        if not security_issues:
            return 100.0
        
        # Different penalties based on severity
        penalty = 0
        for issue in security_issues:
            if issue.severity.value == "CRITICAL":
                penalty += 40
            elif issue.severity.value == "HIGH":
                penalty += 25
            elif issue.severity.value == "MEDIUM":
                penalty += 10
            else:
                penalty += 5
        
        # Cap penalty at 100
        penalty = min(penalty, 100)
        
        return max(0, 100 - penalty)
    
    def _calculate_performance_score(self, issues: List[Issue]) -> float:
        """Calculate performance score"""
        perf_issues = [i for i in issues if i.category.value == "PERFORMANCE"]
        
        if not perf_issues:
            return 100.0
        
        # Each performance issue deducts 15 points
        penalty = len(perf_issues) * 15
        
        return max(0, 100 - penalty)
    
    def _calculate_practices_score(self, issues: List[Issue]) -> float:
        """Calculate best practices score"""
        practice_issues = [i for i in issues if i.category.value == "BEST_PRACTICE"]
        
        if not practice_issues:
            return 100.0
        
        # Each practice issue deducts 8 points
        penalty = len(practice_issues) * 8
        
        return max(0, 100 - penalty)
    
    def _calculate_complexity_score(self, 
                                   metrics: ComplexityMetrics,
                                   level: ComplexityLevel) -> float:
        """Calculate complexity score based on metrics"""
        score = 100
        
        # Penalize based on complexity level
        if level == ComplexityLevel.VERY_HIGH:
            score -= 60
        elif level == ComplexityLevel.HIGH:
            score -= 40
        elif level == ComplexityLevel.MEDIUM:
            score -= 20
        elif level == ComplexityLevel.LOW:
            score -= 10
        
        # Additional penalties for specific metrics
        if metrics.maintainability_index < 50:
            score -= 20
        elif metrics.maintainability_index < 70:
            score -= 10
        
        if metrics.cyclomatic_complexity > 10:
            score -= 15
        elif metrics.cyclomatic_complexity > 5:
            score -= 5
        
        if metrics.duplication_rate > 20:
            score -= 20
        elif metrics.duplication_rate > 10:
            score -= 10
        
        return max(0, score)
    
    def _determine_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        for grade, threshold in self.grade_thresholds.items():
            if score >= threshold:
                return grade
        return "F"
    
    def generate_score_report(self, score: CodeScore) -> Dict[str, Any]:
        """Generate a detailed score report"""
        return {
            'overall': {
                'score': score.overall_score,
                'grade': score.grade,
                'passed': score.passed_threshold,
                'timestamp': score.timestamp.isoformat()
            },
            'categories': {
                cat: {
                    'score': cat_score.score,
                    'weight': cat_score.weight,
                    'weighted_contribution': round(cat_score.score * cat_score.weight, 1),
                    'issues_found': cat_score.issues_found,
                    'max_issues': cat_score.max_issues,
                    'status': self._get_category_status(cat_score)
                }
                for cat, cat_score in score.category_scores.items()
            },
            'interpretation': self._interpret_score(score),
            'improvement_suggestions': self._generate_improvements(score)
        }
    
    def _get_category_status(self, cat_score: CategoryScore) -> str:
        """Get status text for a category"""
        if cat_score.score >= 90:
            return "Excellent"
        elif cat_score.score >= 75:
            return "Good"
        elif cat_score.score >= 60:
            return "Needs Improvement"
        else:
            return "Poor"
    
    def _interpret_score(self, score: CodeScore) -> Dict[str, str]:
        """Provide interpretation of the overall score"""
        interpretations = {
            'A': "Excellent code quality. Production ready with minimal issues.",
            'B': "Good code quality. Ready for production with minor improvements needed.",
            'C': "Fair code quality. Needs refactoring before production deployment.",
            'D': "Poor code quality. Significant refactoring required.",
            'F': "Very poor code quality. Major security or structural issues present."
        }
        
        return {
            'grade_meaning': interpretations.get(score.grade, "Unknown grade"),
            'recommended_action': self._get_recommended_action(score),
            'next_steps': self._get_next_steps(score)
        }
    
    def _get_recommended_action(self, score: CodeScore) -> str:
        """Get recommended action based on score"""
        if score.overall_score >= 90:
            return "Code is production ready. No urgent changes needed."
        elif score.overall_score >= 75:
            return "Address minor issues before production deployment."
        elif score.overall_score >= 60:
            return "Moderate refactoring recommended before production."
        else:
            return "Major refactoring required. Do not deploy to production."
    
    def _get_next_steps(self, score: CodeScore) -> List[str]:
        """Get actionable next steps"""
        steps = []
        
        # Check each category
        for cat_name, cat_score in score.category_scores.items():
            if cat_score.score < 60:
                if cat_name == "SECURITY":
                    steps.append("🔐 Fix all security issues immediately")
                elif cat_name == "PERFORMANCE":
                    steps.append("⚡ Optimize performance-critical sections")
                elif cat_name == "BEST_PRACTICES":
                    steps.append("📚 Address best practice violations")
                elif cat_name == "COMPLEXITY":
                    steps.append("🧩 Refactor to reduce code complexity")
        
        # Add general steps based on overall score
        if score.overall_score < 70:
            steps.append("🔄 Run analysis again after making changes")
        
        if len(steps) == 0:
            steps.append("✅ Continue maintaining current code quality standards")
        
        return steps
    
    def _generate_improvements(self, score: CodeScore) -> List[Dict[str, Any]]:
        """Generate specific improvement suggestions"""
        improvements = []
        
        for cat_name, cat_score in score.category_scores.items():
            if cat_score.score < 80:
                improvement = {
                    'category': cat_name,
                    'current_score': cat_score.score,
                    'target_score': min(100, cat_score.score + 20),
                    'priority': 'HIGH' if cat_score.score < 60 else 'MEDIUM',
                    'actions': self._get_category_actions(cat_name, cat_score)
                }
                improvements.append(improvement)
        
        return improvements
    
    def _get_category_actions(self, category: str, cat_score: CategoryScore) -> List[str]:
        """Get specific actions for a category"""
        actions = []
        
        if category == "SECURITY":
            actions = [
                "Review all string concatenation in database queries",
                "Replace hardcoded credentials with environment variables",
                "Remove eval() and exec() calls",
                "Add input validation for user inputs"
            ]
        elif category == "PERFORMANCE":
            actions = [
                "Replace string concatenation in loops with join()",
                "Reduce nested loop depth",
                "Use list comprehensions where appropriate",
                "Remove unnecessary data copying"
            ]
        elif category == "BEST_PRACTICES":
            actions = [
                "Add docstrings to all functions and classes",
                "Replace bare except clauses with specific exceptions",
                "Fix mutable default arguments",
                "Add type hints to function signatures"
            ]
        elif category == "COMPLEXITY":
            actions = [
                "Break large functions into smaller ones",
                "Reduce nested conditionals",
                "Extract duplicate code into functions",
                "Simplify complex boolean expressions"
            ]
        
        return actions[:3]  # Return top 3 actions
    
    def save_score_history(self, score: CodeScore, filename: str = "scores.json"):
        """Save score to history file"""
        try:
            # Load existing history
            try:
                with open(filename, 'r') as f:
                    history = json.load(f)
            except FileNotFoundError:
                history = []
            
            # Add new score
            score_data = {
                'timestamp': score.timestamp.isoformat(),
                'overall_score': score.overall_score,
                'grade': score.grade,
                'passed': score.passed_threshold,
                'category_scores': {
                    cat: {
                        'score': cs.score,
                        'issues_found': cs.issues_found
                    }
                    for cat, cs in score.category_scores.items()
                }
            }
            
            history.append(score_data)
            
            # Keep only last 100 scores
            if len(history) > 100:
                history = history[-100:]
            
            # Save back to file
            with open(filename, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save score history: {e}")


# Test function
def test_scoring_system():
    """Test the scoring system"""
    # Create mock issues
    from analyzer.static_rules import Issue, Category, Severity
    
    mock_issues = [
        Issue(
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            title="SQL Injection",
            description="String concatenation in SQL",
            line=10,
            suggestion="Use parameterized queries",
            rule_id="SEC002"
        ),
        Issue(
            category=Category.PERFORMANCE,
            severity=Severity.MEDIUM,
            title="String concatenation in loop",
            description="Inefficient string building",
            line=15,
            suggestion="Use join()",
            rule_id="PERF001"
        ),
        Issue(
            category=Category.BEST_PRACTICE,
            severity=Severity.LOW,
            title="Missing docstring",
            description="Function missing documentation",
            line=5,
            suggestion="Add docstring",
            rule_id="BP001"
        )
    ]
    
    # Create mock complexity metrics
    mock_metrics = ComplexityMetrics(
        lines_of_code=150,
        comment_lines=20,
        blank_lines=15,
        function_count=8,
        class_count=2,
        cyclomatic_complexity=12.5,
        maintainability_index=65.0,
        halstead_volume=1250.5,
        cognitive_complexity=18,
        duplication_rate=8.5
    )
    
    mock_level = ComplexityLevel.MEDIUM
    
    # Calculate score
    scorer = CodeScoringSystem()
    score = scorer.calculate_score(mock_issues, mock_metrics, mock_level)
    report = scorer.generate_score_report(score)
    
    print("=== CODE SCORING REPORT ===")
    print(f"Overall Score: {report['overall']['score']}/100")
    print(f"Grade: {report['overall']['grade']}")
    print(f"Passed: {report['overall']['passed']}")
    
    print("\n📈 Category Breakdown:")
    for cat, data in report['categories'].items():
        print(f"  {cat}: {data['score']}/100 ({data['status']})")
        print(f"    Weight: {data['weight']*100}%")
        print(f"    Issues: {data['issues_found']}/{data['max_issues']}")
    
    print(f"\n📝 Interpretation:")
    print(f"  {report['interpretation']['grade_meaning']}")
    print(f"  Recommended: {report['interpretation']['recommended_action']}")
    
    print("\n🎯 Next Steps:")
    for step in report['interpretation']['next_steps']:
        print(f"  • {step}")
    
    print("\n🔧 Improvement Areas:")
    for imp in report['improvement_suggestions']:
        print(f"  {imp['category']} (Score: {imp['current_score']} → Target: {imp['target_score']})")
        print(f"    Priority: {imp['priority']}")
        for action in imp['actions']:
            print(f"    • {action}")
    
    return score


if __name__ == "__main__":
    test_scoring_system()