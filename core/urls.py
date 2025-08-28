from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView # New import

urlpatterns = [
    path('', views.feed, name='feed'),
    path('create/', views.create_post_view, name='create_post'),
    path('profile/', views.profile, name='profile'),
    path('profile/<int:user_id>/', views.profile, name='profile_detail'),
    path('signup/', views.signup_view, name='signup'), # New signup URL
    path('login/', LoginView.as_view(template_name='login.html'), name='login'), # Custom login view
    path('logout/', LogoutView.as_view(next_page='feed'), name='logout'), # Custom logout view
    path('post/<int:post_id>/edit/', views.edit_post_view, name='edit_post'), # New edit post URL
    path('post/<int:post_id>/delete/', views.delete_post_view, name='delete_post'), # New delete post URL
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/repost/', views.toggle_repost, name='toggle_repost'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:post_id>/comments/', views.list_comments_api, name='list_comments_api'),
    path('profile/<int:user_id>/follow/', views.toggle_follow, name='toggle_follow'),
    path('notifications/', views.list_notifications_api, name='list_notifications_api'),
    path('notifications/mark_read/', views.mark_notifications_read_api, name='mark_notifications_read_api'),
]
