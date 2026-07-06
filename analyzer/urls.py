from django.contrib import admin
from django.urls import include, path
from .import views

urlpatterns = [
    path('',views.home, name='Home'),
    path('upload_resume/',views.upload_resume, name='upload_resume'),
]
