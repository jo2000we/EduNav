from __future__ import annotations

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Reflection, Note
from .serializers import ReflectionSerializer, NoteSerializer
from goals.permissions import IsVGUser
from goals.models import Goal
from goals.services import suggest_next_steps


class ReflectionCreateView(generics.CreateAPIView):
    queryset = Reflection.objects.all()
    serializer_class = ReflectionSerializer


class NoteCreateView(generics.CreateAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer


class NextStepSuggestView(APIView):
    permission_classes = [IsVGUser]

    def post(self, request):
        goal_id = request.data.get("goal_id")
        obstacles = request.data.get("obstacles", "")
        goal = get_object_or_404(Goal, id=goal_id)
        selected = request.data.get("selected")

        if selected:
            data = {
                "user_session": request.data.get("user_session"),
                "goal": goal_id,
                "result": request.data.get("result"),
                "obstacles": obstacles,
                "next_step": selected,
                "next_step_source": "ai",
            }
            serializer = ReflectionSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=201)

        suggestions = suggest_next_steps(goal, obstacles)
        return Response({"suggestions": suggestions})
