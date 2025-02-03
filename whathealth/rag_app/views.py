from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser
from .vectorstore import Vectorstore

# Initialize Vectorstore globally
vectorstore = Vectorstore()

from rest_framework.parsers import MultiPartParser, FormParser

class FileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')  # Get the file from the request
        if not file:
            return Response({"detail": "File not provided"}, status=400)
        content = file.read().decode('utf-8')  # Decode the file content
        vectorstore.ingest_text(content)
        return Response({"message": "File ingested successfully."})


import logging

logger = logging.getLogger(__name__)

class ChatView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            query = request.data.get("query")
            chat_history = request.data.get("chat_history", [])  # Default to empty list

            if not query:
                return Response({"detail": "Query is required."}, status=400)

            # Log inputs for debugging
            logger.debug(f"Query received: {query}")
            logger.debug(f"Chat history: {chat_history}")

            chatbot_response, updated_chat_history = vectorstore.run_chatbot(query, chat_history)

            # Log outputs for debugging
            logger.debug(f"Chatbot response: {chatbot_response}")
            logger.debug(f"Updated chat history: {updated_chat_history}")

            return Response({
                "response": chatbot_response,
                "chat_history": updated_chat_history,
            })

        except Exception as e:
            logger.error(f"Error in ChatView: {str(e)}", exc_info=True)
            return Response({"detail": str(e)}, status=500)


class ChartView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            query = request.data.get("query")
            chat_history = request.data.get("chat_history", [])  # Default to empty list

            if not query:
                return Response({"detail": "Query is required."}, status=400)

            # Log inputs for debugging
            logger.debug(f"Query received: {query}")
            logger.debug(f"Chat history: {chat_history}")

            chatbot_response, updated_chat_history = vectorstore.chartcsv(query, chat_history)

            # Log outputs for debugging
            logger.debug(f"Chatbot response: {chatbot_response}")
            logger.debug(f"Updated chat history: {updated_chat_history}")

            return Response({
                "response": chatbot_response,
                "chat_history": updated_chat_history,
            })

        except Exception as e:
            logger.error(f"Error in ChartView: {str(e)}", exc_info=True)
            return Response({"detail": str(e)}, status=500)

