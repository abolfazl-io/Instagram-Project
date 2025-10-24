from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

app_name = 'shop1'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('login/', views.loginView, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('', views.post_list, name='post_list'),

    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),

    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:pk>/comment/<int:parent_id>/', views.add_comment, name='reply_comment'),

    path('register/', views.register_view, name='register'),

    path('post/<int:pk>/like/', views.like_post, name='like_post'),
    path('post/<int:pk>/dislike/', views.dislike_post, name='dislike_post'),

    path('comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('comment/<int:comment_id>/dislike/', views.dislike_comment, name='dislike_comment'),
    path('search/', views.search_users, name='search_users'),

    path('user/<str:username>/', views.public_profile, name='public_profile'),
    path('profile/delete/', views.delete_account, name='delete_account'),

    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='password_reset_form.html',
             email_template_name='password_reset_email.html',
             subject_template_name='password_reset_subject.txt',
             success_url=reverse_lazy('shop1:password_reset_done')
         ),
         name='password_reset'),

    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html',
             success_url=reverse_lazy('shop1:password_reset_complete')
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # Story URLs
    path('story/create/', views.create_story, name='create_story'),
    path('story/<int:story_id>/', views.view_story, name='view_story'),
    path('story/<int:story_id>/like/', views.like_story, name='like_story'),
    path('story/<int:story_id>/comment/', views.add_story_comment, name='add_story_comment'),
    # خط جدید زیر را اضافه کنید
    path('user/<str:username>/follow/', views.follow_unfollow, name='follow_unfollow'),
    path('user/<str:username>/', views.public_profile, name='public_profile'),
    path('user/<str:username>/follow/', views.follow_unfollow, name='follow_unfollow'),
    # دو خط جدید زیر را اضافه کنید
    path('user/<str:username>/followers/', views.followers_list, name='followers_list'),
    path('user/<str:username>/following/', views.following_list, name='following_list'),
    
    path('profile/delete/', views.delete_account, name='delete_account'),
    # Direct Message URLs
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/thread/<int:thread_id>/', views.thread_view, name='thread_view'),
    path('inbox/create_thread/<str:username>/', views.create_thread, name='create_thread'),
    path('inbox/thread/<int:thread_id>/upload/', views.upload_direct_file, name='upload_direct_file'),
    path('post/<int:post_pk>/share/', views.share_post, name='share_post'),
    path('message/<int:message_id>/viewed/', views.mark_media_as_viewed, name='mark_media_as_viewed'),
    path('inbox/thread/<int:thread_id>/upload/', views.upload_direct_file, name='upload_direct_file'),
    path('inbox/create_group/', views.create_group, name='create_group'),
    path('inbox/thread/<int:thread_id>/edit/', views.edit_group, name='edit_group'),
    path('explore/', views.explore_view, name='explore'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)