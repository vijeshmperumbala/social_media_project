import django
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):

    password = models.CharField(max_length=128, blank=True, null=True)
    email = models.EmailField(max_length=254, unique=True,)
    name = models.CharField(max_length=150, blank=True, null=True)
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)

    def __str__(self):
        return self.email


class FriendRequest(models.Model):

    STATUS = [
        (1, 'Requested'),
        (2, 'Accepted'),
        (3, 'Rejected'),
    ]
    created_date = models.DateTimeField(default=django.utils.timezone.now)
    requested_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_user')
    request_received_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='request_received_user')
    status = models.IntegerField(choices=STATUS, default=1)

    @classmethod
    def can_send_friend_request(cls, user):
        cutoff_time = timezone.now() - timezone.timedelta(minutes=1)
        recent_requests_count = cls.objects.filter(
            requested_user=user,
            created_date__gte=cutoff_time
        ).count()

        return recent_requests_count < 3
    
    @classmethod
    def check_already_request_send(cls, requested_user, secondary_user):
        return cls.objects.filter(
            requested_user=requested_user,
            request_received_user=secondary_user,
            status=1
        ).exists()
        
    @classmethod
    def check_already_friend(cls, requested_user, secondary_user):
        return cls.objects.filter(
            requested_user=requested_user,
            request_received_user=secondary_user,
            status=2
        ).exists()
        