from django.db import models

# Create your models here.
class UserInfo(models.Model):
    user_id = models.CharField(primary_key=True, max_length=20)
    user_name = models.CharField(max_length=20)
    user_password = models.CharField(max_length=20)

