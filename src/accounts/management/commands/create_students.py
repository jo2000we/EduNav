from django.core.management.base import BaseCommand, CommandError
from accounts.models import User
from lessons.models import Classroom

class Command(BaseCommand):
    help = "Create multiple student users. Provide pseudonyms and optional classroom code."

    def add_arguments(self, parser):
        parser.add_argument("pseudonyms", nargs="+", help="List of student pseudonyms to create")
        parser.add_argument(
            "--class-code",
            dest="class_code",
            help="Optional classroom code to assign",
        )

    def handle(self, *args, **options):
        class_code = options.get("class_code")
        classroom = None
        if class_code:
            try:
                classroom = Classroom.objects.get(code=class_code)
            except Classroom.DoesNotExist:
                raise CommandError(f"Classroom with code '{class_code}' not found")

        created = 0
        for pseudonym in options["pseudonyms"]:
            user, was_created = User.objects.get_or_create(
                pseudonym=pseudonym,
                defaults={"classroom": classroom}
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {created} students"))
