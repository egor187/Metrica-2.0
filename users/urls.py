from django.urls import path

import uuid

from users import views


app_name = 'users'

urlpatterns = [
    path('', views.UsersListView.as_view(), name='users_index'),
    path('login/', views.UsersLoginView.as_view(), name='login'),
    path('logout/', views.UsersLogoutView.as_view(), name='logout'),
    path('<int:pk>/', views.UsersDetailView.as_view(), name='users_detail'),
    path(
        'friendship_requests/',
        views.FriendRequestListView.as_view(),
        name='friendship_requests_list'
    ),
    path(
        'friendship_requests/proceed/<int:request_pk>/<str:status>/',
        views.FriendRequestProceedView.as_view(),
        name='friendship_request_proceed'
    ),
    path('register/', views.UsersCreateView.as_view(), name='users_register'),
    path('update/<int:pk>/', views.UsersUpdateView.as_view(), name='users_update'),
    path('friends/add/<int:pk>/', views.FriendAddView.as_view(), name='friend_add'),
    path('friends/remove/<int:pk>/', views.FriendRemoveView.as_view(), name='friend_remove'),

    path(
        'update/password/',
        views.PasswordChangeCustomView.as_view(template_name="password_update.html"),
        name='password_update'
    ),

    # create and update user profile by tg link
    path('add_user/', views.add_user_view_through_tg_bot, name='add_user_from_bot'),
    path('reg_cont/<int:pk>/' + str(uuid.uuid4()), views.UserUpdateViewFromBot.as_view(), name='reg_cont'),
    path('invite_to_register/', views.invite_to_register, name='invite_to_register'),

    # claim
    path('send_email_to_admin/', views.feedback_view, name='feedback_to_email'),
    path('contact_us/', views.ClaimCreateView.as_view(), name='feedback'),

    # jwt
    path('jwt/', views.JwtLoginView.as_view()),
    path('jwt/user/', views.JwtUserView.as_view()),
]
