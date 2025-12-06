from django.urls import path
from . import views

urlpatterns = [
    path('register', views.api_register, name='api_register'),
    path('login', views.api_login, name='api_login'),
    path('logout', views.api_logout, name='api_logout'),
    path('me', views.api_me, name='api_me'),
    
    path('venues', views.api_venues_list, name='api_venues_list'),
    path('venues/<int:venue_id>', views.api_venue_detail, name='api_venue_detail'),
    
    path('reviews', views.api_reviews_list, name='api_reviews_list'),
    path('reviews/create', views.api_reviews_create, name='api_reviews_create'),
    path('reviews/<int:review_id>', views.api_reviews_update, name='api_reviews_update'),
    path('reviews/<int:review_id>/delete', views.api_reviews_delete, name='api_reviews_delete'),
    
    path('user/<int:user_id>', views.api_user_profile, name='api_user_profile'),
    
    path('feed', views.api_feed, name='api_feed'),
]
