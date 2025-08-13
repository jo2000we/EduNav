from __future__ import annotations

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Goal, KIInteraction
from .serializers import GoalSerializer
from .services import evaluate_smart, AiCoach, SMART_PROMPT
from .permissions import IsVGUser
from lessons.models import UserSession


class GoalCreateKGView(generics.CreateAPIView):
    serializer_class = GoalSerializer

    def perform_create(self, serializer):
        goal = serializer.save()
        goal.final_text = goal.raw_text
        goal.finalized_at = timezone.now()
        goal.smart_score = evaluate_smart(goal.raw_text)
        goal.save()


class GoalCreateVGView(generics.CreateAPIView):
    serializer_class = GoalSerializer
    permission_classes = [IsVGUser]

    def perform_create(self, serializer):
        goal = serializer.save()
        goal.smart_score = evaluate_smart(goal.raw_text)
        goal.save()
        KIInteraction.objects.create(goal=goal, turn=1, role="user", content=goal.raw_text)


class CoachNextView(APIView):
    permission_classes = [IsVGUser]

    def post(self, request):
        goal_id = request.data.get("goal_id")
        user_reply = request.data.get("user_reply")
        goal = get_object_or_404(Goal, id=goal_id)
        turn = goal.interactions.count() + 1
        coach = AiCoach()
        if user_reply:
            KIInteraction.objects.create(goal=goal, turn=turn, role="user", content=user_reply)
            goal.smart_score = evaluate_smart(user_reply)
            goal.save()
            turn += 1
        prompt = SMART_PROMPT + "\n" + "\n".join(i.content for i in goal.interactions.order_by("turn"))
        answer = coach.ask(prompt)
        KIInteraction.objects.create(goal=goal, turn=turn, role="assistant", content=answer)
        status_flag = "ready" if goal.smart_score and goal.smart_score.get("score", 0) >= 4 else "question"
        return Response({"assistant_text": answer, "message_type": status_flag, "smart_status": goal.smart_score})


class GoalFinalizeView(APIView):
    permission_classes = [IsVGUser]

    def post(self, request):
        goal_id = request.data.get("goal_id")
        goal = get_object_or_404(Goal, id=goal_id)
        last_user = goal.interactions.filter(role="user").order_by("-turn").first()
        final_text = last_user.content if last_user else goal.raw_text
        goal.final_text = final_text
        goal.finalized_at = timezone.now()
        goal.save()
        return Response(GoalSerializer(goal).data)
