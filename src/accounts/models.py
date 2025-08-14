from __future__ import annotations

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, pseudonym: str, password: str | None, **extra_fields):
        if not pseudonym:
            raise ValueError("The pseudonym must be set")
        user = self.model(pseudonym=pseudonym, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, pseudonym: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(pseudonym, password, **extra_fields)

    def create_superuser(self, pseudonym: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(pseudonym, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    VG = "VG"
    KG = "KG"
    GROUP_CHOICES = [(VG, "Versuchsgruppe"), (KG, "Kontrollgruppe")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pseudonym = models.CharField(max_length=150, unique=True)
    classroom = models.ForeignKey(
        "lessons.Classroom", null=True, blank=True, on_delete=models.SET_NULL
    )
    gruppe = models.CharField(max_length=2, choices=GROUP_CHOICES, default=KG)
    created_at = models.DateTimeField(auto_now_add=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "pseudonym"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.pseudonym
