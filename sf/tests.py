from django.test import TestCase, Client
from django.urls import reverse
from .models import Tag, Artist, Release, ReleaseTags, ReleaseArtists, Track

# c = Client()
# response = c.post('/login/', {'username': 'john', 'password': 'smith'})
# response.status_code
# response = c.get('/customer/details/')
# response.content


# class TagModelTests(TestCase):
#     def setUp(self):
#         Tag.objects.create(name="testtag")
#
#     def test_tag_creation(self):
#         test_tag = Tag.objects.get(name="testtag")
#         self.assertTrue(isinstance(test_tag, Tag))
#         self.assertEqual(test_tag.__unicode__(), test_tag.title)


class IndexViewTests(TestCase):

    def test_index_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertGreaterEqual(len(response.context['releases']), 2)
        self.assertEqual(response.context['releases'], 2)
        self.assertEqual(response.context['releases'][0], None)
        self.assertEqual(response.context['headline'], 2)
        self.assertEqual(response.context['headline'][0], None)
        # self.assertGreater
