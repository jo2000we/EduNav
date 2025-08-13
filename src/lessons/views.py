from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import LessonSession, UserSession
from .serializers import LessonSessionSerializer, UserSessionSerializer


class LessonSessionCreateView(generics.CreateAPIView):
    queryset = LessonSession.objects.all()
    serializer_class = LessonSessionSerializer
    permission_classes = [permissions.IsAdminUser]


class UserSessionEnterView(APIView):
    def post(self, request):
        lesson_id = request.data.get("lesson_session_id")
        lesson = get_object_or_404(LessonSession, id=lesson_id)
        user_session, _ = UserSession.objects.get_or_create(
            user=request.user, lesson_session=lesson
        )
        return Response({"user_session_id": str(user_session.id)})
