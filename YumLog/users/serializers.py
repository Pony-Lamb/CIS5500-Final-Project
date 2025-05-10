from rest_framework import serializers
import re
from .models import users

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6)
    tags = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value):
        import re
        if not re.fullmatch(r'[a-zA-Z0-9]{3,20}', value):
            raise serializers.ValidationError("用户名必须是3-20位字母或数字")
        return value

    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("密码至少6位")
        return value


    def validate_username(self, value):
        # length between 3-20, only number and character
        if not re.fullmatch(r'[a-zA-Z0-9]{3,20}', value):
            raise serializers.ValidationError("Username must be 3-20 characters long and contain only letters and numbers.")
        return value

    def validate_email(self, value):
        # email with specific domains
        allowed_domains = ['com', 'edu', 'org', 'net']
        if not any(value.endswith(f".{d}") for d in allowed_domains):
            raise serializers.ValidationError("Email must end with .com, .edu, .org, or .net")
        return value

    def validate_password(self, value):
        # at least 6, with both numbers and characters
        if len(value) < 6 or not re.search(r'[a-zA-Z]', value) or not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must be at least 6 characters and include both letters and numbers.")
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


