import re
import ast
import astunparse
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
import difflib
import time

from .ai_handler import groq_handler

from analyzer.static_rules import Issue, Category, Severity


@dataclass
class CodeFix:
    """Represents a single fix applied to code"""
    issue: Issue
    original_line: str
    fixed_line: str
    line_number: int
    confidence: float
    fix_type: str
    provider: str = "rule_based"
    explanation: str = ""
    pros: List[str] = field(default_factory=list)
    cons_of_old: List[str] = field(default_factory=list)
    ai_latency: float = 0.0
    tokens_used: int = 0


class AutoFixer:
    """Main class that automatically fixes code issues with AI integration"""
    
    def __init__(self):
        self.ai_handler = groq_handler   
        self.fix_rules = self._register_fix_rules()
        self.llm_stats = {
            "groq": {"calls": 0, "success": 0, "tokens": 0, "latency": 0},
            "rule_based": {"calls": 0, "success": 0, "tokens": 0, "latency": 0}
        }
    
    def _register_fix_rules(self) -> Dict[str, callable]:
        """Register all fix rules by issue type"""
        return {
            "SEC001": self._fix_hardcoded_password,
            "SEC002": self._fix_sql_injection,
            "SEC003": self._fix_dangerous_function,
            "PERF001": self._fix_string_concat_in_loop,
            "PERF002": self._fix_nested_loops,
            "BP001": self._fix_missing_docstring,
            "BP002": self._fix_bare_except,
            "BP003": self._fix_mutable_default,
            "STYLE001": self._fix_line_length,
            "STYLE002": self._fix_print_statement,
        }
    
    def fix_code_with_ai(self, code: str, issues: List[Issue], 
                         provider: str = "grok") -> Tuple[str, List[CodeFix], Dict]:
        """
        Always call Groq to optimize code.
        """
        # Build description – demand real optimization
        if issues:
            issue_desc = self._build_issue_description(issues)
        else:
            issue_desc = "No syntax errors, but the code is very inefficient. Please rewrite for maximum speed."
        
        issue_desc += "\n\nCRITICAL: Do NOT just add comments or change print to logging. Improve algorithms."
        
        # Call groq
        ai_result = self.ai_handler.fix_code(code, issue_desc)
        
        if ai_result.success:
            fixed_code = ai_result.fixed_code
            # If AI returned the same code or only trivial changes, try one more time
            if fixed_code.strip() == code.strip() or "logging" in fixed_code:
                aggressive_desc = "You did not optimize. Rewrite using Sieve of Eratosthenes for primes and remove the triple loop. Return only the new code."
                ai_result = self.ai_handler.fix_code(code, aggressive_desc)
                if ai_result.success and ai_result.fixed_code.strip() != code.strip():
                    fixed_code = ai_result.fixed_code
            
            fixes = self._generate_ai_fixes(code, fixed_code, issues, ai_result)
            self._update_llm_stats("groq", ai_result)
            return fixed_code, fixes, {
                "provider": provider,
                "explanation": ai_result.explanation,
                "pros": ai_result.pros,
                "cons_of_old": ai_result.cons_of_old,
                "confidence": ai_result.confidence,
                "latency": ai_result.latency,
                "tokens_used": ai_result.tokens_used
            }
        else:
            # Fallback to rule‑based fixes
            fixed_code, fixes = self._apply_rule_based_fixes(code, issues)
            return fixed_code, fixes, {
                "provider": "rule_based",
                "explanation": "AI unavailable – using basic fixes",
                "error": ai_result.error,
                "pros": [],
                "cons_of_old": ["Original code is slow, but AI could not optimize"]
            }
    
    def _build_issue_description(self, issues: List[Issue]) -> str:
        """Build detailed description of issues for AI"""
        if not issues:
            return "No issues found – still please optimize for speed."
        
        desc = "Found the following code issues to fix:\n\n"
        by_category = {}
        for issue in issues:
            cat = issue.category.value
            by_category.setdefault(cat, []).append(issue)
        
        for category, cat_issues in by_category.items():
            desc += f"\n{category} ({len(cat_issues)} issues):\n"
            for issue in cat_issues:
                desc += f"  - Line {issue.line}: {issue.title}\n"
                desc += f"    Description: {issue.description}\n"
                desc += f"    Severity: {issue.severity.value}\n"
                desc += f"    Suggestion: {issue.suggestion}\n"
        return desc
    
    def _apply_rule_based_fixes(self, code: str, issues: List[Issue]) -> Tuple[str, List[CodeFix]]:
        """Apply rule-based fixes (fallback)"""
        lines = code.split('\n')
        applied_fixes = []
        sorted_issues = sorted(issues, key=lambda x: x.line, reverse=True)
        
        for issue in sorted_issues:
            if issue.rule_id in self.fix_rules:
                line_num = issue.line - 1
                if 0 <= line_num < len(lines):
                    original_line = lines[line_num]
                    fix_func = self.fix_rules[issue.rule_id]
                    fixed_line, fix_applied, fix_type = fix_func(original_line, issue)
                    if fix_applied and fixed_line != original_line:
                        code_fix = CodeFix(
                            issue=issue,
                            original_line=original_line,
                            fixed_line=fixed_line,
                            line_number=issue.line,
                            confidence=0.8,
                            fix_type=fix_type,
                            provider="rule_based"
                        )
                        applied_fixes.append(code_fix)
                        lines[line_num] = fixed_line
        
        fixed_code = '\n'.join(lines)
        fixed_code = self._add_required_imports(fixed_code, applied_fixes)
        self._update_llm_stats("rule_based", None)
        return fixed_code, applied_fixes
    
    def apply_rule_based_fixes(self, code: str, issues: List[Issue]) -> Tuple[str, List[CodeFix], Dict]:
        """Apply only rule-based fixes without calling AI."""
        fixed_code, fixes = self._apply_rule_based_fixes(code, issues)
        details = {
            "provider": "rule_based",
            "explanation": "Rule-based fixes applied without AI.",
            "pros": [f"Applied {len(fixes)} rule-based fix(es)."] if fixes else [],
            "cons_of_old": [issue.title for issue in issues] if issues else []
        }
        return fixed_code, fixes, details
    
    def _generate_ai_fixes(self, original_code: str, fixed_code: str, 
                          issues: List[Issue], ai_result) -> List[CodeFix]:
        """Generate CodeFix objects from AI-fixed code"""
        applied_fixes = []
        original_lines = original_code.split('\n')
        fixed_lines = fixed_code.split('\n')
        
        for i, (orig_line, fixed_line) in enumerate(zip(original_lines, fixed_lines)):
            if orig_line != fixed_line:
                matching_issue = None
                for issue in issues:
                    if issue.line == i + 1:
                        matching_issue = issue
                        break
                if matching_issue:
                    code_fix = CodeFix(
                        issue=matching_issue,
                        original_line=orig_line,
                        fixed_line=fixed_line,
                        line_number=i+1,
                        confidence=ai_result.confidence,
                        fix_type=matching_issue.category.value.lower(),
                        provider=ai_result.provider,
                        explanation=ai_result.explanation,
                        pros=ai_result.pros,
                        cons_of_old=ai_result.cons_of_old,
                        ai_latency=ai_result.latency,
                        tokens_used=ai_result.tokens_used
                    )
                    applied_fixes.append(code_fix)
        return applied_fixes
    
    def _update_llm_stats(self, provider: str, result: Optional[Any]):
        if provider in self.llm_stats:
            self.llm_stats[provider]["calls"] += 1
            if result and hasattr(result, 'success') and result.success:
                self.llm_stats[provider]["success"] += 1
                self.llm_stats[provider]["tokens"] += getattr(result, 'tokens_used', 0)
                self.llm_stats[provider]["latency"] += getattr(result, 'latency', 0)
    
    # ========== Rule implementations (keep as they were) ==========
    def _fix_hardcoded_password(self, line: str, issue: Issue) -> Tuple[str, bool, str]:
        match = re.search(r'(\w+)\s*=\s*["\'][^"\']+["\']', line)
        if match:
            var_name = match.group(1)
            new_line = re.sub(r'=\s*["\'][^"\']+["\']', f'= os.getenv("{var_name.upper()}")', line)
            return new_line, True, "security"
        return line, False, ""
    
    def _fix_sql_injection(self, line: str, issue: Issue) -> Tuple[str, bool, str]:
        if '+' in line and any(kw in line.upper() for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
            new_line = line + "  # WARNING: Use parameterized queries"
            return new_line, True, "security"
        return line, False, ""
    
    def _fix_dangerous_function(self, line: str, issue: Issue) -> Tuple[str, bool, str]:
        if 'eval(' in line:
            return line.replace('eval(', 'ast.literal_eval('), True, "security"
        elif 'exec(' in line:
            return "# " + line + "  # DANGEROUS: exec() removed", True, "security"
        return line, False, ""
    
    def _fix_string_concat_in_loop(self, line: str, issue: Issue) -> Tuple[str, bool, str]:
        if '+=' in line and ('"' in line or "'" in line):
            return line + "  # PERF: Use ''.join()", True, "performance"
        return line, False, ""
    
    def _fix_nested_loops(self, line: str, issue: Issue) -> Tuple[str, bool, str]:
        if 'for ' in line or 'while ' in line:
            return line + "  # PERF: Consider optimizing nested loops", True, "performance"
        return line, False, ""
    
    def _fix_missing_docstring(self, line: str, issue: Issue) -> Tuple[str, bool, str]:
        if 'def ' in line:
            return line, True, "docstring"
        return line, False, ""
    
    def _fix_bare_except(self, line: str, issue: Issue) -> Tuple[str, bool, str]:
        if 'except:' in line:
            return line.replace('except:', 'except Exception:'), True, "best_practice"
        return line, False, ""
    
    def _fix_mutable_default(self, line: str, issue: Issue) -> Tuple[str, bool, str]:
        if '=[]' in line or '={}' in line:
            new_line = line.replace('=[]', '=None').replace('={}', '=None')
            return new_line + "  # Then: items = items if items is not None else []", True, "best_practice"
        return line, False, ""
    
    def _fix_line_length(self, line: str, issue: Issue) -> Tuple[str, bool, str]:
        if len(line) > 79:
            return line + "  # STYLE: Line too long", True, "style"
        return line, False, ""
    
    def _fix_print_statement(self, line: str, issue: Issue) -> Tuple[str, bool, str]:
        if 'print(' in line and not line.strip().startswith('#'):
            return line.replace('print(', 'logging.info('), True, "style"
        return line, False, ""
    
    def _add_required_imports(self, code: str, fixes: List[CodeFix]) -> str:
        imports_to_add = []
        lines = code.split('\n')
        for fix in fixes:
            if fix.fix_type == "security" and 'os.getenv' in fix.fixed_line:
                imports_to_add.append('import os')
            elif fix.fix_type == "security" and 'ast.literal_eval' in fix.fixed_line:
                imports_to_add.append('import ast')
            elif fix.fix_type == "style" and 'logging.info' in fix.fixed_line:
                imports_to_add.append('import logging')
        imports_to_add = list(set(imports_to_add))
        if imports_to_add:
            for imp in imports_to_add:
                if imp not in code:
                    for i, line in enumerate(lines):
                        if line.strip() and not line.strip().startswith(('import ', 'from ', '#')):
                            lines.insert(i, imp)
                            break
        return '\n'.join(lines)
    
    def get_diff(self, original: str, fixed: str) -> str:
        return ''.join(difflib.unified_diff(original.splitlines(keepends=True), fixed.splitlines(keepends=True), fromfile='Original', tofile='Fixed', lineterm=''))
    
    def get_llm_stats(self) -> Dict:
        return self.llm_stats


# Create a global instance
auto_fixer = AutoFixer()
