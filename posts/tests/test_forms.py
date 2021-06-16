import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

User = get_user_model()


class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.form = PostForm()
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user
        )

    def test_create_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_edit_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group.id,
            'text': 'Новый тестовый текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('post_edit',
                    kwargs={'username': 'test_user',
                            'post_id': self.post.id}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(
                'post',
                kwargs={'username': 'test_user',
                        'post_id': self.post.id}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(self.user.posts.get(id=1).text,
                         'Новый тестовый текст')


class CommentFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.form = CommentForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user
        )

    def test_write_comment(self):
        comments_count = Comment.objects.count()

        form_data = {
            'text': 'Комментарий',
        }

        self.authorized_client.post(
            reverse('add_comment',
                    kwargs={'username': 'test_user',
                            'post_id': self.post.id}),
            data=form_data,
            follow=True
        )

        self.assertEqual(
            Comment.objects.count(),
            comments_count + 1,
            'Комментарий не создался'
        )
