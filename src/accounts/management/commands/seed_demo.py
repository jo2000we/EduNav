from django.core.management.base import BaseCommand
from accounts.models import User
from lessons.models import LessonSession, Classroom
from django.utils import timezone

class Command(BaseCommand):
    help = "Seed demo users and a lesson session"

    def handle(self, *args, **options):
        classroom, _ = Classroom.objects.get_or_create(name="Demo", defaults={"use_ai": True})
        User.objects.get_or_create(
            pseudonym="alice", defaults={"gruppe": User.VG, "classroom": classroom}
        )
        User.objects.get_or_create(
            pseudonym="bob", defaults={"gruppe": User.KG, "classroom": classroom}
        )
        LessonSession.objects.get_or_create(
            date=timezone.now().date(),
            classroom=classroom,
            defaults={"topic": "Demo", "use_ai": True},
        )
        self.stdout.write(self.style.SUCCESS("Demo data created"))
