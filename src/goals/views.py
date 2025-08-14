from __future__ import annotations

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Goal, KIInteraction, OverallGoal
from .serializers import GoalSerializer, OverallGoalSerializer
from .services import evaluate_smart, AiCoach
from .permissions import IsVGUser
from lessons.models import UserSession


class OverallGoalView(APIView):
    def get(self, request):
        goal = OverallGoal.objects.filter(user=request.user).first()
        if not goal:
            return Response({})
        return Response(OverallGoalSerializer(goal).data)

    def post(self, request):
        serializer = OverallGoalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        goal, created = OverallGoal.objects.update_or_create(
            user=request.user, defaults={"text": serializer.validated_data["text"]}
        )
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(OverallGoalSerializer(goal).data, status=status_code)


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
            KIInteraction.objects.create(
                goal=goal, turn=turn, role="user", content=user_reply
            )
            turn += 1

        last_user_text = goal.interactions.filter(role="user").last().content
        result = evaluate_smart(last_user_text, topic)

        fields = ["specific", "measurable", "achievable", "relevant", "time_bound"]
        smart = goal.smart_score or {k: False for k in fields}
        for k in fields:
            smart[k] = smart.get(k, False) or result[k]
        smart["overall"] = sum(smart[k] for k in fields)
        goal.smart_score = smart
        goal.save()

        if smart["overall"] == 5:
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
