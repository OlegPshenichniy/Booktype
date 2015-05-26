import factory
from PIL import Image
import StringIO

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.files import uploadedfile
from django.db.models.signals import post_save

from booki.editor.models import Book, BookStatus, Language, BookVersion, BookiGroup
from booktype.apps.account.models import UserProfile


class FrontpageTest(TestCase):
    def setUp(self):
        self.dispatcher = reverse('portal:frontpage')
        self.user = UserFactory()

        # setup for groups
        bookiGroup = BookiGroupFactory(members=(0, 1))

        # setup for books
        book = BookFactory()

    def tearDown(self):
        self.user.delete()

    def test_frontpage(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['title'], 'Home')

    def test_books(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertNotContains(response, 'book title')

    def test_people(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)
        self.assertNotContains(response, 'user_')
        self.assertNotContains(response, 'description')

    def test_groups(self):
        response = self.client.get(self.dispatcher)
        self.assertEquals(response.status_code, 200)

        self.assertNotContains(response, 'group name')
        self.assertNotContains(response, 'url_group_name')
        self.assertNotContains(response, 'booki group description')
        self.assertNotContains(response, 'Members: 1')
        self.assertNotContains(response, 'Books: ')


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: "user_%d" % n)


class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile

    description = 'description'

    user = factory.SubFactory(UserFactory, profile=None)


class BookiGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BookiGroup

    name = 'group name'
    url_name = 'url_group_name'
    description = 'booki group description'
    owner = factory.SubFactory(UserFactory)

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for member in extracted:
                self.members.add(member)


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book

    owner = factory.SubFactory(UserFactory)
    url_title = factory.Sequence(lambda n: 'title_{}'.format(n))
    title = 'book title'
    status = BookStatus()
    language = Language(0, 'test language', 'tl')
    version = BookVersion(0, 0, 0, 0)
    group = factory.SubFactory(BookiGroupFactory)


class BookStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BookStatus

    book = factory.SubFactory(BookFactory)
    name = 'status name'
    weight = 0