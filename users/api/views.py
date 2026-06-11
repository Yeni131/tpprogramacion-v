from django.contrib.auth import authenticate, login, logout, get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer, UserMeSerializer

User = get_user_model()


class RegisterView(APIView):
    """
    POST /api/users/register/
    Crea usuario con nombre, apellido, email y contraseña.
    Sin confirmación por email. Sin OAuth.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = serializer.save()
        # Loguear automáticamente después del registro
        login(request, user)
        return Response(
            {
                'success': True,
                'user': UserMeSerializer(user).data,
                'message': 'Cuenta creada exitosamente.'
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """
    POST /api/users/login/
    Autenticación estándar Django con email + contraseña.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email    = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')

        if not email or not password:
            return Response(
                {'success': False, 'errors': {'detail': 'Email y contraseña son requeridos.'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        # AbstractUser usa username internamente; nuestro USERNAME_FIELD es email
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response(
                {'success': False, 'errors': {'detail': 'Credenciales incorrectas.'}},
                status=status.HTTP_401_UNAUTHORIZED
            )

        login(request, user)
        return Response(
            {
                'success': True,
                'user': UserMeSerializer(user).data,
            }
        )


class LogoutView(APIView):
    """POST /api/users/logout/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'success': True})


class MeView(APIView):
    """
    GET /api/users/me/
    Devuelve first_name, last_name, email para autocompletar el checkout.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserMeSerializer(request.user).data)