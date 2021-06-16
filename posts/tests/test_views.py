from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug'
        )

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        Post.objects.bulk_create([
            Post(
                text='Тестовый текст',
                author=self.user,
                group=self.group,
                image=self.uploaded,
            ) for i in range(13)
        ])

        Post.objects.bulk_create([
            Post(
                text='Тестовый текст',
                author=self.user,
                image=self.uploaded,
            ) for i in range(3)
        ])

        self.user2 = User.objects.create_user(username='user')
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        Follow.objects.create(
            user=self.user2,
            author=self.user
        )

        self.templates_pages_names = {
            reverse('index'): 'posts/index.html',
            reverse('new_post'): 'posts/new_post.html',
            (reverse('group', kwargs={'slug': 'test-slug'})):
                'posts/group.html',
            (reverse('profile', kwargs={'username': 'test_user'})):
                'posts/profile.html',
            (reverse('post',
                     kwargs={'username': 'test_user',
                             'post_id': 1})):
                'posts/post.html',
            (reverse('post_edit',
                     kwargs={'username': 'test_user',
                             'post_id': 1})):
                'posts/new_post.html',
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
            reverse('follow_index'): 'posts/follow.html',
        }

        self.posts_pages_reverse = [
            reverse('index'),
            (reverse('group', kwargs={'slug': 'test-slug'})),
            (reverse('profile', kwargs={'username': 'test_user'}))
        ]

        self.form_pages_reverse = [
            reverse('new_post'),
            (reverse(
                'post_edit',
                kwargs={'username': 'test_user',
                        'post_id': 1}))
        ]

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name, template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(
                    response, template,
                    'Ожидался другой шаблон'
                )

    def test_some_page_show_correct_context(self):
        """Шаблон index/group/profile сформирован с правильным контекстом."""
        for reverse_name in self.posts_pages_reverse:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post_text_0 = response.context.get('page')[0].text
                post_author_0 = response.context.get('page')[0].author
                post_group_title_9 = (response.context.get('page')
                                      [9].group.title)
                post_pub_date_0 = (response.context.get('page')
                                   [0].pub_date.date())
                post_image_0 = response.context.get('page')[0].image
                today = datetime.utcnow().date()
                self.assertEqual(post_text_0, 'Тестовый текст')
                self.assertEqual(post_author_0, self.user)
                self.assertEqual(post_group_title_9, 'Тестовый заголовок')
                self.assertEqual(post_pub_date_0, today)
                self.assertIsNotNone(post_image_0)

    def test_post_page_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        reverse_name = reverse('post',
                               kwargs={
                                   'username': 'test_user',
                                   'post_id': 14
                               })
        response = self.authorized_client.get(reverse_name)
        post_text = response.context.get('post').text
        post_author = response.context.get('post').author
        post_group_title = response.context.get('post').group
        post_image = response.context.get('post').image
        post_pub_date = response.context.get('post').pub_date.date()
        today = datetime.utcnow().date()
        self.assertEqual(post_text, 'Тестовый текст')
        self.assertEqual(post_author, self.user)
        self.assertEqual(post_group_title, None)
        self.assertIsNotNone(post_image)
        self.assertEqual(post_pub_date, today)

    def test_form_page_show_correct_context(self):
        """Шаблон new_post/post_edit сформирован с правильным контекстом."""
        for reverse_name in self.form_pages_reverse:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                form_group_label = (response.context.get('form')
                                    ['group'].field.label)
                form_text_label = (response.context.get('form')
                                   ['text'].field.label)
                form_group_help_text = (response.context.get('form')
                                        ['group'].field.help_text)
                form_text_help_text = (response.context.get('form')
                                       ['text'].field.help_text)
                form_image = response.context.get('form')['image']
                self.assertEqual(form_group_label, 'Группа')
                self.assertEqual(form_text_label, 'Текст статьи')
                self.assertEqual(
                    form_group_help_text, 'Поле Группа не заполнено'
                )
                self.assertEqual(
                    form_text_help_text,
                    'Добавьте текст статьи'
                )
                self.assertIsNotNone(form_image)

    def test_home_first_page_containse_ten_records(self):
        """На первой странице на главной 10 постов (Paginator)"""
        response = self.client.get(reverse('index'))
        error = 'На первой странице на главной ожидалось другое кол-во постов'
        self.assertEqual(
            len(response.context.get('page').object_list),
            10,
            error
        )

    def test_home_second_page_containse_three_records(self):
        """На второй странице на главной 3 поста (Paginator)"""
        response = self.client.get(reverse('index') + '?page=2')
        error = 'На второй странице на главной ожидалось другое кол-во постов'
        self.assertEqual(
            len(response.context.get('page').object_list),
            6,
            error
        )

    def test_group_first_page_containse_ten_records(self):
        """На первой странице в группе test-slug 10 постов (Paginator)"""
        response = self.client.get(
            reverse('group', kwargs={'slug': 'test-slug'})
        )
        error = 'На первой странице test-slug ожидалось другое кол-во постов'
        self.assertEqual(
            len(response.context.get('page').object_list),
            10,
            error
        )

    def test_group_second_page_containse_three_records(self):
        """На второй странице в группе test-slug 3 поста (Paginator)"""
        response = self.client.get(
            reverse('group', kwargs={'slug': 'test-slug'}) + '?page=2'
        )
        error = 'На второй странице test-slug ожидалось другое кол-во постов'
        self.assertEqual(
            len(response.context.get('page').object_list),
            3,
            error
        )

    def test_profile_first_page_containse_ten_records(self):
        """На первой странице в группе profile 10 постов (Paginator)"""
        response = self.client.get(
            reverse('profile', kwargs={'username': 'test_user'})
        )
        error = 'На первой странице test-slug ожидалось другое кол-во постов'
        self.assertEqual(
            len(response.context.get('page').object_list),
            10,
            error
        )

    def test_profile_second_page_containse_three_records(self):
        """На второй странице в группе profile 6 поста (Paginator)"""
        response = self.client.get(
            reverse('profile', kwargs={'username': 'test_user'}) + '?page=2'
        )
        error = 'На второй странице test-slug ожидалось другое кол-во постов'
        self.assertEqual(
            len(response.context.get('page').object_list),
            6,
            error
        )

    def test_follow_authorized_client(self):
        """Новый авторизованный пользователь подписался на test_user"""
        user = User.objects.create_user(username='test_user2')
        authorized_client = Client()
        authorized_client.force_login(user)

        reverse_name = (
            reverse(
                'profile_follow',
                kwargs={'username': 'test_user'}
            )
        )
        authorized_client.get(reverse_name)

        is_follow = Follow.objects.filter(user=user, author=self.user).exists()
        error = 'Авторизованному пользователю не удалось подписаться на автора'
        self.assertTrue(is_follow, error)

    def test_unfollow_authorized_client(self):
        """test_use2 отписался от test_user"""
        reverse_name = (
            reverse(
                'profile_unfollow',
                kwargs={'username': 'test_user'}
            )
        )
        self.authorized_client2.delete(reverse_name)

        is_follow = Follow.objects.filter(
            user=self.user2,
            author=self.user
        ).exists()
        error = 'Авторизованному пользователю не удалось отписаться от автора'
        self.assertFalse(is_follow, error)

    def test_new_post_follow_author(self):
        """Новый пост test_user появился у
        подписанного пользователя в Избранном"""
        Post.objects.create(
            text='Проверка',
            author=self.user,
            group=self.group,
            image=self.uploaded,
        )
        response = self.authorized_client2.get(reverse('follow_index'))
        post_text_0 = response.context.get('page')[0].text
        error = 'Пост не появился в ленте подпиманного пользователя'
        self.assertEqual(post_text_0, 'Проверка', error)

    def test_new_post_unfollow_author(self):
        """Новый пост test_user не появился у
        неподписанного пользователя в Избранном"""
        user = User.objects.create_user(username='test_user2')
        authorized_client = Client()
        authorized_client.force_login(user)

        Post.objects.create(
            text='Проверка',
            author=self.user,
            group=self.group,
            image=self.uploaded,
        )
        response = authorized_client.get(reverse('follow_index'))
        error = 'Пост появился в ленте неподпиманного пользователя'
        self.assertEqual(
            len(response.context.get('page').object_list),
            0,
            error
        )

    def test_cache(self):
        """Проверка кэширования постов на главной"""
        response_1 = self.client.get(reverse('index'))
        Post.objects.create(
            text='Проверка кэша',
            author=self.user,
            image=self.uploaded,
        )
        response_2 = self.client.get(reverse('index'))
        error = 'Новый пост сразу появился'
        self.assertHTMLEqual(
            str(response_1.content), str(response_2.content), error
        )

        cache.clear()
        response_3 = self.client.get(reverse('index'))
        error = 'Новый пост не появился после очистки кэша'
        self.assertHTMLNotEqual(
            str(response_1.content), str(response_3.content), error
        )
