"""
AI Handler for CodeOptima – Groq (Llama 3)
No billing required – truly free tier.
"""
import os
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from groq import Groq


@dataclass
class AIFixResult:
    """Result from AI fix request"""
    provider: str
    success: bool
    fixed_code: str
    explanation: str
    pros: List[str]
    cons_of_old: List[str]
    confidence: float
    latency: float
    tokens_used: int
    error: Optional[str] = None


class GroqAPIHandler:
    """Groq API integration for code fixing – free tier, no card required"""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.available = bool(self.api_key)
        if self.available:
            self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"

    def is_available(self) -> bool:
        return self.available

    def fix_code(self, code: str, issues_description: str) -> AIFixResult:
        start_time = time.time()
        if not self.available:
            return AIFixResult(
                provider="Groq",
                success=False,
                fixed_code="",
                explanation="",
                pros=[],
                cons_of_old=[],
                confidence=0.0,
                latency=0.0,
                tokens_used=0,
                error="GROQ_API_KEY not set in environment"
            )

        try:
            prompt = self._prepare_prompt(code, issues_description)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            content = response.choices[0].message.content
            fix_data = self._parse_response(content, code)
            latency = time.time() - start_time
            return AIFixResult(
                provider="Groq",
                success=True,
                fixed_code=fix_data["fixed_code"],
                explanation=fix_data["explanation"],
                pros=fix_data["pros"],
                cons_of_old=fix_data["cons_of_old"],
                confidence=0.9,
                latency=latency,
                tokens_used=response.usage.total_tokens if response.usage else 0
            )
        except Exception as e:
            return AIFixResult(
                provider="Groq",
                success=False,
                fixed_code="",
                explanation="",
                pros=[],
                cons_of_old=[],
                confidence=0.0,
                latency=time.time() - start_time,
                tokens_used=0,
                error=str(e)
            )

    def _prepare_prompt(self, code: str, issues: str) -> str:
        return f"""You are an expert Python developer specializing in code optimization. Rewrite the code below to be more efficient, Pythonic, and maintainable while preserving exact functionality and output.

CODE:
```python
{code}
```

INSTRUCTIONS:

1. **Performance Optimization:**
   - Improve time complexity using efficient algorithms (e.g., Sieve of Eratosthenes, sqrt prime checks, dynamic programming).
   - Optimize space complexity by using appropriate data structures (e.g., sets for lookups, generators for memory efficiency).
   - Remove unnecessary loops, redundant computations, and inefficient operations.

2. **Pythonic Best Practices:**
   - Follow PEP 8 style guidelines.
   - Use list comprehensions, generator expressions, and built-in functions (e.g., map, filter, zip) where appropriate.
   - Prefer idiomatic Python patterns over verbose code.
   - Use meaningful variable names and add docstrings if beneficial.

3. **Code Quality Improvements:**
   - Enhance readability and maintainability.
   - Eliminate code duplication.
   - Handle edge cases properly.
   - Use type hints if they improve clarity.
   - Avoid global variables and side effects where possible.

4. **General Optimizations:**
   - Choose optimal data structures (dicts for O(1) lookups, heaps for priority queues, etc.).
   - Minimize I/O operations and use buffering when applicable.
   - Leverage Python's standard library effectively (e.g., collections, itertools, functools).

Do NOT:
- Just add comments or change print statements to logging.
- Alter the exact output or behavior of the code.
- Introduce external dependencies unless absolutely necessary.

After the code, list:
PROS:
(specific benefits of the new code, including performance gains, readability improvements, etc.)

CONS_OF_OLD:
(specific problems of the original code, such as inefficiencies, non-Pythonic patterns, etc.)

Return format:
```python
# optimized code here
```
PROS:
...
CONS_OF_OLD:
...
"""

    def _parse_response(self, content: str, original_code: str) -> Dict:
        try:
            code_part = content
            if "```python" in content:
                code_part = content.split("```python", 1)[1]
                if "```" in code_part:
                    code_part = code_part.split("```", 1)[0]
            elif "```" in content:
                code_part = content.split("```", 1)[1]
                if "```" in code_part:
                    code_part = code_part.split("```", 1)[0]

            if "PROS:" in code_part:
                code_part = code_part.split("PROS:", 1)[0]
            fixed_code = code_part.strip()
            if not fixed_code:
                fixed_code = original_code

            pros = []
            cons_of_old = []

            if "PROS:" in content:
                pros_section = content.split("PROS:", 1)[1]
                if "CONS_OF_OLD:" in pros_section:
                    pros_section = pros_section.split("CONS_OF_OLD:", 1)[0]
                for line in pros_section.strip().splitlines():
                    line = line.strip().lstrip('-•*').strip()
                    if line and not line.upper().startswith("CONS"):
                        pros.append(line)

            if "CONS_OF_OLD:" in content:
                cons_section = content.split("CONS_OF_OLD:", 1)[1]
                for line in cons_section.strip().splitlines():
                    line = line.strip().lstrip('-•*').strip()
                    if line and not line.upper().startswith("PROS"):
                        cons_of_old.append(line)

            if not pros:
                pros = ["Optimized code (AI generated)"]
            if not cons_of_old:
                cons_of_old = ["Original code had performance issues"]

            return {
                "fixed_code": fixed_code,
                "explanation": "AI optimized the code for better performance.",
                "pros": pros,
                "cons_of_old": cons_of_old
            }
        except Exception as e:
            return {
                "fixed_code": original_code,
                "explanation": f"Failed to parse AI response: {e}",
                "pros": [],
                "cons_of_old": []
            }


UnifiedAIHandler = GroqAPIHandler
groq_handler = GroqAPIHandler()