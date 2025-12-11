# accounts/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q 

class DualFieldBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        print(f"\n--- AUTH DEBUG START ---")
        print(f"1. Input Credential (Email/User): {username}")
        
        user = None
        # 1. Define the query: Try to find the user by email OR by username
        try:
            user = UserModel.objects.get(
                Q(email__iexact=username) | Q(username__iexact=username)
            )
            print(f"2. User Found: Yes (ID: {user.id}, Username: {user.username}, Email: {user.email})")
            
        except UserModel.DoesNotExist:
            print(f"2. User Found: NO (Match not found in email or username fields)")
            return None
        
        # 2. Check the password
        if user is not None:
            
            # Use check_password() to compare submitted password with stored hash
            password_matches = user.check_password(password)
            
            print(f"3. Password Check Result: {password_matches}")
            print(f"4. User is Active: {user.is_active}")
            
            if password_matches and user.is_active:
                print(f"--- AUTH SUCCESSFUL ---")
                return user
                
        print(f"--- AUTH FAILED ---")
        return None