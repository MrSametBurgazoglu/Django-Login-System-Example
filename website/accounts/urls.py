from django.urls import path
from .views import *
from django.contrib.auth import views
app_name = 'accounts'

urlpatterns = [
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("password_reset/", password_reset_view, name="password_reset"),
    path('password_reset/done/',
         views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html", success_url='/accounts/reset/done'),
         name='password_reset_confirm'),
    path('reset/done/',
         views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
]
