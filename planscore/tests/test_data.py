import unittest, unittest.mock
from .. import data

class TestData (unittest.TestCase):

    def test_upload_storage(self):
        ''' Past and future data.Upload instances are readable
        '''
        upload1 = data.Upload.from_json('{"id": "ID", "key": "KEY"}')
        self.assertEqual(upload1.id, 'ID')
        self.assertEqual(upload1.key, 'KEY')
        self.assertEqual(upload1.districts, [])

        upload2 = data.Upload.from_json('{"id": "ID", "key": "KEY", "districts": ["yo"]}')
        self.assertEqual(upload2.id, 'ID')
        self.assertEqual(upload2.key, 'KEY')
        self.assertEqual(upload2.districts, ['yo'])

    def test_upload_json(self):
        ''' data.Upload instances can be converted to and from JSON
        '''
        upload1 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json')
        upload2 = data.Upload.from_json(upload1.to_json())

        self.assertEqual(upload2.id, upload1.id)
        self.assertEqual(upload2.key, upload1.key)
        self.assertEqual(upload2.districts, upload1.districts)
    
        upload3 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json', districts=['yo', 'yo', 'yo'])
        upload4 = data.Upload.from_json(upload3.to_json())

        self.assertEqual(upload4.id, upload3.id)
        self.assertEqual(upload4.key, upload3.key)
        self.assertEqual(upload4.districts, upload3.districts)

    def test_upload_index_key(self):
        ''' data.Upload.index_key() correctly munges Upload.key
        '''
        upload = data.Upload(id='ID', key='uploads/ID/upload/whatever.json')
        self.assertEqual(upload.index_key(), 'uploads/ID/index.json')
    
    def test_upload_clone(self):
        ''' data.Upload.clone() returns a copy with the right properties
        '''
        districts1, districts2 = unittest.mock.Mock(), unittest.mock.Mock()
        input = data.Upload(id='ID', key='whatever.json', districts=districts1)
        self.assertIs(input.districts, districts1)

        output1 = input.clone(districts=districts2)
        self.assertEqual(output1.id, input.id)
        self.assertEqual(output1.key, input.key)
        self.assertIs(output1.districts, districts2)

        output2 = input.clone()
        self.assertEqual(output2.id, input.id)
        self.assertEqual(output2.key, input.key)
        self.assertIs(output2.districts, input.districts)

        output3 = input.clone(districts=None)
        self.assertEqual(output3.id, input.id)
        self.assertEqual(output3.key, input.key)
        self.assertIs(output3.districts, input.districts)
