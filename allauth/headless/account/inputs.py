from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import validate_email

from allauth.account import app_settings as account_settings
from allauth.account.adapter import get_adapter as get_account_adapter
from allauth.account.forms import (
    AddEmailForm,
    BaseSignupForm,
    ConfirmLoginCodeForm,
    ReauthenticateForm,
    RequestLoginCodeForm,
    ResetPasswordForm,
    UserTokenForm,
)
from allauth.account.internal import flows
from allauth.account.internal.textkit import compare_code
from allauth.account.models import (
    EmailAddress,
    Login,
    get_emailconfirmation_model,
)
from allauth.core import context
from allauth.headless.adapter import get_adapter
from allauth.headless.internal.restkit import inputs


class SignupInput(BaseSignupForm, inputs.Input):
    password = inputs.CharField()

    def clean_password(self):
        password = self.cleaned_data["password"]
        return get_account_adapter().clean_password(password)


class LoginInput(inputs.Input):
    username = inputs.CharField(required=False)
    email = inputs.EmailField(required=False)
    password = inputs.CharField()

    def clean(self):
        cleaned_data = super().clean()
        username = None
        email = None

        if account_settings.LOGIN_METHODS == {account_settings.LoginMethod.USERNAME}:
            username = cleaned_data.get("username")
            missing_field = "username"
        elif account_settings.LOGIN_METHODS == {account_settings.LoginMethod.EMAIL}:
            email = cleaned_data.get("email")
            missing_field = "email"
        elif account_settings.LOGIN_METHODS == {
            account_settings.LoginMethod.USERNAME,
            account_settings.LoginMethod.EMAIL,
        }:
            username = cleaned_data.get("username")
            email = cleaned_data.get("email")
            missing_field = "email"
            if email and username:
                raise get_adapter().validation_error("email_or_username")
        else:
            raise ImproperlyConfigured(account_settings.LOGIN_METHODS)

        if not email and not username:
            if not self.errors.get(missing_field):
                self.add_error(
                    missing_field, get_adapter().validation_error("required")
                )

        password = cleaned_data.get("password")
        if password and (username or email):
            credentials = {"password": password}
            if email:
                credentials["email"] = email
                auth_method = account_settings.AuthenticationMethod.EMAIL
            else:
                credentials["username"] = username
                auth_method = account_settings.AuthenticationMethod.USERNAME
            user = get_account_adapter().authenticate(context.request, **credentials)
            if user:
                self.login = Login(user=user, email=credentials.get("email"))
                if flows.login.is_login_rate_limited(context.request, self.login):
                    raise get_account_adapter().validation_error(
                        "too_many_login_attempts"
                    )
            else:
                error_code = "%s_password_mismatch" % auth_method.value
                self.add_error(
                    "password", get_account_adapter().validation_error(error_code)
                )
        return cleaned_data


class VerifyEmailInput(inputs.Input):
    key = inputs.CharField()

    def __init__(self, *args, **kwargs):
        self.process = kwargs.pop("process", None)
        super().__init__(*args, **kwargs)

    def clean_key(self):
        key = self.cleaned_data["key"]
        if self.process:
            if not compare_code(actual=key, expected=self.process.code):
                raise get_account_adapter().validation_error("incorrect_code")
            valid = True
            email_address = self.process.email_address
        else:
            model = get_emailconfirmation_model()
            verification = model.from_key(key)
            valid = verification and not verification.key_expired()
            if not valid:
                raise get_account_adapter().validation_error(
                    "incorrect_code"
                    if account_settings.EMAIL_VERIFICATION_BY_CODE_ENABLED
                    else "invalid_or_expired_key"
                )
            email_address = verification.email_address
            self.verification = verification
        if valid and not email_address.can_set_verified():
            raise get_account_adapter().validation_error("email_taken")
        return key


class RequestPasswordResetInput(ResetPasswordForm, inputs.Input):
    pass


class ResetPasswordKeyInput(inputs.Input):
    key = inputs.CharField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.code = kwargs.pop("code", None)
        super().__init__(*args, **kwargs)

    def clean_key(self):
        if account_settings.PASSWORD_RESET_BY_CODE_ENABLED:
            return self._clean_key_code()
        else:
            return self._clean_key_link()

    def _clean_key_code(self):
        key = self.cleaned_data["key"]
        if not compare_code(actual=key, expected=self.code):
            raise get_account_adapter().validation_error("incorrect_code")
        return key

    def _clean_key_link(self):
        key = self.cleaned_data["key"]
        uidb36, _, subkey = key.partition("-")
        token_form = UserTokenForm(data={"uidb36": uidb36, "key": subkey})
        if not token_form.is_valid():
            raise get_account_adapter().validation_error("invalid_password_reset")
        self.user = token_form.reset_user
        return key


class ResetPasswordInput(ResetPasswordKeyInput):
    password = inputs.CharField()

    def clean(self):
        cleaned_data = super().clean()
        password = self.cleaned_data.get("password")
        if self.user and password is not None:
            try:
                get_account_adapter().clean_password(password, user=self.user)
            except ValidationError as e:
                self.add_error("password", e)
        return cleaned_data


class ChangePasswordInput(inputs.Input):
    current_password = inputs.CharField(required=False)
    new_password = inputs.CharField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["current_password"].required = self.user.has_usable_password()

    def clean_current_password(self):
        current_password = self.cleaned_data["current_password"]
        if current_password:
            if not self.user.check_password(current_password):
                raise get_account_adapter().validation_error("enter_current_password")
        return current_password

    def clean_new_password(self):
        new_password = self.cleaned_data["new_password"]
        adapter = get_account_adapter()
        return adapter.clean_password(new_password, user=self.user)


class AddEmailInput(AddEmailForm, inputs.Input):
    pass


class SelectEmailInput(inputs.Input):
    email = inputs.CharField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"]
        validate_email(email)
        try:
            return EmailAddress.objects.get_for_user(user=self.user, email=email)
        except EmailAddress.DoesNotExist:
            raise get_adapter().validation_error("unknown_email")


class DeleteEmailInput(SelectEmailInput):
    def clean_email(self):
        email = super().clean_email()
        if not flows.manage_email.can_delete_email(email):
            raise get_account_adapter().validation_error("cannot_remove_primary_email")
        return email


class MarkAsPrimaryEmailInput(SelectEmailInput):
    primary = inputs.BooleanField(required=True)

    def clean_email(self):
        email = super().clean_email()
        if not flows.manage_email.can_mark_as_primary(email):
            raise get_account_adapter().validation_error("unverified_primary_email")
        return email


class ReauthenticateInput(ReauthenticateForm, inputs.Input):
    pass


class RequestLoginCodeInput(RequestLoginCodeForm, inputs.Input):
    pass


class ConfirmLoginCodeInput(ConfirmLoginCodeForm, inputs.Input):
    pass
