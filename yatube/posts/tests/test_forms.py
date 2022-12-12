import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class FormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='user_for_testing')

        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост для тестов',
        )

        cls.POST_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.pk}
        )
        cls.USERS_LOGIN = reverse('users:login')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormsPostsTest(FormsTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.POST_PROFILE = reverse(
            'posts:profile', kwargs={'username': cls.user.username}
        )
        cls.POST_CREATE = reverse('posts:post_create')
        cls.POST_EDIT = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.pk}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_new_post(self):
        '''Проверка создния нового поста'''
        post_count = Post.objects.count()

        bytes_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image = SimpleUploadedFile(
            name='new_create.gif',
            content=bytes_image,
            content_type='image/gif',
        )

        new_post = {
            'author': self.user,
            'text': 'Новый пост для тестов',
            'image': image,
        }
        response = self.authorized_client.post(
            self.POST_CREATE,
            data=new_post,
            follow=True
        )

        self.assertRedirects(response, self.POST_PROFILE)
        self.assertEqual(Post.objects.count(), post_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text=new_post['text'],
                group=None,
                author=new_post['author'],
                image=f"posts/{new_post['image']}",
            ).exists()
        )

    def test_edit_post(self):
        '''Проверка редактирования поста'''
        post_count = Post.objects.count()

        edit_post = {
            'text': 'Измененный пост для тестов'
        }

        response = self.authorized_client.post(
            self.POST_EDIT,
            data=edit_post,
            follow=True
        )

        self.assertRedirects(response, self.POST_DETAIL)

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
            self.POST_CREATE,
            data=new_post,
            follow=True
        )
        self.assertRedirects(response,
                             (
                                 self.USERS_LOGIN
                                 + '?next='
                                 + self.POST_CREATE
                             )
                             )
        self.assertEqual(Post.objects.count(), post_count)

        self.assertFalse(
            Post.objects.filter(
                text=new_post['text'],
                group=None,
                author=new_post['author'],
            ).exists()
        )


class TestComments(FormsTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.comment = Comment.objects.create(
            text='комментарий',
            author=cls.user,
            post=cls.post,
        )

        cls.ADD_COMMENT = reverse(
            'posts:add_comment',
            kwargs={'post_id': cls.post.id},
        )

    def test_create_comment(self):
        '''Авторизованный пользователь может создать комментарий'''
        commets_count = self.post.comments.count()
        comments = {
            'text': 'Первый',
            'author': self.user,
            'post': self.post,
        }
        response = self.authorized_client.post(
            self.ADD_COMMENT,
            data=comments,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL)
        self.assertEqual(self.post.comments.count(), commets_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=comments['text'],
                author=self.user,
                post=self.post,
            ).exists()
        )

    def test_unauthorized_user_cannot_create_comment(self):
        '''Неавторизованный пользователь не может оставить комментарий'''
        commets_count = self.post.comments.count()
        comments = {
            'text': 'Первый',
            'author': self.user,
            'post': self.post,
        }
        response = self.guest_client.post(
            self.ADD_COMMENT,
            data=comments,
            follow=True
        )
        self.assertRedirects(response,
                             (
                                 reverse('users:login')
                                 + '?next='
                                 + self.ADD_COMMENT
                             )
                             )
        self.assertEqual(self.post.comments.count(), commets_count)
        self.assertFalse(
            Comment.objects.filter(
                text=comments['text'],
                author=self.user,
                post=self.post,
            ).exists()
        )

    def test_comment_display(self):
        '''Проверка отображения комментария на сранице'''
        response = self.guest_client.get(self.POST_DETAIL)
        self.assertContains(response, self.comment)
