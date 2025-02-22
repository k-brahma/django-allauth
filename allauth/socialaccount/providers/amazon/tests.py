from django.test import TestCase

from allauth.socialaccount.tests import OAuth2TestsMixin
from allauth.tests import MockedResponse

from .provider import AmazonProvider


class AmazonTests(OAuth2TestsMixin, TestCase):
    provider_id = AmazonProvider.id

    def get_mocked_response(self):
        return MockedResponse(
            200,
            """
        {
          "Profile":{
                        "CustomerId":"amzn1.account.K2LI23KL2LK2",
                        "Name":"John Doe",
                        "PrimaryEmail":"johndoe@example.com"
                    }
        }""",
        )

    def get_expected_to_str(self):
        return "johndoe@example.com"
