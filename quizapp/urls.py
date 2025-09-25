from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_pdf, name='upload_pdf'),
    path('quiz/<int:pdf_id>/', views.take_mcq, name='take_quiz'),
    path('result/<int:pdf_id>/', views.show_result, name='show_result'),
]
