from random import choice
from string import ascii_letters

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    POST_TEXT = ''.join(choice(ascii_letters) for i in range(150))

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='группа для теста',
            slug='group_test',
            description='Описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=cls.POST_TEXT
        )

    def test_verbose_name(self):
        '''Проверка полей verbose_name модели Post'''
        verboses = {
            'text': 'текст поста',
            'created': 'дата публикации',
            'author': 'автор',
            'group': 'группа',
        }

        for value, expected in verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).verbose_name, expected
                )

    def test_help_text(self):
        '''Проверка полей help_text модели Post'''
        help_texts = {
            'text': 'введите тескт поста',
            'group': 'группа, к которой будет относиться пост',
        }
        for value, expected in help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).help_text, expected
                )

    def test_correct_object_names(self):
        '''Проверка корректной работы __str__ модели Post'''
        post_text = str(self.post)
        expected_post_text = self.POST_TEXT[:15]
        self.assertEqual(post_text, expected_post_text)


class GroupModelTest(TestCase):
    GROUP_TITLE = 'Группа для теста'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title=cls.GROUP_TITLE,
            slug='Cлаг',
            description='Описание'
        )

    def test_verbose_name(self):
        '''Проверка полей verbose_name модели Group'''
        verboses = {
            'title': 'название группы',
            'description': 'описание группы'
        }

        for value, expected in verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.group._meta.get_field(value).verbose_name, expected
                )

    def test_help_text(self):
        '''Проверка полей help_text модели Group'''
        help_texts = {
            'title': 'введите название группы',
            'description': 'введите описание группы'
        }

        for value, expected in help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.group._meta.get_field(value).help_text, expected
                )

    def test_correct_object_names(self):
        '''Проверка корректной работы __str__ модели Group'''
        group_title = str(self.group)
        self.assertEqual(group_title, self.GROUP_TITLE)
