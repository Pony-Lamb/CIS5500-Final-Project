# users/adapter.py
# users/adapter.py
from django.contrib.auth import get_user_model
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
import random
from django.contrib.auth.hashers import make_password

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Auto-link social logins for users that already exist
        with the same email address, instead of throwing email_taken.
        """
        email = sociallogin.user.email
        if not email:
            return
        # Link to existing Django User, not profile table
        UserModel = get_user_model()
        try:
            existing = UserModel.objects.get(email=email)
            sociallogin.connect(request, existing)
        except UserModel.DoesNotExist:
            # No existing Django user with this email, proceed normally
            pass
        
    def save_user(self, request, sociallogin, form=None):
        from django.db import IntegrityError

        try:
            user = super().save_user(request, sociallogin, form)
        except IntegrityError as e:
            # If an EmailAddress already exists and is verified, link it rather than error
            if 'unique_verified_email' in str(e):
                user = sociallogin.user
                # Ensure there's a verified EmailAddress record
                EmailAddress.objects.update_or_create(
                    user=user,
                    email=user.email,
                    defaults={'verified': True, 'primary': True}
                )
            else:
                raise
        return user

    def get_login_redirect_url(self, request):
        from django.urls import reverse
        return reverse('private_index')

    def get_signup_redirect_url(self, request):
        from django.urls import reverse
        return reverse('private_index')

    def get_connect_redirect_url(self, request, socialaccount):
        from django.urls import reverse
        return reverse('private_index')