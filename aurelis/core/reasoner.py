from .ai import DeepSeekR1, O3Mini, CohereEmbeddings
from dataclasses import dataclass
from typing import List, Dict
import numpy as np
from scipy.spatial.distance import cosine

@dataclass
class ChainOfThought:
    steps: List[str]
    confidence: float
    model_name: str

@dataclass
class ReasoningResult:
    explanation: str
    chain_of_thought: List[ChainOfThought]
    confidence: float
    alternatives: List[str]
    sources: Dict[str, str]

class Reasoner:
    def __init__(self):
        self.deepseek = DeepSeekR1()
        self.o3mini = O3Mini()
        self.embeddings = CohereEmbeddings()

    def analyze(self, content: str, question: str) -> ReasoningResult:
        # Generate chain-of-thought from both models
        deepseek_cot = self._generate_cot(self.deepseek, content, question)
        o3mini_cot = self._generate_cot(self.o3mini, content, question)
        
        # Combine insights using embeddings
        combined_explanation = self._combine_insights([
            deepseek_cot.steps[-1],
            o3mini_cot.steps[-1]
        ])
        
        return ReasoningResult(
            explanation=combined_explanation,
            chain_of_thought=[deepseek_cot, o3mini_cot],
            confidence=(deepseek_cot.confidence + o3mini_cot.confidence) / 2,
            alternatives=self._generate_alternatives(content, question),
            sources={"DeepSeek": "reasoning", "O3-mini": "reasoning"}
        )

    def _generate_cot(self, model: any, content: str, question: str) -> ChainOfThought:
        prompt = f"""
        Analyze step by step:
        Content: {content}
        Question: {question}
        
        Provide:
        1. Step-by-step reasoning
        2. Confidence level (0-1)
        3. Final conclusion
        """
        
        response = model.generate(prompt)
        # Parse the response into steps
        # This is a simplified implementation
        steps = response.content.split("\n")
        return ChainOfThought(
            steps=steps,
            confidence=0.85,
            model_name=model.model_name
        )

    def _combine_insights(self, insights: List[str]) -> str:
        # Convert insights to embeddings
        embeddings = self.embeddings.embed(insights)
        
        # Calculate similarity and weights
        weights = self._calculate_weights(embeddings)
        
        # Combine insights based on weights
        # This is a simplified implementation
        return max(insights, key=lambda x: len(x))

    def _calculate_weights(self, embeddings: List[List[float]]) -> List[float]:
        weights = []
        for i, emb in enumerate(embeddings):
            similarities = [
                1 - cosine(emb, other_emb)
                for j, other_emb in enumerate(embeddings)
                if i != j
            ]
            weights.append(np.mean(similarities))
        return weights

    def _generate_alternatives(self, content: str, question: str) -> List[str]:
        prompt = f"Generate alternative approaches for: {question}"
        response = self.o3mini.generate(prompt)
        return response.content.split("\n")
