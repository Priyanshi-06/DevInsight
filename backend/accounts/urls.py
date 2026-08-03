from django.urls import path

from . import views

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='auth-register'),
    path('auth/login/', views.LoginView.as_view(), name='auth-login'),
    path('auth/me/', views.MeView.as_view(), name='auth-me'),
    path('auth/forgot-password/', views.ForgotPasswordView.as_view(), name='auth-forgot-password'),
    path('auth/verify-otp/', views.VerifyOtpView.as_view(), name='auth-verify-otp'),
    path('auth/reset-password/', views.ResetPasswordView.as_view(), name='auth-reset-password'),
]
