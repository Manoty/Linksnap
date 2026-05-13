# accounts/views.py
# Auth views. Thin by design — all logic lives in services.
# Each view does: deserialize → validate → call service → respond.

import logging
from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.serializers import LoginSerializer, RegisterSerializer, UserSerializer
from accounts.services import AuthService

logger = logging.getLogger(__name__)
User = get_user_model()


def get_tokens_for_user(user):
    """
    Generates JWT access + refresh token pair for a user.
    Kept as a standalone utility — reusable across views.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = AuthService.register_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                full_name=serializer.validated_data.get('full_name', ''),
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        tokens = get_tokens_for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(
            request,
            username=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )

        if user is None:
            return Response(
                {'detail': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {'detail': 'This account has been deactivated.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        tokens = get_tokens_for_user(user)
        logger.info(f"User logged in: {user.email}")

        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
        }, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Returns the currently authenticated user's profile."""
        return Response(UserSerializer(request.user).data)