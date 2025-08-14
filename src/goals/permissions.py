from rest_framework.permissions import BasePermission
from lessons.models import UserSession
from config.models import SiteSettings
from .models import Goal

class IsVGUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated or getattr(user, "gruppe", "") != "VG":
            return False

        if not SiteSettings.get().allow_ai:
            return False

        lesson_session = None
        user_session_id = request.data.get("user_session")
        goal_id = request.data.get("goal_id") or request.data.get("goal")

        if user_session_id:
            try:
                lesson_session = UserSession.objects.get(id=user_session_id).lesson_session
            except UserSession.DoesNotExist:
                return False
        elif goal_id:
            try:
                goal = Goal.objects.get(id=goal_id)
                lesson_session = goal.user_session.lesson_session
            except Goal.DoesNotExist:
                return False

        return bool(lesson_session and lesson_session.use_ai)
