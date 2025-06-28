from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('verify-email/', views.verify_email_view, name='verify-email'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('home/', views.home, name='home'),
    path('upload_images/', views.upload_images, name='upload_images'),
    path('facial_recognition_history/', views.facial_recognition_history, name='facial_recognition_history'),
    path('recognition/<int:pk>/', views.facial_recognition_detail, name='facial_recognition_detail'),
    path('resend-verification/<str:email>/', views.resend_verification_view, name='resend_verification'),
    path('resend-verification/', views.resend_verification_view, name='resend_verification_no_email'),
    path('recognition/<int:pk>/delete/', views.delete_recognition, name='delete-recognition'),
]