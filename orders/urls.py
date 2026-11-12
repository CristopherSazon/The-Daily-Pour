from django.urls import path

from . import views

urlpatterns = [
    path('orders/', views.place_order, name='place_order'),
]
