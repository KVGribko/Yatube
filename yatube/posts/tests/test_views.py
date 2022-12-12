import shutil
import tempfile
from math import ceil

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class ViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='user_for_testing')

        cls.group = Group.objects.create(
            title='Группа для теста',
            slug='group_test',
            description='Описание'
        )

        cls.INDEX = reverse('posts:index')
        cls.GROUP_LIST = reverse(
            'posts:group_list', kwargs={'slug': cls.group.slug}
        )
        cls.PROFILE = reverse(
            'posts:profile', kwargs={'username': cls.user.username}
        )

        cls.CONTEXT = 'page_obj'

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(ViewTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        bytes_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='view_test.gif',
            content=bytes_image,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text=f'Пост для тестов №{0}',
            group=cls.group,
            image=cls.image,
        )

        cls.POST_DETAIL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.id}
        )
        cls.CREATE = reverse('posts:post_create')
        cls.FOLLOW = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.user.username},
        )
        cls.UNFOLLOW = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.user.username},
        )
        cls.FOLLOW_INDEX = reverse('posts:follow_index')

        cls.INDEX_HTML = 'posts/index.html'
        cls.GROUP_LIST_HTML = 'posts/group_list.html'
        cls.PROFILE_HTML = 'posts/profile.html'
        cls.POST_DETAIL_HTML = 'posts/post_detail.html'
        cls.POST_CREATE_EDIT_HTML = 'posts/create_post.html'
        cls.FOLLOW_INDEX_HTML = 'posts/follow.html'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        cache.clear()

    def test_templates(self):
        '''view-функции используют правильные html-шаблоны'''
        page_template = {
            self.INDEX: self.INDEX_HTML,
            self.GROUP_LIST: self.GROUP_LIST_HTML,
            self.PROFILE: self.PROFILE_HTML,
            self.POST_DETAIL: self.POST_DETAIL_HTML,
            self.POST_EDIT: self.POST_CREATE_EDIT_HTML,
            self.CREATE: self.POST_CREATE_EDIT_HTML,
            self.FOLLOW_INDEX: self.FOLLOW_INDEX_HTML,
        }

        for page, template in page_template.items():
            with self.subTest(page=page, template=template):
                response = self.authorized_client.get(page)
                self.assertTemplateUsed(response, template)

    def test_correct_context(self):
        '''Корректная передача контекста'''
        POST_DETAIL_CONTEXT = 'post'
        urls_context_name = {
            self.INDEX: self.CONTEXT,
            self.GROUP_LIST: self.CONTEXT,
            self.PROFILE: self.CONTEXT,
            self.POST_DETAIL: POST_DETAIL_CONTEXT,
        }

        for url, context_name in urls_context_name.items():
            with self.subTest(url=url, context_name=context_name):
                response = self.authorized_client.get(url)
                if context_name == POST_DETAIL_CONTEXT:
                    post = response.context[context_name]
                else:
                    post = response.context[context_name][0]
                self.assertEqual(post.author, self.user)
                self.assertEqual(post.group, self.group)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.image, self.post.image)

    def test_correct_form_context(self):
        '''Корректная передача контекста в формах'''
        create_form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        urls_field = {
            self.CREATE: create_form_fields,
            self.POST_EDIT: create_form_fields
        }

        for url, fields in urls_field.items():
            response = self.authorized_client.get(url)
            for name, expected_type in fields.items():
                with self.subTest(
                    url=url,
                    name=name,
                    expected_type=expected_type
                ):
                    form_field = response.context['form'].fields[name]
                    self.assertIsInstance(form_field, expected_type)

    def test_correct_appearance_post(self):
        '''Новый пост попал в группу, для которой был предназначен'''
        new_post = Post.objects.create(
            author=self.user,
            group=self.group,
            text='Другой новыйы пост'
        )

        urls = [
            self.INDEX,
            self.GROUP_LIST,
            self.PROFILE,
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                page_obj = response.context[self.CONTEXT]
                self.assertIn(new_post, page_obj)

    def test_not_appearint_post_in_other_place(self):
        '''Новый пост не попал в группу, для которой не был предназначен'''
        other_group = Group.objects.create(
            title='Еще одна Другая Группа для теста',
            slug='other_group_test',
            description='Описание еще одной другой группы'
        )
        other_user = User.objects.create_user(username='other_test_user')

        new_post = Post.objects.create(
            author=other_user,
            group=other_group,
            text='Еще один Другой новыйы пост'
        )

        urls = [
            self.GROUP_LIST,
            self.PROFILE,
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                page_obj = response.context[self.CONTEXT]
                self.assertNotIn(new_post, page_obj)

    def test_commet_create(self):
        '''Проверка создания комменатрия'''
        commets_count = self.post.comments.count()
        comment = Comment.objects.create(
            text='комментарий',
            author=self.user,
            post=self.post,
        )
        self.assertEqual(self.post.comments.count(), commets_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=comment.text,
                author=self.user,
                post=self.post,
            ).exists()
        )

    def test_index_cache(self):
        '''Проверка кэширования главной страницы'''
        post_count = Post.objects.count()
        post = Post.objects.create(
            author=self.user,
            text='проверка кэша'
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        response = self.guest_client.get(self.INDEX)

        post.delete()
        self.assertEqual(Post.objects.count(), post_count)

        response_after_delete = self.guest_client.get(self.INDEX)
        self.assertEqual(response.content, response_after_delete.content)

        cache.clear()

        response_after_cache_clear = self.guest_client.get(self.INDEX)
        self.assertNotEqual(
            response.content,
            response_after_cache_clear.content,
        )


class PaginatorTest(ViewTest):
    POST_COUNT = settings.OBJECTS_PER_PAGE + 5

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.create_posts()

    @classmethod
    def create_posts(cls):
        posts = list()
        for i in range(cls.POST_COUNT):
            post = Post(
                author=cls.user,
                text=f'Пост для тестов №{i + 1}',
                group=cls.group
            )
            posts.append(post)

        Post.objects.bulk_create(posts)

    @staticmethod
    def posts_in_page(
        page_number,
        total_posts_count,
        posts_per_page=settings.OBJECTS_PER_PAGE
    ):
        max_pages = ceil(total_posts_count / posts_per_page)

        if 0 < page_number < max_pages:
            return posts_per_page

        return (total_posts_count % posts_per_page) or posts_per_page

    def test_paginator(self):
        '''Корректное формирование Paginator'''
        urls = [
            self.INDEX,
            self.GROUP_LIST,
            self.PROFILE,
        ]

        posts_count_in_db = Post.objects.count()
        tested_pages_count = 2
        for url in urls:
            with self.subTest(url=url):
                for i in range(1, tested_pages_count + 1):
                    response = self.authorized_client.get(
                        url + f'?page={i}'
                    )
                    posts_count_in_page = len(response.context[self.CONTEXT])
                    expected_posts_count = self.posts_in_page(
                        i,
                        posts_count_in_db
                    )
                    self.assertEqual(
                        posts_count_in_page,
                        expected_posts_count,
                        msg=(
                            f'\nВсего постов: {posts_count_in_db}'
                            f'\nСтраница: {i}'
                            f'\nПостов на странице: {posts_count_in_page}'
                            f'\nОжидаемое: {expected_posts_count}'
                        )
                    )


class FollowingTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='author')
        cls.follower = User.objects.create_user(username='follower')

        cls.FOLLOW = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.author.username},
        )
        cls.UNFOLLOW = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.author.username},
        )

        cls.FOLLOW_INDEX = reverse('posts:follow_index')
        cls.CONTEXT = 'page_obj'

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

        self.guest_client = Client()

    def test_following(self):
        '''Проверка создания подписки'''
        follow_count = Follow.objects.count()

        self.follower_client.get(self.FOLLOW)

        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.follower,
                author=self.author,
            ).exists()
        )

    def test_unfollow(self):
        '''Проверка отписки'''
        follow_count = Follow.objects.count()

        self.follower_client.get(self.FOLLOW)

        self.assertEqual(Follow.objects.count(), follow_count + 1)

        self.follower_client.get(self.UNFOLLOW)

        self.assertEqual(Follow.objects.count(), follow_count)

        self.assertFalse(
            Follow.objects.filter(
                user=self.follower,
                author=self.author,
            ).exists()
        )

    def test_follow_post(self):
        '''Новая запись пользователя появляется в ленте подписчиков'''
        Follow.objects.create(
            user=self.follower,
            author=self.author,
        )

        new_post = Post.objects.create(
            author=self.author,
            text='Пост для проверки подписки',
        )

        response = self.follower_client.get(self.FOLLOW_INDEX)

        self.assertIn(new_post, response.context[self.CONTEXT])

    def test_unfollow_post(self):
        '''Новая запись пользователя не появляется в ленте не подписчиков'''
        new_post = Post.objects.create(
            author=self.author,
            text='Пост для проверки подписки',
        )

        self.assertFalse(
            Follow.objects.filter(
                user=self.follower,
                author=self.author,
            ).exists()
        )

        response = self.follower_client.get(self.FOLLOW_INDEX)

        self.assertNotIn(new_post, response.context[self.CONTEXT])
