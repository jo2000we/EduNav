import base64
import hashlib
from django.conf import settings
from django.db import models
from cryptography.fernet import Fernet, InvalidToken


def _get_fernet() -> Fernet:
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


class EncryptedTextField(models.TextField):
    """Simple field that encrypts its value using Fernet."""

    def from_db_value(self, value, expression, connection):  # pragma: no cover - thin wrapper
        if value is None:
            return value
        try:
            return _get_fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            return None

    def get_prep_value(self, value):  # pragma: no cover - thin wrapper
        if value is None or value == "":
            return ""
        return _get_fernet().encrypt(value.encode()).decode()


class SiteSettings(models.Model):
    """Singleton model holding site-wide configuration."""

    openai_api_key = EncryptedTextField(blank=True, null=True)
    allow_ai = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # enforce singleton with primary key 1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self) -> str:  # pragma: no cover - trivial
        return "Site Settings"

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"
