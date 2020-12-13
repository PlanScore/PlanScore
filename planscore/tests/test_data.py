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
    
    def test_Progress(self):
        ''' data.Progress works like a fraction
        '''
        p1 = data.Progress(1, 2)
        p2 = data.Progress(2, 2)
        p3 = data.Progress(3, 3)
        self.assertFalse(p1.is_complete())
        self.assertTrue(p2.is_complete())
        self.assertTrue(p3.is_complete())
        
        self.assertEqual(p1.to_list(), [1, 2])
        self.assertEqual(p1.to_percentage(), '50%')

        p4 = data.Progress(0, 0)
        self.assertEqual(p4.to_percentage(), '???%')
    
    def test_model(self):
        '''
        '''
        model1 = data.Model.from_json('{"state": "NC", "house": "ushouse", "seats": 13, "key_prefix": "data/NC/001"}')
        self.assertEqual(model1.state, data.State.NC)
        self.assertEqual(model1.house, data.House.ushouse)
        self.assertEqual(model1.seats, 13)
        self.assertEqual(model1.key_prefix, 'data/NC/001')
        self.assertEqual(model1.incumbency, False)
        
        with self.assertRaises(KeyError) as e:
            model2 = data.Model.from_json('{}')
        
        with self.assertRaises(KeyError) as e:
            model3 = data.Model.from_json('{"state": "-1", "house": "ushouse", "seats": 13, "key_prefix": "data/NC/001"}')

        model4 = data.Model.from_json('{"state": "NC", "house": "ushouse", "seats": 13, "key_prefix": "data/NC/001", "incumbency": true}')
        self.assertEqual(model4.state, data.State.NC)
        self.assertEqual(model4.house, data.House.ushouse)
        self.assertEqual(model4.seats, 13)
        self.assertEqual(model4.key_prefix, 'data/NC/001')
        self.assertEqual(model4.incumbency, True)
        self.assertEqual(model4.version, '2017')

        model5 = data.Model.from_json('{"state": "NC", "house": "ushouse", "seats": 13, "key_prefix": "data/NC/001", "version": "2020"}')
        self.assertEqual(model5.state, data.State.NC)
        self.assertEqual(model5.house, data.House.ushouse)
        self.assertEqual(model5.seats, 13)
        self.assertEqual(model5.key_prefix, 'data/NC/001')
        self.assertEqual(model5.version, '2020')

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

        upload4 = data.Upload.from_json('{"id": "ID", "key": "KEY", "progress": [1, 2]}')
        self.assertEqual(upload4.id, 'ID')
        self.assertEqual(upload4.key, 'KEY')
        self.assertEqual(upload4.progress, data.Progress(1, 2))

        upload5 = data.Upload.from_json('{"id": "ID", "key": "KEY", "start_time": 999}')
        self.assertEqual(upload5.id, 'ID')
        self.assertEqual(upload5.key, 'KEY')
        self.assertEqual(upload5.start_time, 999)

        upload6 = data.Upload.from_json('{"id": "ID", "key": "KEY", '
            '"model": {"state": "NC", "house": "ushouse", "seats": 13, "key_prefix": "data/NC/001"}}')
        self.assertEqual(upload6.id, 'ID')
        self.assertEqual(upload6.key, 'KEY')
        self.assertEqual(upload6.model.state, data.State.NC)
        self.assertEqual(upload6.model.seats, 13)

        upload7 = data.Upload.from_json('{"id": "ID", "key": "KEY", '
            '"description": "A fine new plan"}')
        self.assertEqual(upload7.id, 'ID')
        self.assertEqual(upload7.key, 'KEY')
        self.assertEqual(upload7.description, 'A fine new plan')

        upload8 = data.Upload.from_json('{"id": "ID", "key": "KEY", '
            '"description": "A fine new plan", "incumbents": ["D", "R"]}')
        self.assertEqual(upload8.id, 'ID')
        self.assertEqual(upload8.key, 'KEY')
        self.assertEqual(upload8.description, 'A fine new plan')
        self.assertEqual(upload8.incumbents, ['D', 'R'])
    
    def test_upload_overdue(self):
        ''' data.Upload self-reports correct overdue state
        '''
        upload1 = data.Upload('ID', 'Key', start_time=1000000000)
        upload2 = data.Upload('ID', 'Key', start_time=9000000000)
        
        self.assertTrue(upload1.is_overdue(), '15 year old Upload should be overdue')
        self.assertFalse(upload2.is_overdue(), 'Star Trek era Upload should not be overdue')

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
    
        upload7 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            progress=data.Progress(1, 2), start_time=999)
        upload8 = data.Upload.from_json(upload7.to_json())

        self.assertEqual(upload8.id, upload7.id)
        self.assertEqual(upload8.key, upload7.key)
        self.assertEqual(upload8.progress, upload7.progress)
        self.assertEqual(upload8.start_time, upload7.start_time)
    
        upload9 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            model=data.Model(data.State.NC, data.House.ushouse, 13, False, '2020', 'data/NC/001'))
        upload10 = data.Upload.from_json(upload9.to_json())

        self.assertEqual(upload10.id, upload9.id)
        self.assertEqual(upload10.key, upload9.key)
        self.assertEqual(upload10.model.state, upload9.model.state)
        self.assertEqual(upload10.model.house, upload9.model.house)
        self.assertEqual(upload10.model.seats, upload9.model.seats)
        self.assertEqual(upload10.model.key_prefix, upload9.model.key_prefix)
    
        upload11 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            message='I have uploaded the plan that was on your laptop')
        upload12 = data.Upload.from_json(upload11.to_json())

        self.assertEqual(upload12.id, upload11.id)
        self.assertEqual(upload12.key, upload11.key)
        self.assertEqual(upload12.message, upload11.message)
    
        upload13 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            description='I have uploaded the plan that was on your laptop')
        upload14 = data.Upload.from_json(upload13.to_json())

        self.assertEqual(upload14.id, upload13.id)
        self.assertEqual(upload14.key, upload13.key)
        self.assertEqual(upload14.description, upload13.description)
    
        upload15 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            incumbents=['O', 'D', 'R'])
        upload16 = data.Upload.from_json(upload15.to_json())

        self.assertEqual(upload16.id, upload15.id)
        self.assertEqual(upload16.key, upload15.key)
        self.assertEqual(upload16.incumbents, upload15.incumbents)
    
    def test_upload_plaintext(self):
        ''' data.Upload instances can be converted to plaintext
        '''
        upload1 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            districts=[
                { "totals": { "Democratic Votes": 100, "Population 2015": 200, "Republican Votes": 300 }, "compactness": { "Reock": .2 } },
                { "totals": { "Democratic Votes": 400, "Population 2015": 500, "Republican Votes": 600 }, "compactness": { "Reock": .3 } },
                { "totals": { "Democratic Votes": 700, "Population 2015": 800, "Republican Votes": 900 }, "compactness": { "Reock": .4 } }
              ])
        
        plaintext1 = upload1.to_plaintext()
        head, row1, row2, row3, tail = plaintext1.split('\r\n', 4)
        
        self.assertEqual(head, 'District\tDemocratic Votes\tRepublican Votes\tPopulation 2015\tReock')
        self.assertEqual(row1, '1\t100\t300\t200\t0.2')
        self.assertEqual(row2, '2\t400\t600\t500\t0.3')
        self.assertEqual(row3, '3\t700\t900\t800\t0.4')
        self.assertEqual(tail, '')

        upload2 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            districts=[ { "garbage": True } ])
        
        plaintext2 = upload2.to_plaintext()
        self.assertEqual(plaintext2, "Error: 'totals'\n")

        upload3 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            model=data.Model(data.State.XX, data.House.statehouse, 2, True, '2020', 'data/XX/000'),
            incumbents=['O', 'D', 'R'],
            districts=[
                { "totals": { "Democratic Votes": 100, "Population 2015": 200, "Republican Votes": 300 }, "compactness": { "Reock": .2 } },
                { "totals": { "Democratic Votes": 400, "Population 2015": 500, "Republican Votes": 600 }, "compactness": { "Reock": .3 } },
                { "totals": { "Democratic Votes": 700, "Population 2015": 800, "Republican Votes": 900 }, "compactness": { "Reock": .4 } }
              ])
        
        plaintext3 = upload3.to_plaintext()
        head, row1, row2, row3, tail = plaintext3.split('\r\n', 4)
        
        self.assertEqual(head, 'District\tCandidate Scenario\tDemocratic Votes\tRepublican Votes\tPopulation 2015\tReock')
        self.assertEqual(row1, '1\tO\t100\t300\t200\t0.2')
        self.assertEqual(row2, '2\tD\t400\t600\t500\t0.3')
        self.assertEqual(row3, '3\tR\t700\t900\t800\t0.4')
        self.assertEqual(tail, '')
    
    @unittest.mock.patch('time.time')
    def test_upload_to_logentry(self, time):
        ''' data.Upload instances can be converted to log entry
        '''
        time.return_value = -999
        
        upload1 = data.Upload(id='ID', message='Yo.', key='whatever')
        logentry1 = upload1.to_logentry()
        self.assertEqual(logentry1, 'ID\t-999\tYo.\t\t\t\r\n')

        upload2 = data.Upload(id='ID', message="Hell's Bells", key='whatever')
        logentry2 = upload2.to_logentry()
        self.assertEqual(logentry2, "ID\t-999\tHell's Bells\t\t\t\r\n")

        upload3 = data.Upload(id='ID', message="Oh, really?", key='whatever')
        logentry3 = upload3.to_logentry()
        self.assertEqual(logentry3, 'ID\t-999\tOh, really?\t\t\t\r\n')
        
        upload4 = data.Upload(
            id='ID', message='Yo.', key='whatever',
            model=data.Model.from_json('{"state": "NC", "house": "ushouse", "seats": 13, "key_prefix": "data/NC/001", "version": "2020"}')
        )
        logentry4 = upload4.to_logentry()
        self.assertEqual(logentry4, 'ID\t-999\tYo.\tNC\tushouse\t'
            '{"house":"ushouse","incumbency":false,"key_prefix":"data/NC/001","seats":13,"state":"NC","version":"2020"}\r\n')

    def test_upload_index_key(self):
        ''' data.Upload.index_key() correctly munges Upload.key
        '''
        upload = data.Upload(id='ID', key='uploads/ID/upload/whatever.json')
        self.assertEqual(upload.index_key(), 'uploads/ID/index.json')
    
    def test_upload_plaintext_key(self):
        ''' data.Upload.plaintext_key() correctly munges Upload.key
        '''
        upload = data.Upload(id='ID', key='uploads/ID/upload/whatever.json')
        self.assertEqual(upload.plaintext_key(), 'uploads/ID/index.txt')
    
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
    
    def test_upload_logentry_key(self):
        ''' data.Upload.logentry_key() correctly munges Upload.key
        '''
        upload = data.Upload(start_time=1607891802, id='ID', key='uploads/ID/upload/whatever.json')
        self.assertEqual(upload.logentry_key('uuid4'), 'logs/ds=2020-12-13/uuid4.txt')
    
    def test_upload_clone(self):
        ''' data.Upload.clone() returns a copy with the right properties
        '''
        model1, model2 = unittest.mock.Mock(), unittest.mock.Mock()
        districts1, districts2 = unittest.mock.Mock(), unittest.mock.Mock()
        incumbents1, incumbents2 = unittest.mock.Mock(), unittest.mock.Mock()
        summary1, summary2 = unittest.mock.Mock(), unittest.mock.Mock()
        progress1, progress2 = unittest.mock.Mock(), unittest.mock.Mock()
        start_time1, start_time2 = unittest.mock.Mock(), unittest.mock.Mock()
        input = data.Upload(id='ID', key='whatever.json', districts=districts1,
            model=model1, summary=summary1, progress=progress1, start_time=start_time1,
            incumbents=incumbents1)

        self.assertIs(input.districts, districts1)
        self.assertIs(input.incumbents, incumbents1)
        self.assertIs(input.summary, summary1)
        self.assertIs(input.progress, progress1)

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
        self.assertIs(output2.progress, input.progress)

        output3 = input.clone(districts=None, summary=None)
        self.assertEqual(output3.id, input.id)
        self.assertEqual(output3.key, input.key)
        self.assertIs(output3.districts, input.districts)
        self.assertIs(output3.summary, input.summary)
        self.assertIs(output3.progress, input.progress)

        output4 = input.clone(progress=progress2)
        self.assertEqual(output4.id, input.id)
        self.assertEqual(output4.key, input.key)
        self.assertIs(output4.progress, progress2)

        output5 = input.clone(start_time=start_time2)
        self.assertEqual(output5.id, input.id)
        self.assertEqual(output5.key, input.key)
        self.assertIs(output5.start_time, start_time2)

        output6 = input.clone(model=model2)
        self.assertEqual(output6.id, input.id)
        self.assertEqual(output6.key, input.key)
        self.assertIs(output6.model, model2)

        output7 = input.clone(message='Yo')
        self.assertEqual(output7.id, input.id)
        self.assertEqual(output7.key, input.key)
        self.assertIs(output7.message, 'Yo')

        output8 = input.clone(incumbents=incumbents2)
        self.assertEqual(output8.id, input.id)
        self.assertEqual(output8.key, input.key)
        self.assertIs(output8.incumbents, incumbents2)
