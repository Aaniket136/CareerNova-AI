from django.urls import path 
from .import views


urlpatterns =[
    path('', views.interview_home, name='interview_home'),
    path("submit-answer/", views.submit_answer, name="submit_answer"),
    path("interview-complete/",views.interview_complete,name="interview_complete"),
    path("interview-answers/",views.interview_answers,name="interview_answers"),
    
]