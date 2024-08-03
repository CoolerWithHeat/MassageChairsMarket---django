from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

class HasToBeAdmin(BasePermission):

    def has_permission(self, request, token):
        token = request.headers.get('Authorization', None)

        if not token:
            raise AuthenticationFailed('Authorization header is missing.')

        # Ensure the header starts with 'Bearer '
        if not token.startswith('Bearer '):
            raise AuthenticationFailed('Authorization header must start with Bearer.')

        # Extract the token from the header
        token = token[len('Bearer '):]

        try:
            # Check if the token is valid
            token_obj = Token.objects.get(key=token)
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')

        # Retrieve the user associated with the token
        user = token_obj.user

        # Check if the user is an admin
        if not user.is_superuser:
            return False


        return True