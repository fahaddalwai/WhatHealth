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


class ChatView(APIView):
    def post(self, request, *args, **kwargs):
        query = request.data.get("query")
        response = vectorstore.retrieve(query)
        return Response({"response": "I know my api endpoint is working atleast"})
