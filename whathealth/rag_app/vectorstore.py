import cohere
import uuid
import hnswlib
from typing import List, Dict
from unstructured.partition.html import partition_html
from unstructured.chunking.title import chunk_by_title
import os
from dotenv import load_dotenv
import re

load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(COHERE_API_KEY)

class Vectorstore:
    def __init__(self):
        self.docs = []
        self.docs_embs = []
        self.retrieve_top_k = 50
        self.rerank_top_k = 5
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
        print(f"Retrieving for query: {query}")

        # Dense retrieval
        query_emb = co.embed(
            texts=[query], model="embed-english-v3.0", input_type="search_query"
        ).embeddings

        # Safeguard: ensure k doesn't exceed the number of indexed embeddings
        k = min(self.retrieve_top_k, self.idx.get_current_count())
        if k == 0:
            raise RuntimeError("No indexed elements available for retrieval.")

        # Properly extract document IDs
        labels, _ = self.idx.knn_query(query_emb, k=k)
        doc_ids = labels[0]  # Now a list/array of document indices

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
                    "url": self.docs[doc_id].get("url", ""),  # Default for 'url'
                }
            )

        return docs_retrieved


    def run_chatbot(self, message, chat_history=None):
        if chat_history is None:
            chat_history = []

        # Define a system prompt
        system_prompt = (
            "You are a health assistant answering user's questions using the provided health data that is already available in your document dataset. "
            "Your role is to accurately extract insights and provide fact-based answers based on this document and also answer the users questions whatever they may be as accurately as possible "
            "When answering, prioritize precision and use available document to support your claims. "
            "For example, if the user asks about calorie burn trends, analyze available data and provide exact numbers."
        )


        # Combine the system prompt with the user message
        full_message = f"{system_prompt}\n\nUser: {message}"

        # Generate search queries, if any
        response = co.chat(
            message=full_message,
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
                retrieved_docs = self.retrieve(query)
                documents.extend(retrieved_docs)
                print(f"Retrieved documents for query '{query}': {retrieved_docs}")

            response = co.chat_stream(
                message=full_message,
                model="command-r-plus",
                documents=documents,
                chat_history=chat_history,
            )
        else:
            response = co.chat_stream(
                message=full_message,
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
    
    def chartcsv(self, message, chat_history=None):
        if chat_history is None:
            chat_history = []

        # Define a system prompt
        system_prompt = (
            "You are a health assistant answering user's questions using the provided health data that is already available in your document dataset. "
            "Your role is to accurately extract data fields which are relevant to the user query and return in CSV format. "
            "When answering, return in csv format containing 2 columns ONLY."
            "For example, if the user asks about calorie burn trends, analyze available data and provide exact numbers in CSV format containing 2 columns like this:"
            "Day,Calorie",
            "02-22-2024,250"
        )


        # Combine the system prompt with the user message
        full_message = f"{system_prompt}\n\nUser: {message}"

        # Generate search queries, if any
        response = co.chat(
            message=full_message,
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
                retrieved_docs = self.retrieve(query)
                documents.extend(retrieved_docs)
                print(f"Retrieved documents for query '{query}': {retrieved_docs}")

            response = co.chat_stream(
                message=full_message,
                model="command-r-plus",
                documents=documents,
                chat_history=chat_history,
            )
        else:
            response = co.chat_stream(
                message=full_message,
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
        print(chatbot_response)
        return chatbot_response, final_chat_history

    import re

    def chart_html(self, message, chat_history=None):
        if chat_history is None:
            chat_history = []

        system_prompt = (
            "You are a health assistant answering user's questions using the provided health data that is already available in your document dataset. "
            "Your role is to accurately extract data fields which are relevant to the user query and return a complete HTML snippet that renders a line chart using Chart.js. "
            "The HTML snippet should include a <canvas> element with id 'healthChart' and a corresponding <script> block that initializes the chart with dynamic data. "
            "Ensure that the chart is fully functional when inserted into a webpage, with dynamic axis titles and data arrays. "
            "Return only the necessary HTML code snippet (canvas and script), without <html>, <head>, or <body> tags."
        )

        full_message = f"{system_prompt}\n\nUser: {message}"

        # Generate search queries (if any)
        response = co.chat(
            message=full_message,
            model="command-r-plus",
            search_queries_only=True,
            chat_history=chat_history,
        )
        search_queries = [query.text for query in response.search_queries]

        if search_queries:
            documents = []
            for query in search_queries:
                retrieved_docs = self.retrieve(query)
                documents.extend(retrieved_docs)
                print(f"Retrieved documents for query '{query}': {retrieved_docs}")
            response = co.chat_stream(
                message=full_message,
                model="command-r-plus",
                documents=documents,
                chat_history=chat_history,
            )
        else:
            response = co.chat_stream(
                message=full_message,
                model="command-r-plus",
                chat_history=chat_history,
            )

        chatbot_response = ""
        final_chat_history = chat_history

        for event in response:
            if event.event_type == "text-generation":
                chatbot_response += event.text
            if event.event_type == "stream-end":
                final_chat_history = event.response.chat_history

        # 🔹 Strip unwanted Markdown formatting (```html ... ```)
        chatbot_response = chatbot_response.replace("```html", "").replace("```", "").strip()

        # 🔹 Extract only the <canvas> and <script> sections
        canvas_match = re.search(r"<canvas[^>]*>.*?</canvas>", chatbot_response, re.DOTALL)
        script_match = re.search(r"<script[^>]*>.*?</script>", chatbot_response, re.DOTALL)

        if canvas_match and script_match:
            cleaned_html = canvas_match.group(0) + script_match.group(0)
        else:
            cleaned_html = "<p class='text-red-500'>Error: No valid chart generated.</p>"

        return cleaned_html, final_chat_history
