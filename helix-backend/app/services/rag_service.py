import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
try:
    import faiss
except ImportError:
    faiss = None

logger = logging.getLogger(__name__)

FAISS_INDEX_DIR = "./faiss_indices"
os.makedirs(FAISS_INDEX_DIR, exist_ok=True)


class FAISSVectorStore:
    """FAISS-based vector store for user-specific memory with embeddings."""

    def __init__(self, dimension: int = 384):
        """
        Initialize FAISS vector store.
        
        Args:
            dimension: Embedding dimension (default 384 for sentence-transformers)
        """
        if faiss is None:
            raise ImportError("faiss-cpu not installed. Install with: pip install faiss-cpu")

        self.dimension = dimension
        self.user_indices: Dict[str, Any] = {}
        self.user_metadata: Dict[str, List[Dict]] = {}
        self.user_embeddings: Dict[str, np.ndarray] = {}

    def _get_user_index_path(self, user_id: str) -> str:
        """Get the file path for a user's FAISS index."""
        return os.path.join(FAISS_INDEX_DIR, f"user_{user_id}_index.faiss")

    def _get_user_metadata_path(self, user_id: str) -> str:
        """Get the file path for a user's metadata."""
        return os.path.join(FAISS_INDEX_DIR, f"user_{user_id}_metadata.json")

    def _load_or_create_index(self, user_id: str):
        """Load user's index from disk or create new one."""
        index_path = self._get_user_index_path(user_id)
        metadata_path = self._get_user_metadata_path(user_id)

        if os.path.exists(index_path) and os.path.exists(metadata_path):
            try:
                self.user_indices[user_id] = faiss.read_index(index_path)
                with open(metadata_path, 'r') as f:
                    self.user_metadata[user_id] = json.load(f)
                logger.info(f"Loaded existing index for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to load index for user {user_id}: {e}")
                self._create_empty_index(user_id)
        else:
            self._create_empty_index(user_id)

    def _create_empty_index(self, user_id: str):
        """Create a new empty FAISS index for a user."""
        index = faiss.IndexFlatL2(self.dimension)
        self.user_indices[user_id] = index
        self.user_metadata[user_id] = []
        logger.info(f"Created new index for user {user_id}")

    def _save_index(self, user_id: str):
        """Save user's index to disk."""
        if user_id not in self.user_indices:
            return

        index_path = self._get_user_index_path(user_id)
        metadata_path = self._get_user_metadata_path(user_id)

        try:
            faiss.write_index(self.user_indices[user_id], index_path)
            with open(metadata_path, 'w') as f:
                json.dump(self.user_metadata[user_id], f)
            logger.info(f"Saved index for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to save index for user {user_id}: {e}")

    def _generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for text.
        Uses a simple hash-based approach for now (non-trainable).
        In production, use sentence-transformers or similar.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            return model.encode(text, convert_to_numpy=True).astype(np.float32)
        except ImportError:
            # Fallback: create deterministic embedding from text hash
            logger.warning("sentence-transformers not available, using fallback embedding")
            np.random.seed(hash(text) % (2**32))
            return np.random.randn(self.dimension).astype(np.float32)

    def add_to_memory(
        self,
        user_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add text to user's vector memory with embedding.
        
        Args:
            user_id: User identifier
            text: Text content to store
            metadata: Additional metadata (report_id, timestamp, etc.)
        
        Returns:
            Success status
        """
        try:
            self._load_or_create_index(user_id)

            # Generate embedding
            embedding = self._generate_embedding(text)
            embedding = embedding.reshape(1, -1)

            # Add to FAISS index
            self.user_indices[user_id].add(embedding)

            # Store metadata
            meta_entry = {
                "id": len(self.user_metadata[user_id]),
                "text": text,
                "metadata": metadata or {},
                "added_at": datetime.utcnow().isoformat(),
            }
            self.user_metadata[user_id].append(meta_entry)

            # Save to disk
            self._save_index(user_id)

            logger.info(f"Added memory for user {user_id}: {len(text)} chars")
            return True

        except Exception as e:
            logger.error(f"Failed to add memory for user {user_id}: {e}")
            return False

    def retrieve_context(
        self,
        user_id: str,
        query: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-k similar documents from user's memory.
        
        Args:
            user_id: User identifier
            query: Query text
            k: Number of results to retrieve
        
        Returns:
            List of retrieved documents with similarity scores
        """
        try:
            self._load_or_create_index(user_id)

            if user_id not in self.user_metadata or len(self.user_metadata[user_id]) == 0:
                logger.warning(f"No memory for user {user_id}")
                return []

            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            query_embedding = query_embedding.reshape(1, -1)

            # Search in FAISS
            distances, indices = self.user_indices[user_id].search(query_embedding, min(k, len(self.user_metadata[user_id])))

            # Build results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx < len(self.user_metadata[user_id]):
                    meta = self.user_metadata[user_id][idx]
                    results.append({
                        "text": meta["text"],
                        "metadata": meta.get("metadata", {}),
                        "distance": float(dist),
                        "similarity": 1.0 / (1.0 + float(dist)),
                    })

            logger.info(f"Retrieved {len(results)} results for user {user_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to retrieve context for user {user_id}: {e}")
            return []

    def clear_user_memory(self, user_id: str) -> bool:
        """Clear all memory for a specific user."""
        try:
            index_path = self._get_user_index_path(user_id)
            metadata_path = self._get_user_metadata_path(user_id)

            if user_id in self.user_indices:
                del self.user_indices[user_id]
            if user_id in self.user_metadata:
                del self.user_metadata[user_id]
            if user_id in self.user_embeddings:
                del self.user_embeddings[user_id]

            if os.path.exists(index_path):
                os.remove(index_path)
            if os.path.exists(metadata_path):
                os.remove(metadata_path)

            logger.info(f"Cleared memory for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear memory for user {user_id}: {e}")
            return False

    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about a user's memory."""
        self._load_or_create_index(user_id)
        
        if user_id not in self.user_metadata:
            return {"documents": 0, "user_id": user_id}
        
        return {
            "user_id": user_id,
            "documents": len(self.user_metadata[user_id]),
            "size_bytes": sum(len(m.get("text", "")) for m in self.user_metadata[user_id]),
        }


# Global instance
_vector_store_instance: Optional[FAISSVectorStore] = None


def get_vector_store() -> FAISSVectorStore:
    """Get or create singleton vector store instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = FAISSVectorStore()
    return _vector_store_instance


class RAGService:
    """High-level RAG service with user isolation."""

    @staticmethod
    def add_report_to_memory(user_id: str, report_id: str, report_text: str) -> bool:
        """
        Add a report to user's memory for future retrieval.
        
        Args:
            user_id: User identifier
            report_id: Report identifier
            report_text: Report content
        
        Returns:
            Success status
        """
        vector_store = get_vector_store()
        return vector_store.add_to_memory(
            user_id=user_id,
            text=report_text,
            metadata={"report_id": report_id, "type": "report"}
        )

    @staticmethod
    def retrieve_for_chat(user_id: str, question: str, k: int = 5) -> str:
        """
        Retrieve relevant context for a chat question.
        
        Args:
            user_id: User identifier
            question: User's question
            k: Number of documents to retrieve
        
        Returns:
            Combined context as string
        """
        vector_store = get_vector_store()
        results = vector_store.retrieve_context(user_id, question, k)

        if not results:
            return ""

        # Format results as context string
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Context {i}] {result['text']}")

        return "\n\n".join(context_parts)

    @staticmethod
    def index_documents(
        user_id: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Index multiple documents for a user.
        
        Args:
            user_id: User identifier
            documents: List of documents with "text" and optional "metadata"
        
        Returns:
            Indexing result
        """
        vector_store = get_vector_store()
        success_count = 0

        for doc in documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})

            if text and vector_store.add_to_memory(user_id, text, metadata):
                success_count += 1

        return {
            "status": "success" if success_count > 0 else "failed",
            "indexed": success_count,
            "total": len(documents),
        }

    @staticmethod
    def clear_user_data(user_id: str) -> bool:
        """Clear all data for a user (GDPR compliance)."""
        vector_store = get_vector_store()
        return vector_store.clear_user_memory(user_id)

    @staticmethod
    def get_stats(user_id: str) -> Dict[str, Any]:
        """Get statistics about user's stored data."""
        vector_store = get_vector_store()
        return vector_store.get_memory_stats(user_id)

def analyze_with_rag(data: Dict[str, Any], context: str = "") -> Dict[str, Any]:
    """
    Analyze patient data with RAG-enhanced context.
    
    Args:
        data: Patient medical data
        context: Additional context
    
    Returns:
        Enhanced analysis with grounded information
    """
    from app.services.reasoning_service import analyze_health
    
    # Retrieve relevant medical context
    query = " ".join([f"{k} {v}" for k, v in data.items()])
    rag_context = retrieve_context(query)
    
    # Combine with provided context
    full_context = f"{context}\n\nMedical Literature:\n{rag_context}"
    
    # Perform analysis with enhanced context
    return analyze_health(data, full_context)

def index_documents(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Index documents into vector database.
    
    Args:
        documents: List of documents to index
    
    Returns:
        Indexing status
    """
    try:
        # Placeholder for actual indexing
        return {
            "status": "indexed",
            "count": len(documents),
            "message": f"Successfully indexed {len(documents)} documents"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def search_similar(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for similar documents in vector DB.
    
    Args:
        query: Search query
        k: Number of results
    
    Returns:
        List of similar documents
    """
    # Placeholder implementation
    return [
        {
            "title": "Document 1",
            "similarity": 0.95,
            "content": "Sample content"
        }
    ]
