from sentence_transformers import SentenceTransformer
from app.core.config import settings

# Load model lazily to avoid loading it on API startup if it's only needed in workers
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model

def get_embedding(text: str) -> list[float]:
    model = get_model()
    # encode returns a numpy array, convert to list of floats for pgvector
    return model.encode(text).tolist()

def get_embeddings(texts: list[str]) -> list[list[float]]:
    model = get_model()
    return model.encode(texts).tolist()
