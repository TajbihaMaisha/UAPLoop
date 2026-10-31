from django.urls import path

from . import views

urlpatterns = [
    path('', views.browse, name='browse'),
    path('listing/<int:pk>/', views.detail, name='detail'),
    path('listing/<int:pk>/buy/', views.request_buy, name='request_buy'),
    path('listing/<int:pk>/requests/', views.listing_requests, name='listing_requests'),
    path('request/<int:pk>/accept/', views.accept_request, name='accept_request'),
    path('new/', views.new_listing, name='new_listing'),
    path('mine/', views.my_listings, name='my_listings'),
    path('sold/<int:pk>/', views.mark_sold, name='mark_sold'),
    path('remove/<int:pk>/', views.remove_listing, name='remove_listing'),
]
