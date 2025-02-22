Social Accounts
===============

.. toctree::
   :maxdepth: 1

   introduction
   configuration
   provider_configuration
   views
   templates
   forms
   signals
   providers/index
   adapter
   advanced

Auto-Connecting Accounts
~~~~~~~~~~~~~~~~~~~~~

django-allauth can automatically connect social accounts to existing user accounts
based on matching email addresses. This feature is disabled by default but can be
enabled via the ``SOCIALACCOUNT_AUTO_CONNECT_BY_EMAIL`` setting. When enabled,
if a user attempts to login with a social account that has an email address
matching an existing user account, the social account will be automatically
connected to that existing user account.

For security reasons, by default this only works with verified email addresses
from the social account provider. This behavior can be controlled via the
``SOCIALACCOUNT_AUTO_CONNECT_VERIFIED_ONLY`` setting.
