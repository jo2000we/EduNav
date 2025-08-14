from __future__ import annotations

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Goal, KIInteraction
from .serializers import GoalSerializer
from .services import evaluate_smart, AiCoach
from .permissions import IsVGUser
from lessons.models import UserSession


class GoalCreateKGView(generics.CreateAPIView):
    serializer_class = GoalSerializer

    def perform_create(self, serializer):
        goal = serializer.save()
        goal.final_text = goal.raw_text
        goal.finalized_at = timezone.now()
        topic = goal.user_session.lesson_session.topic
        goal.smart_score = evaluate_smart(goal.raw_text, topic)
        goal.save()


class GoalCreateVGView(generics.CreateAPIView):
    serializer_class = GoalSerializer
    permission_classes = [IsVGUser]

    def perform_create(self, serializer):
        goal = serializer.save()
        topic = goal.user_session.lesson_session.topic
        goal.smart_score = evaluate_smart(goal.raw_text, topic)
        goal.save()
        KIInteraction.objects.create(goal=goal, turn=1, role="user", content=goal.raw_text)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        goal = Goal.objects.get(id=response.data["id"])
        coach = AiCoach()
        response.data["history"] = coach._history(goal)
        return response


class CoachNextView(APIView):
    permission_classes = [IsVGUser]

    def post(self, request):
        goal_id = request.data.get("goal_id")
        user_reply = request.data.get("user_reply")
        goal = get_object_or_404(Goal, id=goal_id)
        topic = goal.user_session.lesson_session.topic
        turn = goal.interactions.count() + 1
        coach = AiCoach()
        if user_reply:
            KIInteraction.objects.create(goal=goal, turn=turn, role="user", content=user_reply)
            turn += 1
        conversation = coach._conversation(goal)
        result = evaluate_smart(conversation, topic)
        goal.smart_score = {k: result[k] for k in [
            "specific",
            "measurable",
            "achievable",
            "relevant",
            "time_bound",
            "overall",
        ]}
        goal.save()
        if result["overall"] == 5:
            answer = coach.finalize(goal, topic)
            status_flag = "ready_to_finalize"
        else:
            answer = result.get("question")
            status_flag = "question"
        KIInteraction.objects.create(goal=goal, turn=turn, role="assistant", content=answer)
        return Response(
            {
                "assistant_text": answer,
                "message_type": status_flag,
                "smart_status": goal.smart_score,
                "history": coach._history(goal),
            }
        )


class GoalFinalizeView(APIView):
    permission_classes = [IsVGUser]

    def post(self, request):
        goal_id = request.data.get("goal_id")
        goal = get_object_or_404(Goal, id=goal_id)
        coach = AiCoach()
        topic = goal.user_session.lesson_session.topic
        final_text = coach.finalize(goal, topic)
        turn = goal.interactions.count() + 1
        KIInteraction.objects.create(goal=goal, turn=turn, role="assistant", content=final_text)
        goal.final_text = final_text
        goal.finalized_at = timezone.now()
        goal.smart_score = evaluate_smart(final_text, topic)
        goal.save()
        return Response(GoalSerializer(goal).data)
