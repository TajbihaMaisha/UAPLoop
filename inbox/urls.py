from django.urls import path

from . import views

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/<int:pk>/', views.conversation, name='conversation'),
    path('inbox/<int:pk>/new/', views.new_messages, name='new_messages'),
]
