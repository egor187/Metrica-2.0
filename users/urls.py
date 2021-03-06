from django.urls import path

import uuid

from users import views


app_name = 'users'

urlpatterns = [
    path('', views.UsersListView.as_view(), name='users_index'),
    path('login/', views.UsersLoginView.as_view(), name='login'),
    path('logout/', views.UsersLogoutView.as_view(), name='logout'),
    path('<int:pk>/', views.UsersDetailView.as_view(), name='users_detail'),
    path('register/', views.UsersCreateView.as_view(), name='users_register'),
    path('update/<int:pk>/', views.UsersUpdateView.as_view(), name='users_update'),
    path('friends/add/<int:pk>/', views.FriendAddView.as_view(), name='friend_add'),
    path('friends/remove/<int:pk>/', views.FriendRemoveView.as_view(), name='friend_remove'),

    # create and update user profile by tg link
    path('add_user/', views.add_user_view, name='add_user_from_bot'),
    path('reg_cont/<int:pk>/' + str(uuid.uuid4()), views.UserUpdateViewFromBot.as_view(), name='reg_cont'),

    path('invite_to_register/', views.invite_to_register, name='invite_to_register'),
    path('send_email_to_admin/', views.feedback_view, name='feedback_to_email'),
    path('contact_us/', views.ClaimCreateView.as_view(), name='feedback'),

    path('jwt/', views.JwtLoginView.as_view()),
    path('jwt/user/', views.JwtUserView.as_view()),
]
