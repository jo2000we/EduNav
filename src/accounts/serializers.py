from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    classroom = serializers.SlugRelatedField(slug_field="name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "pseudonym", "classroom", "gruppe"]


class LoginSerializer(serializers.Serializer):
    pseudonym = serializers.CharField()
    class_code = serializers.CharField(required=False, allow_blank=True)
