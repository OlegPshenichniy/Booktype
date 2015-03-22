from django.db import models
from django.contrib.auth.models import User

from booki.editor.models import Book


class VideoSettings(models.Model):
    """
    Contain video configuration for user per book.
    """
    user = models.ForeignKey(User)
    book = models.ForeignKey(Book)
    enabled = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Video settings"
        unique_together = ('user', 'book')

    def __unicode__(self):
        return '{0} - "{1}". Video {2}'.format(self.user,
                                               self.book,
                                               'enabled' if self.enabled else 'disabled')