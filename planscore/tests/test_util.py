import unittest, unittest.mock, io, os
from .. import util

class TestUtil (unittest.TestCase):

    def test_temporary_buffer_file(self):
        buffer = io.BytesIO(b'Hello world')

        with util.temporary_buffer_file('hello.txt', buffer) as path:
            with open(path, 'rb') as file:
                data = file.read()

        self.assertEqual(data, buffer.getvalue())
        self.assertFalse(os.path.exists(path))

    def test_event_url(self):
        url1 = util.event_url({'headers': {'Host': 'example.org'}})
        self.assertEqual(url1, 'http://example.org/')

        url2 = util.event_url({'headers': {'Host': 'example.org', 'X-Forwarded-Proto': 'https'}})
        self.assertEqual(url2, 'https://example.org/')

        url3 = util.event_url({'headers': {'Host': 'example.org'}, 'path': '/hello'})
        self.assertEqual(url3, 'http://example.org/hello')

    def test_event_query_args(self):
        args1 = util.event_query_args({})
        self.assertEqual(args1, {})

        args2 = util.event_query_args({'queryStringParameters': None})
        self.assertEqual(args2, {})

        args3 = util.event_query_args({'queryStringParameters': {}})
        self.assertEqual(args3, {})

        args4 = util.event_query_args({'queryStringParameters': {'foo': 'bar'}})
        self.assertEqual(args4, {'foo': 'bar'})
