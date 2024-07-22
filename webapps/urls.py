"""
URL configuration for webapps project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from mapp import views

urlpatterns = [
    path('', views.map_page_action, name='home_page'), #home page TODO: change to the map page later

    path('register', views.register_action, name='register'),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('oauth_logout', auth_views.logout_then_login, name='logout'),
    path('login', views.login_action, name='login'),
    path('admin/', admin.site.urls),
    path('logout', views.logout_action, name='logout'),


    path('<int:id>', views.map_page_action_detail, name='detail_map_page'),
    path('map_page', views.map_page_action, name='map_page'),
    path('post/<int:id>', views.get_post, name='post'),
    path('add_post', views.add_post_action, name="add_post"),
    path('add_comment', views.add_comment_action, name="add_comment"),
    path('new_rating', views.new_rating_action, name="new_rating"),
    path('update_playlists', views.update_playlists, name="update_playlists"),


    path('rec_page', views.get_feed_page, name='rec_page'),

    path('gpt_search', views.get_search_feed, name='gpt_search'),

    path('profile', views.profile_action, name='profile'),
    path('other_profile/<int:id>', views.other_profile_action, name='other_profile'),
    path('photo/<int:id>', views.get_photo, name='photo'),
    path('profile_photo/<int:id>', views.get_photo_profile, name='photo_profile'),
    path('follow/<int:id>', views.follow, name='follow'),
    path('unfollow/<int:id>', views.unfollow, name='unfollow'),

    path('get-global', views.get_global, name='get-global'),
    path('playlist/<int:id>', views.get_playlist, name='playlist_detail'),
    path('playlist/<int:id>/delete', views.delete_playlist, name='playlist_delete'),
    path('post/<int:id>/delete_from_playlist', views.delete_post_from_playlist, name='post_playlist_delete'),

]
