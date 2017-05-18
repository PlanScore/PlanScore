import unittest
from .. import data

class TestData (unittest.TestCase):

    def test_upload_storage(self):
        ''' Verify that past and future Upload objects are readable.
        '''
        upload1 = data.Upload.from_json('{"id": "ID", "key": "KEY"}')
        self.assertEqual(upload1.id, 'ID')
        self.assertEqual(upload1.key, 'KEY')
        self.assertIsNone(upload1.tiles)

        upload2 = data.Upload.from_json('{"id": "ID", "key": "KEY", "tiles": [["yo"]]}')
        self.assertEqual(upload2.id, 'ID')
        self.assertEqual(upload2.key, 'KEY')
        self.assertEqual(upload2.tiles, [['yo']])

    def test_upload_json(self):
    
        upload1 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json')
        upload2 = data.Upload.from_json(upload1.to_json())

        self.assertEqual(upload2.id, upload1.id)
        self.assertEqual(upload2.key, upload1.key)
        self.assertEqual(upload2.tiles, upload1.tiles)
    
        upload3 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json', tiles=['yo', 'yo', 'yo'])
        upload4 = data.Upload.from_json(upload3.to_json())

        self.assertEqual(upload4.id, upload3.id)
        self.assertEqual(upload4.key, upload3.key)
        self.assertEqual(upload4.tiles, upload3.tiles)

    def test_upload_index_key(self):
    
        upload = data.Upload(id='ID', key='uploads/ID/upload/whatever.json')
        self.assertEqual(upload.index_key(), 'uploads/ID/index.json')
