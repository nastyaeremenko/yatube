from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug'
        )

        Post.objects.create(
            text='Тестовый текст',
            author=self.user
        )

        user2 = User.objects.create_user(username='test_author')

        Post.objects.create(
            text='Тестовый текст',
            author=user2
        )

        self.templates_url_names = {
            '/': 'posts/index.html',
            '/new/': 'posts/new_post.html',
            '/group/test-slug/': 'posts/group.html',
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
            '/test_user/': 'posts/profile.html',
            '/test_user/1/': 'posts/post.html',
            '/test_user/1/edit/': 'posts/new_post.html',
            '/follow/': 'posts/follow.html',
        }

        self.code_url_names = {
            '/': 200,
            '/new/': 302,
            '/group/test-slug/': 200,
            '/about/author/': 200,
            '/about/tech/': 200,
            '/test_user/': 200,
            '/test_user/1/': 200,
            '/test_user/1/edit/': 302,
            '/404/': 404,
            '/follow/': 302,
            '/test_user/follow/': 302,
            '/test_user/unfollow/': 302
        }

    def test_urls_exists_at_desired_location(self):
        """Доступ к страницам для неавторизованного пользователю."""
        for reverse_name, code in self.code_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                error = (
                    f'Страница {reverse_name} имеет код '
                    f'{response.status_code} для неавторизованного '
                    f'пользователя, ожидался {code}'
                )
                self.assertEqual(response.status_code, code, error)

    def test_new_post_author_exists_at_desired_location(self):
        """Страница /test_user/1/edit/ доступна авторизованному автору."""
        response = self.authorized_client.get('/test_user/1/edit/')
        self.assertEqual(response.status_code, 200)

    def test_new_post_no_author_exists_at_desired_location(self):
        """
        Страница /test_author/2/edit/ не доступна пользователю test_user.
        """
        response = self.authorized_client.get('/test_author/2/edit/')
        self.assertEqual(response.status_code, 302)

    def test_edit_post_exists_at_desired_location(self):
        """Страница /new/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, 200)

    def test_new_post_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /new/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/new/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/new/'
        )

    def test_edit_post_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /test_user/1/edit/ перенаправит
        анонимного пользователя на страницу логина.
        """
        response = self.guest_client.get('/test_user/1/edit/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/test_user/1/edit/'
        )

    def test_urls_user_correct_template(self):
        """Страницы используют корректный шаблон"""
        for reverse_name, template in self.templates_url_names.items():
            with self.subTest(reverse_name=reverse_name, template=template):
                response = self.authorized_client.get(reverse_name)
                error = f'Неккорректный шаблон для страницы {reverse_name}'
                self.assertTemplateUsed(response, template, error)
