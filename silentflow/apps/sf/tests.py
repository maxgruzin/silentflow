from django.test import TestCase


class TestTests(TestCase):

    def test_test(self):
        self.assertEqual('foo', 'foo')

    def test_test2(self):
        self.assertAlmostEqual('foo', 'foo')
