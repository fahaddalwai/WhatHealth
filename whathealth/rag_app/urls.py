from django.urls import path
from .views import FileUploadView, ChatView, ChartView

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='upload'),
    path('chat/', ChatView.as_view(), name='chat'),
    path('chart/', ChartView.as_view(), name='chart'),
]
