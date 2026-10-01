import random
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

try:
    from rank_bm25 import BM25Plus
except ImportError:
    BM25Plus = None
    print("Warning: Library 'rank_bm25' tidak ditemukan. Metode BM25+ tidak akan berfungsi.")

def retrieve_random(texts, k=5, seed=None):
    """Random-k baseline. Bila seed diberikan, hasilnya dapat direproduksi."""
    rng = random.Random(seed) if seed is not None else random
    return rng.sample(texts, min(k, len(texts)))

def retrieve_dense(query_embedding, doc_embeddings, texts, k=5):
    similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
    top_indices = np.argsort(similarities)[-k:][::-1]
    return [texts[i] for i in top_indices]

# MODIFIKASI: Menerima 'centroid_embedding' langsung
def retrieve_centroid(centroid_embedding, doc_embeddings, texts, k=5):
    similarities = cosine_similarity(centroid_embedding, doc_embeddings)[0]
    top_indices = np.argsort(similarities)[-k:][::-1]
    return [texts[i] for i in top_indices]

def retrieve_bm25(query_text, bm25_model, texts, k=5):
    if bm25_model is None:
        raise ValueError("Model BM25 belum diinisialisasi.")
    tokenized_query = str(query_text).lower().split()
    return bm25_model.get_top_n(tokenized_query, texts, n=k)

# MODIFIKASI: Menerima 'centroid_embedding' secara langsung
def retrieve_hybrid_early_fusion(query_embedding, centroid_embedding, doc_embeddings, texts, k=5, alpha=0.5):
    """Vector Interpolation (Early Fusion)"""
    hybrid_vector = (alpha * query_embedding) + ((1 - alpha) * centroid_embedding)
    similarities = cosine_similarity(hybrid_vector, doc_embeddings)[0]
    top_indices = np.argsort(similarities)[-k:][::-1]
    return [texts[i] for i in top_indices]