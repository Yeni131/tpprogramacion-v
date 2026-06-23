from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Registro simple para MVP/académico.
    - NO valida existencia real del email
    - NO envía confirmación
    - NO requiere OAuth
    """
    password  = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, label="Confirmar contraseña")

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'email', 'password', 'password2']

    def validate_email(self, value):
        # Solo verifica que no esté duplicado en la BD, nada más
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return value.lower()

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password2": "Las contraseñas no coinciden."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        # username requerido por AbstractUser — usamos el email
        user.username = validated_data['email']
        user.save()
        return user


class UserMeSerializer(serializers.ModelSerializer):
    """
    Datos del usuario autenticado. Se usa tanto para autocompletar
    el checkout (GET) como para la página "Mi Cuenta" (GET y PATCH).
    """
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            'id', 'first_name', 'last_name', 'email',
            'phone', 'address', 'avatar_url',
        ]

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if not obj.avatar:
            return None
        if request:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para editar datos personales desde 'Mi Cuenta'."""
    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'phone', 'address']

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password      = serializers.CharField(write_only=True, min_length=6)
    new_password2     = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError(
                {'new_password2': 'Las contraseñas no coinciden.'}
            )
        return data