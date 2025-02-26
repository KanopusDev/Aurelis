import faiss
import numpy as np
from typing import List, Dict, Optional, Union
import json
import os
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from ..utils.config import Config
import logging

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: str
    metadata: Dict

class VectorDB:
    def __init__(self, db_path: str = None):
        """Initialize the vector database.
        
        Args:
            db_path: Optional path to the database directory.
                If None, the path from Config will be used.
        """
        if db_path is None:
            db_path = Config.get_db_path()
        
        self.db_path = Path(db_path)
        try:
            self.db_path.mkdir(exist_ok=True, parents=True)
        except Exception as e:
            logger.error(f"Failed to create database directory: {str(e)}")
            raise
        
        self.index_path = self.db_path / "faiss_index"
        self.messages_path = self.db_path / "messages.json"
        self.dimension_path = self.db_path / "dimension.txt"
        
        # Default dimension for embeddings - will be updated when first vector is added
        self.dimension = 1536
        
        # Try to load saved dimension if it exists
        if self.dimension_path.exists():
            try:
                with open(self.dimension_path, 'r') as f:
                    self.dimension = int(f.read().strip())
                logger.info(f"Loaded embedding dimension: {self.dimension}")
            except Exception as e:
                logger.warning(f"Could not load dimension, using default: {str(e)}")
        
        # Initialize FAISS index
        if self.index_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                logger.info(f"Loaded existing FAISS index with dimension {self.index.d}")
                self.dimension = self.index.d  # Update dimension from loaded index
            except Exception as e:
                logger.error(f"Error loading FAISS index: {str(e)}")
                # Create a new index with previously saved dimension
                logger.info(f"Creating new index with dimension {self.dimension}")
                self.index = faiss.IndexFlatL2(self.dimension)
        else:
            # No existing index, create a new one
            logger.info(f"Creating new FAISS index with dimension {self.dimension}")
            self.index = faiss.IndexFlatL2(self.dimension)
        
        # Load messages
        self.messages: List[ChatMessage] = []
        if self.messages_path.exists():
            try:
                with open(self.messages_path, 'r') as f:
                    data = json.load(f)
                    self.messages = [ChatMessage(**msg) for msg in data]
                logger.info(f"Loaded {len(self.messages)} messages from database")
            except Exception as e:
                logger.error(f"Error loading messages: {str(e)}")

    def add_message(self, role: str, content: str, embedding: Union[List[float], np.ndarray], metadata: Dict = None):
        """Add a message and its embedding to the database.
        
        Args:
            role: Role of the message sender (e.g. 'user', 'assistant')
            content: Text content of the message
            embedding: Vector embedding of the message content
            metadata: Optional metadata for the message
        """
        try:
            metadata = metadata or {}
            message = ChatMessage(
                role=role,
                content=content,
                timestamp=datetime.now().isoformat(),
                metadata=metadata
            )
            
            # Convert embedding to numpy array
            if isinstance(embedding, list):
                embed_array = np.array([embedding], dtype=np.float32)
            else:
                embed_array = np.array([embedding], dtype=np.float32)
            
            # Check if this is the first embedding to add
            if len(self.messages) == 0:
                # Update dimension based on the first vector
                actual_dim = embed_array.shape[1]
                if self.dimension != actual_dim:
                    logger.info(f"Updating dimension from {self.dimension} to {actual_dim}")
                    self.dimension = actual_dim
                    # Recreate index with correct dimension
                    self.index = faiss.IndexFlatL2(self.dimension)
                    # Save the dimension for future use
                    with open(self.dimension_path, 'w') as f:
                        f.write(str(self.dimension))
            
            # Check dimension match
            if embed_array.shape[1] != self.dimension:
                logger.error(f"Embedding dimension mismatch: expected {self.dimension}, got {embed_array.shape[1]}")
                # Use dimension padding or trimming as fallback
                if embed_array.shape[1] > self.dimension:
                    logger.warning(f"Trimming embedding from {embed_array.shape[1]} to {self.dimension}")
                    embed_array = embed_array[:, :self.dimension]
                else:
                    logger.warning(f"Padding embedding from {embed_array.shape[1]} to {self.dimension}")
                    padding = np.zeros((1, self.dimension - embed_array.shape[1]), dtype=np.float32)
                    embed_array = np.concatenate([embed_array, padding], axis=1)
            
            # Add message and embedding
            self.messages.append(message)
            self.index.add(embed_array)
            self._save_data()
            
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            # Don't re-raise - allow operation to continue even if storage fails

    def search_similar(self, embedding: Union[List[float], np.ndarray], k: int = 5) -> List[ChatMessage]:
        """Find messages with similar embeddings.
        
        Args:
            embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of similar messages, sorted by relevance
        """
        try:
            if not self.messages:
                return []
            
            # Convert embedding to numpy array if needed
            if isinstance(embedding, list):
                query_vector = np.array([embedding], dtype=np.float32)
            else:
                query_vector = np.array([embedding], dtype=np.float32)
                
            # Handle dimension mismatch
            if query_vector.shape[1] != self.dimension:
                if query_vector.shape[1] > self.dimension:
                    query_vector = query_vector[:, :self.dimension]
                else:
                    padding = np.zeros((1, self.dimension - query_vector.shape[1]), dtype=np.float32)
                    query_vector = np.concatenate([query_vector, padding], axis=1)
            
            # Perform search
            D, I = self.index.search(query_vector, min(k, len(self.messages)))
            
            # Return messages
            return [self.messages[i] for i in I[0] if i >= 0 and i < len(self.messages)]
            
        except Exception as e:
            logger.error(f"Error searching similar messages: {str(e)}")
            return []  # Return empty list as fallback

    def _save_data(self):
        """Save the index and messages to disk."""
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save messages atomically
            temp_path = self.messages_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump([vars(msg) for msg in self.messages], f)
            temp_path.replace(self.messages_path)
            
            # Save dimension
            with open(self.dimension_path, 'w') as f:
                f.write(str(self.dimension))
                
        except Exception as e:
            logger.error(f"Failed to save database: {str(e)}")

