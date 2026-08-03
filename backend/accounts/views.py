from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .emails import send_otp_email
from .models import PasswordResetOTP
from .serializers import (
    ForgotPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    VerifyOtpSerializer,
)


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


def _find_valid_otp(email, code):
    user = User.objects.filter(username=email.strip().lower()).first()
    if not user:
        return None, None
    otp = PasswordResetOTP.objects.filter(user=user, code=code.strip(), used=False).first()
    if not otp or otp.is_expired():
        return user, None
    return user, otp


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'user': UserSerializer(user).data, **_tokens_for_user(user)},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response({'user': UserSerializer(user).data, **_tokens_for_user(user)})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()

        user = User.objects.filter(username=email).first()
        if user:
            # Invalidate any earlier unused codes so only the freshest one can succeed.
            PasswordResetOTP.objects.filter(user=user, used=False).update(used=True)
            otp = PasswordResetOTP.objects.create(user=user)
            send_otp_email(email, otp)

        # Always the same response whether or not the email is registered, so this endpoint can't
        # be used to enumerate which emails have accounts.
        return Response({'message': 'If an account with that email exists, a reset code has been sent.'})


class VerifyOtpView(APIView):
    """Checks a code without consuming it, so the frontend can confirm it's correct *before*
    asking for a new password — ResetPasswordView re-checks and actually consumes it."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _, otp = _find_valid_otp(serializer.validated_data['email'], serializer.validated_data['otp'])

        if not otp:
            return Response({'error': 'That code is invalid or has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'valid': True})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, otp = _find_valid_otp(serializer.validated_data['email'], serializer.validated_data['otp'])

        if not otp:
            return Response({'error': 'That code is invalid or has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['password'])
        user.save()
        otp.used = True
        otp.save(update_fields=['used'])

        return Response({'message': 'Password reset successfully.'})
