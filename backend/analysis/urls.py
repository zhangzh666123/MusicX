from django.urls import path
from . import views

urlpatterns = [
    path('tango/', views.generate_audio, name='tango_gen'),
    path('analyze/', views.upload_and_analyze),
    path('chat/', views.chat_with_analysis),
    path('research/', views.chat_research),
    path('upload/', views.upload_snapshot),
    path('generate-image', views.generate_image, name='gen_image'),
]