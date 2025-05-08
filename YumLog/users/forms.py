from allauth.socialaccount.forms import SignupForm
from django import forms
from .models import users as CustomUser

class CustomSocialSignupForm(SignupForm):
    TAG_CHOICES = [
        ('American','American'),
        ('Burgers','Burgers'),
        ('Fast Food','Fast Food'),
        ('Mexican','Mexican'),
        ('Asian','Asian'),
        ('Pizza','Pizza'),
        ('Desserts','Desserts'),
        ('Seafood','Seafood'),
        ('Sushi','Sushi'),
        ('Vegetarian Friendly','Vegetarian Friendly'),
    ]
    tags = forms.MultipleChoiceField(
        choices=TAG_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Favorite cuisines'
    )

    def clean_email(self):
        # Allow existing emails to pass through for social signup
        return self.cleaned_data.get('email')

    def save(self, request):
        user = super().save(request)
        email_prefix = user.email.split('@')[0]
        cu, created = CustomUser.objects.update_or_create(
            user_id=email_prefix,
            defaults={'email': user.email}
        )
        cu.tags = ','.join(self.cleaned_data.get('tags', []))
        cu.save()
        return user