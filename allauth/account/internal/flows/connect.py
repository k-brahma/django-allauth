from allauth.account.internal.flows import Flow
from allauth.account.utils import user_email
from allauth.utils import get_user_model


class AutoConnectFlow(Flow):
    """Flow for automatically connecting social accounts to existing users."""

    def __init__(self, request, sociallogin):
        self.request = request
        self.sociallogin = sociallogin

    def is_auto_connect_allowed(self):
        """Check if auto-connect is allowed based on settings and conditions."""
        from allauth.socialaccount import app_settings

        if not app_settings.AUTO_CONNECT_BY_EMAIL:
            return False

        if not self.sociallogin.email_addresses or not self.sociallogin.email_addresses[0]:
            return False

        if self.sociallogin.is_existing:
            return False

        email = self.sociallogin.email_addresses[0]
        if app_settings.AUTO_CONNECT_VERIFIED_ONLY and not email.verified:
            return False

        return True

    def execute(self):
        """Execute the auto-connect flow."""
        if not self.is_auto_connect_allowed():
            return False

        email = self.sociallogin.email_addresses[0]
        try:
            user = get_user_model().objects.get(email=email.email)
            self.sociallogin.connect(self.request, user)
            return True
        except get_user_model().DoesNotExist:
            return False 