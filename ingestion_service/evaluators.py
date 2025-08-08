import re
from typing import Dict

class ChunkQualityEvaluator:
    """Lightweight heuristic evaluator for chunk quality.
    Replaces NUL-heavy or empty/garbage chunks and flags issues.
    """

    def __init__(self):
        self.min_characters = 40

    def evaluate_chunk(self, chunk: str) -> Dict[str, object]:
        text = chunk or ""
        has_content = len(text.strip()) >= self.min_characters
        # Detect excessive non-word characters
        non_word_ratio = 0.0
        if text:
            non_word_chars = len(re.findall(r"[^\w\s.,;:()\-]", text))
            non_word_ratio = non_word_chars / max(1, len(text))
        formatting_artifacts = non_word_ratio > 0.15
        grammatically_complete = text.strip().endswith(('.', '!', '?')) or len(text.split()) > 12

        # Binary score: 1 if passes all checks, else 0
        passes = int(has_content and not formatting_artifacts and grammatically_complete)

        explanation_bits = []
        if not has_content:
            explanation_bits.append("insufficient content length")
        if formatting_artifacts:
            explanation_bits.append("formatting artifacts detected")
        if not grammatically_complete:
            explanation_bits.append("chunk likely incomplete")
        explanation = ", ".join(explanation_bits) if explanation_bits else "chunk looks good"

        return {
            "score": passes,
            "explanation": explanation,
            "criteria": "chunk_quality",
            "model_used": "heuristic:v0"
        } 