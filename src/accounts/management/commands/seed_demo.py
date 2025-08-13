from django.core.management.base import BaseCommand
from accounts.models import User
from lessons.models import LessonSession
from django.utils import timezone

class Command(BaseCommand):
    help = "Seed demo users and a lesson session"

    def handle(self, *args, **options):
        User.objects.get_or_create(pseudonym="alice", defaults={"gruppe": User.VG})
        User.objects.get_or_create(pseudonym="bob", defaults={"gruppe": User.KG})
        LessonSession.objects.get_or_create(
            date=timezone.now().date(), defaults={"topic": "Demo", "use_ai": True}
        )
        self.stdout.write(self.style.SUCCESS("Demo data created"))
