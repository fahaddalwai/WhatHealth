from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("rag_app.urls")),

    # This line makes the root URL (/) serve the upload template
    path("", TemplateView.as_view(template_name="upload.html"), name="home"),

    # For reference, your other paths
    path("upload/", TemplateView.as_view(template_name="upload.html"), name="upload"),
    path("chat/", TemplateView.as_view(template_name="chat.html"), name="chat"),
]
