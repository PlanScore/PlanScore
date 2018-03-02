import unittest, unittest.mock
from .. import observe

class TestObserveTiles (unittest.TestCase):

    def test_put_upload_index(self):
        ''' Upload index file is posted to S3
        '''
        storage, upload = unittest.mock.Mock(), unittest.mock.Mock()
        upload.id = 'ID'
        observe.put_upload_index(storage, upload)
        
        (put_call1, ) = storage.s3.put_object.mock_calls
        
        self.assertEqual(put_call1[2], dict(Bucket=storage.bucket,
            Key='uploads/ID/index-tiles.json',
            Body=upload.to_json.return_value.encode.return_value,
            ACL='public-read', ContentType='text/json'))
        
        return
        
        self.assertEqual(put_call2[2], dict(Bucket=storage.bucket,
            Key=upload.plaintext_key.return_value,
            Body=upload.to_plaintext.return_value.encode.return_value,
            ACL='public-read', ContentType='text/plain'))

    def test_expected_tile(self):
        ''' Expected tile is returned for an enqueued one.
        '''
        upload = unittest.mock.Mock()
        upload.model.key_prefix = 'data/XX'
        upload.id = 'ID'
        
        enqueued_key = 'data/XX/12/656/1582.geojson'
        expected_key = 'uploads/ID/tiles/12/656/1582.json'
        
        self.assertEqual(observe.get_expected_tile(enqueued_key, upload), expected_key)
