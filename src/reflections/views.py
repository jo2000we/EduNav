from __future__ import annotations

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Reflection, Note
from .serializers import ReflectionSerializer, NoteSerializer
from goals.permissions import IsVGUser
from goals.models import Goal
from goals.services import AiCoach


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
        coach = AiCoach()
        prompt = f"Ziel: {goal.final_text}\nHindernisse: {obstacles}\nGib drei kurze nächste Schritte."
        answer = coach.ask(prompt)
        suggestions = [s.strip() for s in answer.split('\n') if s.strip()][:3]
        return Response({"suggestions": suggestions})
