from hr.models import Profile
from django.utils import timezone
from datetime import timedelta


def expire_old_aws_keys():
    stale_threshold = timezone.now() - timedelta(weeks=2)
    Profile.objects.filter(aws_keys_added__lte=stale_threshold).update(
        aws_secret_access_key=None
    )
