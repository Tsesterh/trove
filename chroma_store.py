import chromadb
from chromadb.config import Settings
import os
import hashlib

class MathExampleStore:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            is_persistent=True
        ))
        self.collection = self.client.get_or_create_collection(
            name="math_examples",
            metadata={"hnsw:space": "cosine"}
        )

    def _generate_id(self, question):
        """Generate a unique ID for a question."""
        return hashlib.md5(question.encode()).hexdigest()

    def add_example(self, question: str, solution: str):
        """Add a new example to the store."""
        example_id = self._generate_id(question)
        self.collection.add(
            documents=[question],
            metadatas=[{"solution": solution}],
            ids=[example_id]
        )

    def get_similar_examples(self, question: str, k: int = 3) -> list[dict]:
        """Retrieve k most similar examples."""
        results = self.collection.query(
            query_texts=[question],
            n_results=k
        )
        
        similar_examples = []
        if results and len(results['documents']) > 0:
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                similar_examples.append({
                    'question': doc,
                    'solution': metadata['solution']
                })
        
        return similar_examples

    def clear(self):
        """Clear all examples from the store."""
        self.client.delete_collection("math_examples")
        self.collection = self.client.create_collection(
            name="math_examples",
            metadata={"hnsw:space": "cosine"}
        ) 