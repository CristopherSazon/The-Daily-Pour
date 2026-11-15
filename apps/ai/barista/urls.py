from django.urls import path

from . import views

urlpatterns = [
    path('barista/', views.barista, name='barista'),
]
