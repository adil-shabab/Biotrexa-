from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone
from core.models import *


# Create your models here.
    
class NotificationHR(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    read_status = models.BooleanField(default=False)
    redirection_url = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=200, default='career')
    object_id = models.PositiveIntegerField(default=1)
    is_alarmed = models.BooleanField(default=False)


    def __str__(self):
        return self.message