import uuid

from django.db import models


class Guest(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    milk = models.CharField(max_length=40, blank=True)
    sweetness = models.CharField(max_length=40, blank=True)
    temperature = models.CharField(max_length=40, blank=True)
    note = models.CharField(max_length=200, blank=True)
    usuals = models.JSONField(blank=True, default=list)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['phone']),
        ]

    def __str__(self):
        return self.name or str(self.token)
