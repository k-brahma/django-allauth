from django.test import TestCase
from django.test.utils import override_settings

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from allauth.tests import Mock, TestCase, patch
from allauth.utils import get_user_model


class AutoConnectFlowTests(TestCase):
    def setUp(self):
        super().setUp()
        self.email = "user@example.com"
        self.user = get_user_model().objects.create_user(
            "user", email=self.email, password="password"
        )
        self.email_obj = EmailAddress.objects.create(
            user=self.user, email=self.email, primary=True, verified=True
        )
        self.request = Mock()
        self.sociallogin = Mock()
        self.sociallogin.email_addresses = [Mock(email=self.email, verified=True)]
        self.sociallogin.is_existing = False

    @override_settings(SOCIALACCOUNT_AUTO_CONNECT_BY_EMAIL=True)
    def test_auto_connect_enabled(self):
        from allauth.account.internal.flows.connect import AutoConnectFlow

        flow = AutoConnectFlow(self.request, self.sociallogin)
        self.assertTrue(flow.execute())
        self.assertEqual(self.sociallogin.connect.call_count, 1)

    @override_settings(SOCIALACCOUNT_AUTO_CONNECT_BY_EMAIL=False)
    def test_auto_connect_disabled(self):
        from allauth.account.internal.flows.connect import AutoConnectFlow

        flow = AutoConnectFlow(self.request, self.sociallogin)
        self.assertFalse(flow.execute())
        self.assertEqual(self.sociallogin.connect.call_count, 0)

    @override_settings(
        SOCIALACCOUNT_AUTO_CONNECT_BY_EMAIL=True,
        SOCIALACCOUNT_AUTO_CONNECT_VERIFIED_ONLY=True,
    )
    def test_auto_connect_verified_only(self):
        from allauth.account.internal.flows.connect import AutoConnectFlow

        self.sociallogin.email_addresses[0].verified = False
        flow = AutoConnectFlow(self.request, self.sociallogin)
        self.assertFalse(flow.execute())
        self.assertEqual(self.sociallogin.connect.call_count, 0) 