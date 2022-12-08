from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post

User = get_user_model()


class FormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='user_for_testing')

        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост для тестов'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_new_post(self):
        '''Проверка создния нового поста'''
        post_count = Post.objects.count()
        new_post = {
            'author': self.user,
            'text': 'Новый пост для тестов'
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=new_post,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}
        ))
        self.assertEqual(Post.objects.count(), post_count + 1)

        new_post_from_db = self.user.posts.first()
        self.assertEqual(new_post_from_db.text, new_post['text'])
        self.assertIsNone(new_post_from_db.group)
        self.assertEqual(new_post_from_db.author, self.user)

    def test_edit_post(self):
        '''Проверка редактирования поста'''
        post_count = Post.objects.count()

        edit_post = {
            'text': 'Измененный пост для тестов'
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=edit_post,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        ))

        self.assertEqual(Post.objects.count(), post_count)

        edit_post_from_db = self.user.posts.get(pk=self.post.pk)
        self.assertEqual(edit_post_from_db.text, edit_post['text'])
        self.assertIsNone(edit_post_from_db.group)
        self.assertEqual(edit_post_from_db.author, self.user)

    def test_unauthorized_user_cannot_create_post(self):
        '''Неавторизованный пользователь не может опубликовать пост'''
        post_count = Post.objects.count()
        new_post = {
            'author': self.user,
            'text': 'Новый пост для тестов неавторизованного пользователя'
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=new_post,
            follow=True
        )
        self.assertRedirects(response,
                             (
                                 reverse('users:login')
                                 + '?next='
                                 + reverse('posts:post_create')
                             )
                             )
        self.assertEqual(Post.objects.count(), post_count)
