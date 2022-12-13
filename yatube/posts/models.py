from core.models import CreatedModel
from django.contrib.auth import get_user_model
from django.db import models
User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='название группы',
        help_text='введите название группы',
    )
    slug = models.SlugField(unique=True)
    description = models.TextField(
        verbose_name='описание группы',
        help_text='введите описание группы',
    )

    class Meta:
        verbose_name = 'группа'
        verbose_name_plural = 'группы'

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='текст поста',
        help_text='введите тескт поста',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='автор',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='группа',
        help_text='группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        'картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self):
        return self.text[:15]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='пост',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='автор',
    )
    text = models.TextField(
        verbose_name='коментарий',
        help_text='оставте комментарий к посту',
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Коментарий'
        verbose_name_plural = 'Коментарии'

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='автор',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'],
                name='unique following'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='cant subscribe to yourself',
            ),
        ]
