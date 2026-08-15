from django.urls import path
from .import views


urlpatterns=[

    path('', views.career_home, name='career_home'),
    path("result/", views.career_result, name="career_result"),
    path("roadmap/",views.roadmap_detail,name="roadmap_detail"),
]