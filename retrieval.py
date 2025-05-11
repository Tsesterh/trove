"""
Light‑weight wrapper around ChromaDB for k‑NN retrieval of
in‑context learning examples. Mirrors the recipe used in the paper
(OpenAI ada‐002 embeddings + DuckDB/Parquet persistence).
"""
from __future__ import annotations

import os
import atexit
from typing import List, Dict

import chromadb
from chromadb import Settings
from chromadb.utils import embedding_functions


class ChromaRetriever:
    """Builds/loads a persistent Chroma collection and exposes
    get_similar() that returns the *original* example dictionaries.
    """

    def __init__(
        self,
        examples: List[Dict],
        task_name: str,
        persist_dir: str = "chromadb_store",
        collection_suffix: str = "_icl_examples",
    ) -> None:
        self.examples = examples
        self.ids = [str(i) for i in range(len(examples))]
        self.task_name = task_name
        coll_name = f"{task_name}{collection_suffix}"

        # Use OpenAI ada‑002 embeddings (same as the paper)
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-ada-002",
        )

        # One DuckDB+Parquet backed client per persist_dir
        self.client = chromadb.Client(
            Settings(
                persist_directory=persist_dir,
                chroma_db_impl="duckdb+parquet",
            )
        )
        self.collection = self.client.get_or_create_collection(
            name=coll_name, embedding_function=openai_ef
        )

        # Populate the collection once (idempotent)
        if self.collection.count() == 0:
            docs = [ex["question"] for ex in examples]
            self.collection.add(documents=docs, ids=self.ids)

        # Persist on interpreter shutdown so the index survives
        atexit.register(lambda: self.client.persist())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_similar(
        self, query: str, k: int = 3, exclude_exact: bool = True
    ) -> List[Dict]:
        """Return top‑k similar *example dicts* for the given query."""
        result = self.collection.query(query_texts=[query], n_results=k)
        retrieved_ids = result["ids"][0]
        sims: List[Dict] = [self.examples[int(i)] for i in retrieved_ids]
        if exclude_exact:
            sims = [ex for ex in sims if ex["question"] != query]
        return sims
    
    def add_example(self, question: str, solution: str | None = None) -> None:
        """Append a new (question, optional solution) pair to the collection."""
        new_id = str(len(self.examples))
        self.examples.append({"question": question, "solution": solution if solution else ""})
        self.collection.add(documents=[question], ids=[new_id])