from django.db import models


class CreatedModel(models.Model):
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата публикации',
    )

    class Meta:
        abstract = True
