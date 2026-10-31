from django.urls import path

from . import views

urlpatterns = [
    path('listing/<int:pk>/review/', views.add_review, name='add_review'),
]
