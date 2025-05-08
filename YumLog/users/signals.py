# YumLog/users/signals.py
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from .models import users as CustomUser
import random
from django.contrib.auth.hashers import make_password
import logging
logger = logging.getLogger(__name__)

@receiver(user_signed_up)
def create_custom_user(sender, request, user, **kwargs):
    # derive user_id and name from email prefix
    email_prefix = user.email.split('@')[0]
    TAG_CHOICES = [
        'American','Burgers','Fast Food','Mexican','Asian',
        'Pizza','Desserts','Seafood','Sushi','Vegetarian Friendly'
    ]
    random_tags = random.sample(TAG_CHOICES, 3)
    tags_str = ','.join(random_tags)

    obj, created = CustomUser.objects.get_or_create(
        user_id=email_prefix,
        defaults={
            'name': email_prefix,
            'password': make_password(None),
            'tags': tags_str,
            'profile': '',
            'city': 'Penn',
            'state': 'PA',
            'email': user.email,
        }
    )
    if created:
        logger.info(f"Created CustomUser for {user.email}")
    else:
        logger.info(f"CustomUser already exists for {user.email}")