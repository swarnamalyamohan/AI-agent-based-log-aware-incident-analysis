import faiss
import numpy as np


class LocalVectorStore:
    def __init__(self):
        self.index = None
        self.chunks = []
        self.dimension = None

    def build_index(self, embeddings: list[list[float]], chunks: list[dict]):
        embeddings_np = np.array(embeddings).astype("float32")

        self.dimension = embeddings_np.shape[1]
        self.index = faiss.IndexFlatIP(self.dimension)

        faiss.normalize_L2(embeddings_np)

        self.index.add(embeddings_np)
        self.chunks = chunks

        print(f"FAISS index created with {self.index.ntotal} vectors")

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        query_np = np.array([query_embedding]).astype("float32")
        faiss.normalize_L2(query_np)

        scores, indices = self.index.search(query_np, top_k)

        results = []

        for score, idx in zip(scores[0], indices[0]):
            chunk = self.chunks[idx].copy()
            chunk["score"] = float(score)
            results.append(chunk)

        return results