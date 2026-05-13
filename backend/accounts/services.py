# accounts/services.py
# All authentication business logic lives here.
# Views call services. Services never import from views.

import logging
from django.contrib.auth import get_user_model
from django.db import IntegrityError

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthService:

    @staticmethod
    def register_user(email: str, password: str, full_name: str = "") -> User:
        """
        Creates a new user account.
        Raises ValueError on duplicate email or weak input.
        """
        email = email.strip().lower()

        if User.objects.filter(email=email).exists():
            raise ValueError("An account with this email already exists.")

        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name.strip(),
            )
            logger.info(f"New user registered: {email}")
            return user

        except IntegrityError:
            # Race condition safety net
            raise ValueError("An account with this email already exists.")

    @staticmethod
    def get_user_by_id(user_id) -> User:
        """
        Fetches a user by UUID. Returns None if not found.
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None