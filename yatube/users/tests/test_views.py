from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

User = get_user_model()


class UsersViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='user_for_testing')

        cls.LOGOUT = reverse('users:logout')
        cls.LOGIN = reverse('users:login')
        cls.SIGNUP = reverse('users:signup')
        cls.PASSWORD_RESET = reverse('users:password_reset')
        cls.PASSWORD_RESET_DONE = reverse('users:password_reset_done')
        cls.PASSWORD_RESET_CONFIRM = reverse(
            'users:password_reset_confirm',
            kwargs={'uidb64': 'uidb64', 'token': 'token'}
        )
        cls.PASSWORD_RESET_COMPLETE = reverse('users:password_reset_complete')

        cls.LOGOUT_HTML = 'users/logged_out.html'
        cls.LOGIN_HTML = 'users/login.html'
        cls.SIGNUP_HTML = 'users/signup.html'
        cls.PASSWORD_RESET_HTML = 'users/password_reset_form.html'
        cls.PASSWORD_RESET_DONE_HTML = 'users/password_reset_done.html'
        cls.PASSWORD_RESET_CONFIRM_HTML = 'users/password_reset_confirm.html'
        cls.PASSWORD_RESET_COMPLETE_HTML = 'users/password_reset_complete.html'

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.guest_client = Client()

    def test_public_urls_status_code(self):
        '''view-функции используют правильные html-шаблоны'''
        url_templates_names = {
            self.LOGOUT: self.LOGOUT_HTML,
            self.LOGIN: self.LOGIN_HTML,
            self.SIGNUP: self.SIGNUP_HTML,
            self.PASSWORD_RESET: self.PASSWORD_RESET_HTML,
            self.PASSWORD_RESET_DONE: self.PASSWORD_RESET_DONE_HTML,
            self.PASSWORD_RESET_CONFIRM: self.PASSWORD_RESET_CONFIRM_HTML,
            self.PASSWORD_RESET_COMPLETE: self.PASSWORD_RESET_COMPLETE_HTML,
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url, template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_correct_signup_context(self):
        """Шаблон signup сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField
        }
        for value, expected_type in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected_type)
