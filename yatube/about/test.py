from http import HTTPStatus
from django.urls import reverse

from django.test import Client, TestCase


class AboutTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_urls(self):
        '''Проверка достпуности страниц about'''
        urls = [
            '/about/author/',
            '/about/tech/'
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_templates(self):
        '''Проверка шаблоов about'''
        url_templates = {
            '/about/author/': 'about/about.html',
            '/about/tech/': 'about/tech.html'
        }

        for url, template in url_templates.items():
            with self.subTest(url=url, template=template):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_namespace(self):
        '''Проверка namespase:name'''
        urls = [
            reverse('about:author'),
            reverse('about:tech')
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
