from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "pseudonym", "klassengruppe", "gruppe"]


class LoginSerializer(serializers.Serializer):
    pseudonym = serializers.CharField()
    class_code = serializers.CharField(required=False, allow_blank=True)
