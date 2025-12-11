from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        # 1. Try to find the user by their email address
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        
        # 2. Check if the found user's password is correct
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None