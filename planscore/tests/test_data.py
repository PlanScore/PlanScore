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

        upload3 = data.Upload.from_json('{"id": "ID", "key": "KEY", "districts": ["yo"], "summary": ["oi"]}')
        self.assertEqual(upload3.id, 'ID')
        self.assertEqual(upload3.key, 'KEY')
        self.assertEqual(upload3.districts, ['yo'])
        self.assertEqual(upload3.summary, ['oi'])

    def test_upload_json(self):
        ''' data.Upload instances can be converted to and from JSON
        '''
        upload1 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json')
        upload2 = data.Upload.from_json(upload1.to_json())

        self.assertEqual(upload2.id, upload1.id)
        self.assertEqual(upload2.key, upload1.key)
        self.assertEqual(upload2.districts, upload1.districts)
        self.assertEqual(upload2.summary, upload1.summary)
    
        upload3 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json', districts=['yo', 'yo', 'yo'])
        upload4 = data.Upload.from_json(upload3.to_json())

        self.assertEqual(upload4.id, upload3.id)
        self.assertEqual(upload4.key, upload3.key)
        self.assertEqual(upload4.districts, upload3.districts)
        self.assertEqual(upload4.summary, upload3.summary)
    
        upload5 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            districts=['yo', 'yo', 'yo'], summary=['oi', 'oi', 'oi'])
        upload6 = data.Upload.from_json(upload5.to_json())

        self.assertEqual(upload6.id, upload5.id)
        self.assertEqual(upload6.key, upload5.key)
        self.assertEqual(upload6.districts, upload5.districts)
        self.assertEqual(upload6.summary, upload5.summary)

    def test_upload_index_key(self):
        ''' data.Upload.index_key() correctly munges Upload.key
        '''
        upload = data.Upload(id='ID', key='uploads/ID/upload/whatever.json')
        self.assertEqual(upload.index_key(), 'uploads/ID/index.json')
    
    def test_upload_clone(self):
        ''' data.Upload.clone() returns a copy with the right properties
        '''
        districts1, districts2 = unittest.mock.Mock(), unittest.mock.Mock()
        summary1, summary2 = unittest.mock.Mock(), unittest.mock.Mock()
        input = data.Upload(id='ID', key='whatever.json', districts=districts1, summary=summary1)
        self.assertIs(input.districts, districts1)
        self.assertIs(input.districts, districts1)

        output1 = input.clone(districts=districts2, summary=summary2)
        self.assertEqual(output1.id, input.id)
        self.assertEqual(output1.key, input.key)
        self.assertIs(output1.districts, districts2)
        self.assertIs(output1.summary, summary2)

        output2 = input.clone()
        self.assertEqual(output2.id, input.id)
        self.assertEqual(output2.key, input.key)
        self.assertIs(output2.districts, input.districts)
        self.assertIs(output2.summary, input.summary)

        output3 = input.clone(districts=None, summary=None)
        self.assertEqual(output3.id, input.id)
        self.assertEqual(output3.key, input.key)
        self.assertIs(output3.districts, input.districts)
        self.assertIs(output3.summary, input.summary)
