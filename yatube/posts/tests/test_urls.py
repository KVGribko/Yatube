from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='user_for_testing')

        cls.post = Post.objects.create(
            author=cls.user,
            text='текст поста'
        )
        cls.group = Group.objects.create(
            title='Группа для теста',
            slug='group_test',
            description='Описание'
        )

        cls.INDEX = '/'
        cls.GROUP_LIST = f'/group/{cls.group.slug}/'
        cls.PROFILE = f'/profile/{cls.user.username}/'
        cls.POST_DETAIL = f'/posts/{cls.post.id}/'
        cls.UNEXISTING_PAGE = '/unexisting_page/'
        cls.POST_EDIT = f'/posts/{cls.post.id}/edit/'
        cls.CREATE = '/create/'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_public_urls_stasus_code(self):
        '''Проверка общедоступных страниц'''
        url_code = {
            self.INDEX: HTTPStatus.OK,
            self.GROUP_LIST: HTTPStatus.OK,
            self.PROFILE: HTTPStatus.OK,
            self.POST_DETAIL: HTTPStatus.OK,
            self.UNEXISTING_PAGE: HTTPStatus.NOT_FOUND,
        }

        for url, status_code in url_code.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_urls_uses_correct_template(self):
        '''URL-адрес использует соответствующий шаблон'''
        url_templates_names = {
            self.INDEX: 'posts/index.html',
            self.GROUP_LIST: 'posts/group_list.html',
            self.PROFILE: 'posts/profile.html',
            self.POST_DETAIL: 'posts/post_detail.html',
            self.POST_EDIT: 'posts/create_post.html',
            self.CREATE: 'posts/create_post.html',
            self.UNEXISTING_PAGE: 'core/404.html',
        }

        for url, template in url_templates_names.items():
            with self.subTest(url=url, template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_editing_available_to_the_author(self):
        '''Страница редактирования поста доступна автору'''
        response = self.authorized_client.get(self.POST_EDIT)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_creating_post_avalible_to_an_authorized_user(self):
        '''Страница создания поста доступна авторизованному пользлователю'''
        response = self.authorized_client.get(self.CREATE)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_anonymous_user(self):
        '''Проверка редиректа анонимного пользоватял на страницу логина'''
        urls = [
            self.POST_EDIT,
            self.CREATE
        ]
        redirect_url = '/auth/login/'
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, f'{redirect_url}?next={url}')
