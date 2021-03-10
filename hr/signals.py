from django.db.models.signals import post_save
from django.dispatch import receiver
from hr.models import Profile
from django.contrib.auth.models import User


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    user = instance
    if created:
        user.email = user.username
        user.save()
        Profile.objects.create(user=user)
