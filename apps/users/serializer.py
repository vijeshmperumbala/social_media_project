from django.contrib.auth.hashers import make_password
from django.core.validators import EmailValidator

from rest_framework import serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import User, FriendRequest


class UserSignupSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(
        max_length=254,
        validators=[EmailValidator(message="Enter a valid email address.")],
    )

    class Meta:
        model = User
        fields = ["email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return super(UserSignupSerializer, self).create(validated_data)


# class UserSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = User
#         fields = ['id', 'name', 'email', 'password',]


class UserDisplaySerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'email', 'name']


class UserNameUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name']


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"})

    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise AuthenticationFailed(
                    {"status": False, "message": "User not registered."}
                )

            if user.password and user.check_password(password):
                refresh = self.get_token(user)
                access = str(refresh.access_token)
                refresh = str(refresh)
                return {
                    "status": True,
                    "message": "Token Generated.",
                    "data": {"access": access, "refresh": refresh},
                }
            else:
                raise AuthenticationFailed(
                    {"status": False, "message": "Wrong Password."}
                )
        else:
            raise AuthenticationFailed(
                {"status": False, "message": "Email and password are required."}
            )


class UserSearchSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate(self, attrs):
        email = attrs.get("email")
        name = attrs.get("name")

        if not email and not name:
            raise serializers.ValidationError(
                "Please provide at least one search parameter (email or name)"
            )

        return attrs


class FriendRequestSerializer(serializers.ModelSerializer):
    request_received_user = UserDisplaySerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ["id", "created_date", "request_received_user"]
