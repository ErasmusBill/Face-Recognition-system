from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('verify-email/', views.verify_email_view, name='verify_email'), # type: ignore
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
]