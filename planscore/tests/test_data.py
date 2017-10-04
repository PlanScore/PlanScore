import unittest, unittest.mock
from .. import data

class TestData (unittest.TestCase):

    def test_Storage(self):
        ''' Storage.from_event() creates the right properties.
        '''
        s3 = unittest.mock.Mock()
        storage = data.Storage.from_event(dict(bucket='bucket', prefix='XX'), s3)
        self.assertEqual(storage.s3, s3)
        self.assertEqual(storage.bucket, 'bucket')
        self.assertEqual(storage.prefix, 'XX')

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
    
    def test_upload_geometry_key(self):
        ''' data.Upload.geometry_key() correctly munges Upload.key
        '''
        upload = data.Upload(id='ID', key='uploads/ID/upload/whatever.json')
        self.assertEqual(upload.geometry_key(), 'uploads/ID/geometry.json')
    
    def test_upload_district_key(self):
        ''' data.Upload.district_key() correctly munges Upload.key
        '''
        upload = data.Upload(id='ID', key='uploads/ID/upload/whatever.json')
        self.assertEqual(upload.district_key(999), 'uploads/ID/districts/999.json')
    
    def test_upload_clone(self):
        ''' data.Upload.clone() returns a copy with the right properties
        '''
        districts1, districts2 = [1, 2, 3], [4, 5, 6]
        summary1, summary2 = dict(a=1, b=2), dict(c=3, d=4)
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
        self.assertIsNot(output2.districts, input.districts)
        self.assertIsNot(output2.summary, input.summary)
        self.assertEqual(output2.districts, input.districts)
        self.assertEqual(output2.summary, input.summary)

        output3 = input.clone(districts=None, summary=None)
        self.assertEqual(output3.id, input.id)
        self.assertEqual(output3.key, input.key)
        self.assertIsNot(output3.districts, input.districts)
        self.assertIsNot(output3.summary, input.summary)
        self.assertEqual(output3.districts, input.districts)
        self.assertEqual(output3.summary, input.summary)
    
    def test_upload_swing(self):
        ''' data.Upload.swing() adjusts votes in the right direction.
        '''
        districts = [
            dict(totals={'Voters': 10, 'Red Votes': 2, 'Blue Votes': 6}, tile=None),
            dict(totals={'Voters': 10, 'US Senate Rep Votes': 3, 'US Senate Dem Votes': 5}, tile=None),
            dict(totals={'Voters': 10, 'US House Rep Votes': 5, 'US House Dem Votes': 3}, tile=None),
            dict(totals={'Voters': 10, 'SLDU Rep Votes': 6, 'SLDU Dem Votes': 2}, tile=None),
            dict(totals={'Voters': 10, 'SLDL Rep Votes': 2, 'SLDL Dem Votes': 6}, tile=None),
            ]

        upload = data.Upload(id=None, key=None, districts=districts)
        bluer = upload.swing(.1)
        redder = upload.swing(-.1)
        
        self.assertEqual(bluer.districts[0]['totals']['Red Votes'], 1.2, 'Should now have 1.2 red votes')
        self.assertEqual(bluer.districts[0]['totals']['Blue Votes'], 6.8, 'Should now have 6.8 blue votes')
        self.assertEqual(bluer.districts[1]['totals']['US Senate Rep Votes'], 2.2, 'Should now have 2.2 red votes')
        self.assertEqual(bluer.districts[1]['totals']['US Senate Dem Votes'], 5.8, 'Should now have 5.8 blue votes')
        self.assertEqual(bluer.districts[2]['totals']['US House Rep Votes'], 4.2, 'Should now have 4.2 red votes')
        self.assertEqual(bluer.districts[2]['totals']['US House Dem Votes'], 3.8, 'Should now have 3.8 blue votes')
        self.assertEqual(bluer.districts[3]['totals']['SLDU Rep Votes'], 5.2, 'Should now have 5.2 red votes')
        self.assertEqual(bluer.districts[3]['totals']['SLDU Dem Votes'], 2.8, 'Should now have 2.8 blue votes')
        self.assertEqual(bluer.districts[4]['totals']['SLDL Rep Votes'], 1.2, 'Should now have 1.2 red votes')
        self.assertEqual(bluer.districts[4]['totals']['SLDL Dem Votes'], 6.8, 'Should now have 6.8 blue votes')
        
        self.assertEqual(redder.districts[0]['totals']['Red Votes'], 2.8, 'Should now have 2.8 red votes')
        self.assertEqual(redder.districts[0]['totals']['Blue Votes'], 5.2, 'Should now have 5.2 blue votes')
        self.assertEqual(redder.districts[1]['totals']['US Senate Rep Votes'], 3.8, 'Should now have 3.8 red votes')
        self.assertEqual(redder.districts[1]['totals']['US Senate Dem Votes'], 4.2, 'Should now have 4.2 blue votes')
        self.assertEqual(redder.districts[2]['totals']['US House Rep Votes'], 5.8, 'Should now have 5.8 red votes')
        self.assertEqual(redder.districts[2]['totals']['US House Dem Votes'], 2.2, 'Should now have 2.2 blue votes')
        self.assertEqual(redder.districts[3]['totals']['SLDU Rep Votes'], 6.8, 'Should now have 6.8 red votes')
        self.assertEqual(redder.districts[3]['totals']['SLDU Dem Votes'], 1.2, 'Should now have 1.2 blue votes')
        self.assertEqual(redder.districts[4]['totals']['SLDL Rep Votes'], 2.8, 'Should now have 2.8 red votes')
        self.assertEqual(redder.districts[4]['totals']['SLDL Dem Votes'], 5.2, 'Should now have 5.2 blue votes')
