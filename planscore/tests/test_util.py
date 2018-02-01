import unittest, unittest.mock, io, os, logging
from .. import util, constants

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
    
    def test_sqs_log_handler(self):
        ''' Log events sent to SQS arrive as intended
        '''
        client = unittest.mock.Mock()
        handler = util.SQSLoggingHandler(client, 'http://example.com/queue')
        
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.info('{"hello": "world"}')
        logger.debug('{"too much": "information"}')
        logger.removeHandler(handler)
        
        client.send_message.assert_called_once_with(MessageBody='{"hello": "world"}',
            QueueUrl='http://example.com/queue')
    
    @unittest.mock.patch('logging.getLogger')
    @unittest.mock.patch('planscore.util.SQSLoggingHandler')
    @unittest.mock.patch('boto3.client')
    def test_add_sqs_logging_handler(self, boto3_client, SQSLoggingHandler, getLogger):
        '''
        '''
        logger = getLogger.return_value
        util.add_sqs_logging_handler('yo')
        
        SQSLoggingHandler.assert_called_once_with(boto3_client.return_value, constants.SQS_QUEUEURL)
        logger.addHandler.assert_called_once_with(SQSLoggingHandler.return_value)
        logger.setLevel.assert_called_once_with(logging.INFO)
        getLogger.assert_called_once_with('yo')
