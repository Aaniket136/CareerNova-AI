from django.urls import path 
from .import views


urlpatterns =[
    path('', views.interview_home, name='interview_home'),
    path("submit-answer/", views.submit_answer, name="submit_answer"),
    
]