from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/', include('core.urls')),
    
    path('', views.home_view, name='home'),
    path('community', views.community_view, name='community'),
    path('login', views.login_signup_view, name='login'),
    path('place/<int:venue_id>', views.place_details_view, name='place_details'),
    path('profile/<int:user_id>', views.profile_page_view, name='profile'),
]
