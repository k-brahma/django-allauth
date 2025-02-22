SOCIALACCOUNT_AUTO_CONNECT_BY_EMAIL (=False)
    When enabled, if a user attempts to login with a social account that has an
    email address matching an existing user account, the social account will be
    automatically connected to that existing user account. This simplifies the
    user experience by avoiding the need for manual account connection when
    email addresses match.

SOCIALACCOUNT_AUTO_CONNECT_VERIFIED_ONLY (=True)
    When SOCIALACCOUNT_AUTO_CONNECT_BY_EMAIL is enabled, this setting controls
    whether the auto-connection should only occur when the email address from
    the social account is verified. This adds an extra layer of security by
    ensuring that only verified email addresses can trigger automatic account
    connection. 
