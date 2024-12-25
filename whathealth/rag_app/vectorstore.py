import cohere
import uuid
import hnswlib
from typing import List, Dict
from unstructured.partition.html import partition_html
from unstructured.chunking.title import chunk_by_title

co = cohere.Client("AnPnuFiUEcnWT4POFYHq3S2UOKDbGZv03E82yVhZ")

class Vectorstore:
    def __init__(self):
        self.docs = []
        self.docs_embs = []
        self.retrieve_top_k = 10
        self.rerank_top_k = 3
        self.idx = None
        self.docs_len = 0

    def ingest_text(self, text):
        """
        Load and process text from user-uploaded file.
        """
        # Chunk text into manageable pieces
        max_chunk_size = 2000  # Max characters per chunk
        chunks = self._chunk_text(text, max_chunk_size)

        for i, chunk in enumerate(chunks):
            self.docs.append({"title": f"Chunk {i}", "text": chunk})

        self.embed()
        self.index()

    def _chunk_text(self, text, max_chunk_size):
        """
        Chunk text into pieces of approximately max_chunk_size.
        """
        return [
            text[i : i + max_chunk_size]
            for i in range(0, len(text), max_chunk_size)
        ]

    def embed(self):
        """
        Embeds the document chunks using the Cohere API.
        """
        print("Embedding document chunks...")

        batch_size = 90  # Cohere API supports efficient batch processing
        self.docs_len = len(self.docs)
        for i in range(0, self.docs_len, batch_size):
            batch = self.docs[i : min(i + batch_size, self.docs_len)]
            texts = [item["text"] for item in batch]
            docs_embs_batch = co.embed(
                texts=texts, model="embed-english-v3.0", input_type="search_document"
            ).embeddings
            self.docs_embs.extend(docs_embs_batch)
        print(f"Embedded {len(self.docs_embs)} chunks.")

    def index(self):
        print("Indexing document chunks...")

        self.idx = hnswlib.Index(space="ip", dim=1024)
        self.idx.init_index(
            max_elements=len(self.docs_embs),
            ef_construction=400,  # Increase
            M=64                  # Increase
        )
        self.idx.add_items(self.docs_embs, list(range(len(self.docs_embs))))
        self.idx.set_ef(200)    # Increase

        print(f"Indexing complete with {self.idx.get_current_count()} document chunks.")



    def retrieve(self, query):
        """
        Retrieves document chunks based on the given query.

        Parameters:
        query (str): The query to retrieve document chunks for.

        Returns:
        List[Dict[str, str]]: A list of dictionaries representing the retrieved document chunks.
        """
        print(f"Retrieving for query: {query}")

        # Dense retrieval
        query_emb = co.embed(
            texts=[query], model="embed-english-v3.0", input_type="search_query"
        ).embeddings

         # Safeguard: ensure k doesn't exceed the number of indexed embeddings
        k = min(self.retrieve_top_k, self.idx.get_current_count())
        if k == 0:
            raise RuntimeError("No indexed elements available for retrieval.")

        doc_ids = self.idx.knn_query(query_emb, k=k)[0][0]

        # Reranking
        rank_fields = ["title", "text"]
        docs_to_rerank = [self.docs[doc_id] for doc_id in doc_ids]
        rerank_results = co.rerank(
            query=query,
            documents=docs_to_rerank,
            top_n=self.rerank_top_k,
            model="rerank-english-v3.0",
            rank_fields=rank_fields,
        )

        doc_ids_reranked = [doc_ids[result.index] for result in rerank_results.results]

        docs_retrieved = []
        for doc_id in doc_ids_reranked:
            docs_retrieved.append(
                {
                    "title": self.docs[doc_id]["title"],
                    "text": self.docs[doc_id]["text"],
                    "url": self.docs[doc_id].get("url", ""),  # Add default for 'url'
                }
            )

        return docs_retrieved

    def run_chatbot(self, message, chat_history=None):
        if chat_history is None:
            chat_history = []

        # Generate search queries, if any
        response = co.chat(
            message=message,
            model="command-r-plus",
            search_queries_only=True,
            chat_history=chat_history,
        )

        search_queries = []
        for query in response.search_queries:
            search_queries.append(query.text)

        # If there are search queries, retrieve the documents
        if search_queries:
            documents = []
            for query in search_queries:
                documents.extend(self.retrieve(query))

            # Use document chunks to respond
            response = co.chat_stream(
                message=message,
                model="command-r-plus",
                documents=documents,
                chat_history=chat_history,
            )
        else:
            response = co.chat_stream(
                message=message,
                model="command-r-plus",
                chat_history=chat_history,
            )

        # Parse the response into structured output
        chatbot_response = ""
        final_chat_history = chat_history

        for event in response:
            if event.event_type == "text-generation":
                chatbot_response += event.text
            if event.event_type == "stream-end":
                final_chat_history = event.response.chat_history

        return chatbot_response, final_chat_history