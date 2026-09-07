"""
Vector store — cosine similarity search over numpy embedding matrix.
No external vector DB needed.
"""
import numpy as np
from typing import Optional


class VectorStore:
    def __init__(self):
        self.texts: list[str] = []
        self.embeddings: Optional[np.ndarray] = None

    def add(self, texts: list[str], embeddings: np.ndarray) -> None:
        self.texts.extend(texts)
        if self.embeddings is None:
            self.embeddings = embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[str]:
        if self.embeddings is None or len(self.texts) == 0:
            return []
        # Cosine similarity
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        normed = self.embeddings / (norms + 1e-10)
        q_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        scores = normed @ q_norm
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [self.texts[i] for i in top_idx]

    def clear(self) -> None:
        self.texts = []
        self.embeddings = None

    def __len__(self) -> int:
        return len(self.texts)
