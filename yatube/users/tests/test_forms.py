from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class FormsTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_user_create(self):
        '''Проверка создания новго пользователя'''
        users_count = User.objects.count()

        username = 'new_test_user'
        new_user = {
            'password1': '3n3N!7tWh8RC3Lv',
            'password2': '3n3N!7tWh8RC3Lv',
            'username': username,

        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=new_user,
            follow=True
        )

        self.assertRedirects(response, reverse('posts:index'))

        self.assertEqual(User.objects.count(), users_count + 1)

        self.assertTrue(User.objects.filter(username=username).exists())
