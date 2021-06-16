from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    def setUp(self):
        user = User.objects.create(username='testuser')

        self.post = Post.objects.create(
                text='Тестовый текст',
                author=user
        )

    def test_verbose_name(self):
        verbose_name_text = self.post._meta.get_field('text').verbose_name
        verbose_name_group = self.post._meta.get_field('group').verbose_name
        verbose_name_image = self.post._meta.get_field('image').verbose_name
        self.assertEquals(verbose_name_text, 'Текст статьи',
                          'Неккорректный verbose_name у text модели Post')
        self.assertEquals(verbose_name_group, 'Группа',
                          'Неккорректный verbose_name у group модели Post')
        self.assertEquals(verbose_name_image, 'Изображение',
                          'Неккорректный verbose_name у image модели Post')

    def test_help_text(self):
        help_text_text = self.post._meta.get_field('text').help_text
        help_text_group = self.post._meta.get_field('group').help_text
        help_text_image = self.post._meta.get_field('image').help_text
        self.assertEquals(help_text_text, 'Добавьте текст статьи',
                          'Неккорректный help_text у text модели Post')
        self.assertEquals(help_text_group, 'Поле Группа не заполнено',
                          'Неккорректный help_text у group модели Post')
        self.assertEquals(help_text_image, 'Добавьте картинку',
                          'Неккорректный help_text у image модели Post')

    def test_str_method(self):
        self.assertEqual(str(self.post), self.post.text[:15],
                         'Функция __str__ работает некорректно в моделе Post')


class GroupModelTest(TestCase):

    def setUp(self):
        self.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug'
        )

    def test_verbose_name(self):
        verbose_name = self.group._meta.get_field('title').verbose_name
        self.assertEquals(verbose_name, 'Группа',
                          'Неккорректный verbose_name у text модели Group')

    def test_help_text(self):
        help_text = self.group._meta.get_field('title').help_text
        self.assertEquals(help_text, 'Поле Группа не заполнено',
                          'Неккорректный help_text у text модели Group')

    def test_str_method(self):
        self.assertEqual(str(self.group), self.group.title,
                         'Функция __str__ работает некорректно в моделе Group')
