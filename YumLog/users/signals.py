# YumLog/users/signals.py
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from .models import users as CustomUser
from django.contrib.auth.hashers import make_password
import logging

logger = logging.getLogger(__name__)

@receiver(user_signed_up)
def create_custom_user(sender, request, user, **kwargs):
    # derive user_id and name from email prefix
    email_prefix = user.email.split('@')[0]

    obj, created = CustomUser.objects.get_or_create(
        user_id=email_prefix,
        defaults={
            'name': email_prefix,
            'password': make_password(None),
            'tags': '',           # ✅ 不再随机分配标签，设置为空
            'profile': '',
            'city': 'Penn',
            'state': 'PA',
            'email': user.email,
        }
    )
    if created:
        logger.info(f"[SIGNAL] Created CustomUser for {user.email}")
    else:
        logger.info(f"[SIGNAL] CustomUser already exists for {user.email}")
