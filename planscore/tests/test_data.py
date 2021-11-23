import os, uuid, unittest, unittest.mock, json
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
        self.assertEqual(model4.versions, ['2017'])

        model5 = data.Model.from_json('{"state": "NC", "house": "ushouse", "seats": 13, "key_prefix": "data/NC/001", "version": "2020"}')
        self.assertEqual(model5.state, data.State.NC)
        self.assertEqual(model5.house, data.House.ushouse)
        self.assertEqual(model5.seats, 13)
        self.assertEqual(model5.key_prefix, 'data/NC/001')
        self.assertEqual(model5.versions, ['2020'])

        model6 = data.Model.from_json('{"state": "NC", "house": "localplan", "seats": null, "key_prefix": "data/NC/001", "version": "2020"}')
        self.assertEqual(model6.state, data.State.NC)
        self.assertEqual(model6.house, data.House.localplan)
        self.assertIsNone(model6.seats)
        self.assertEqual(model6.key_prefix, 'data/NC/001')
        self.assertEqual(model6.versions, ['2020'])

        model7 = data.Model.from_json('{"state": "NC", "house": "localplan", "seats": null, "key_prefix": "data/NC/001", "versions": ["2020"]}')
        self.assertEqual(model7.state, data.State.NC)
        self.assertEqual(model7.house, data.House.localplan)
        self.assertIsNone(model7.seats)
        self.assertEqual(model7.key_prefix, 'data/NC/001')
        self.assertEqual(model7.versions, ['2020'])

        model8 = data.Model.from_json('{"state": "NC", "house": "localplan", "seats": null, "key_prefix": "data/NC/001", "versions": ["2020", "2021"]}')
        self.assertEqual(model8.state, data.State.NC)
        self.assertEqual(model8.house, data.House.localplan)
        self.assertIsNone(model8.seats)
        self.assertEqual(model8.key_prefix, 'data/NC/001')
        self.assertEqual(model8.versions, ['2020', '2021'])

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

        upload9 = data.Upload.from_json('{"id": "ID", "key": "KEY", '
            '"geometry_key": "geometry.json", "incumbents": ["D", "R"]}')
        self.assertEqual(upload9.id, 'ID')
        self.assertEqual(upload9.key, 'KEY')
        self.assertEqual(upload9.geometry_key, 'geometry.json')
        self.assertEqual(upload9.incumbents, ['D', 'R'])

        upload10 = data.Upload.from_json('{"id": "ID", "key": "KEY", '
            '"status": true, "incumbents": ["D", "R"]}')
        self.assertEqual(upload10.id, 'ID')
        self.assertEqual(upload10.key, 'KEY')
        self.assertEqual(upload10.status, True)
        self.assertEqual(upload10.incumbents, ['D', 'R'])

        upload11 = data.Upload.from_json('{"id": "ID", "key": "KEY", '
            '"auth_token": "Heyo"}')
        self.assertEqual(upload11.id, 'ID')
        self.assertEqual(upload11.key, 'KEY')
        self.assertEqual(upload11.auth_token, 'Heyo')

        upload12 = data.Upload.from_json('{"id": "ID", "key": "KEY", '
            '"library_metadata": {"key": "value"}}')
        self.assertEqual(upload12.id, 'ID')
        self.assertEqual(upload12.key, 'KEY')
        self.assertEqual(upload12.library_metadata['key'], 'value')
    
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
        os.environ['GIT_COMMIT_SHA'] = str(uuid.uuid4())
        upload1 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json')

        self.assertEqual(upload1.commit_sha, os.environ['GIT_COMMIT_SHA'],
            'Upload.commit_sha should match latest GIT_COMMIT_SHA from env')

        os.environ['GIT_COMMIT_SHA'] = str(uuid.uuid4())
        upload2 = data.Upload.from_json(upload1.to_json())

        self.assertEqual(upload2.id, upload1.id)
        self.assertEqual(upload2.key, upload1.key)
        self.assertEqual(upload2.districts, upload1.districts)
        self.assertEqual(upload2.summary, upload1.summary)
        self.assertEqual(upload2.commit_sha, os.environ['GIT_COMMIT_SHA'],
            'Upload.commit_sha should match latest GIT_COMMIT_SHA from env')
    
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
            model=data.Model(data.State.NC, data.House.ushouse, 13, False, ['2020'], 'data/NC/001'))
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
    
        upload17 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            geometry_key='geometry.json')
        upload18 = data.Upload.from_json(upload17.to_json())

        self.assertEqual(upload18.id, upload17.id)
        self.assertEqual(upload18.key, upload17.key)
        self.assertEqual(upload18.geometry_key, upload17.geometry_key)
    
        upload19 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            status=False)
        upload20 = data.Upload.from_json(upload19.to_json())

        self.assertEqual(upload20.id, upload19.id)
        self.assertEqual(upload20.key, upload19.key)
        self.assertIs(upload20.status, upload19.status)
    
        upload21 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            auth_token='Heyo')

        self.assertIsNone(json.loads(upload21.to_json()).get('auth_token'))
    
        upload22 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            library_metadata={'key': 'value'})
        upload23 = data.Upload.from_json(upload22.to_json())

        self.assertEqual(upload23.id, upload22.id)
        self.assertEqual(upload23.key, upload22.key)
        self.assertEqual(upload23.library_metadata, upload22.library_metadata)
    
        upload24 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            model_version='1999')
        upload25 = data.Upload.from_json(upload24.to_json())

        self.assertEqual(upload25.id, upload24.id)
        self.assertEqual(upload25.key, upload24.key)
        self.assertEqual(upload25.model_version, upload24.model_version)
    
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
            model=data.Model(data.State.XX, data.House.statehouse, 2, True, ['2020'], 'data/XX/000'),
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

        upload4 = data.Upload(id='ID', key='uploads/ID/upload/whatever.json',
            model=data.Model(data.State.XX, data.House.statehouse, 2, True, ['2020'], 'data/XX/000'),
            incumbents=['O', 'D', 'R'],
            districts=[
                { "number": 1, "totals": { "Democratic Votes": 100, "Population 2015": 200, "Republican Votes": 300 }, "compactness": { "Reock": .2 } },
                { "number": None, "totals": { "Democratic Votes": 400, "Population 2015": 500, "Republican Votes": 600 }, "compactness": { "Reock": .3 } },
                { "number": 2, "totals": { "Democratic Votes": 700, "Population 2015": 800, "Republican Votes": 900 }, "compactness": { "Reock": .4 } }
              ])
        
        plaintext4 = upload4.to_plaintext()
        head, row1, row2, row3, tail = plaintext4.split('\r\n', 4)
        
        self.assertEqual(head, 'District\tCandidate Scenario\tDemocratic Votes\tRepublican Votes\tPopulation 2015\tReock')
        self.assertEqual(row1, '1\tO\t100\t300\t200\t0.2')
        self.assertEqual(row2, '\tD\t400\t600\t500\t0.3')
        self.assertEqual(row3, '2\tR\t700\t900\t800\t0.4')
        self.assertEqual(tail, '')
    
    @unittest.mock.patch('time.time')
    def test_upload_to_logentry(self, time):
        ''' data.Upload instances can be converted to log entry
        '''
        time.return_value = -999
        
        upload1 = data.Upload(id='ID', message='Yo.', key='whatever')
        logentry1 = upload1.to_logentry()
        self.assertEqual(logentry1, 'ID\t-999\t0\tYo.\t\t\t\twhatever\t\t\r\n')

        upload2 = data.Upload(id='ID', message="Hell's Bells", key='whatever', status=True)
        logentry2 = upload2.to_logentry()
        self.assertEqual(logentry2, "ID\t-999\t0\tHell's Bells\t\t\t\twhatever\tt\t\r\n")

        upload3 = data.Upload(id='ID', message="Oh, really?", key='whatever', status=False)
        logentry3 = upload3.to_logentry()
        self.assertEqual(logentry3, 'ID\t-999\t0\tOh, really?\t\t\t\twhatever\tf\t\r\n')
        
        upload4 = data.Upload(
            id='ID', message='Yo.', key='whatever',
            model=data.Model.from_json('{"state": "NC", "house": "ushouse", "seats": 13, "key_prefix": "data/NC/001", "version": "2020"}')
        )
        logentry4 = upload4.to_logentry()
        self.assertEqual(logentry4, 'ID\t-999\t0\tYo.\tNC\tushouse\t'
            '{"house":"ushouse","incumbency":false,"key_prefix":"data/NC/001","seats":13,"state":"NC","versions":["2020"]}'
            '\twhatever\t\t\r\n')

        upload5 = data.Upload(id='ID', message="Hell's Bells", key='whatever', auth_token='Heyo')
        logentry5 = upload5.to_logentry()
        self.assertEqual(logentry5, "ID\t-999\t0\tHell's Bells\t\t\t\twhatever\t\tHe********\r\n")

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
    
    def test_upload_district_key(self):
        ''' data.Upload.district_key() correctly munges Upload.key
        '''
        upload = data.Upload(id='ID', key='uploads/ID/upload/whatever.json')
        self.assertEqual(upload.district_key(999), 'uploads/ID/districts/999.json')
    
    def test_upload_logentry_key(self):
        ''' data.Upload.logentry_key() correctly munges Upload.key
        '''
        upload = data.Upload(start_time=1607891802, id='ID', key='uploads/ID/upload/whatever.json')
        self.assertEqual(upload.logentry_key('uuid4'), 'logs/scoring/ds=2020-12-13/uuid4.txt')
    
    def test_upload_clone(self):
        ''' data.Upload.clone() returns a copy with the right properties
        '''
        os.environ['GIT_COMMIT_SHA'] = str(uuid.uuid4())

        model1, model2 = unittest.mock.Mock(), unittest.mock.Mock()
        districts1, districts2 = unittest.mock.Mock(), unittest.mock.Mock()
        incumbents1, incumbents2 = unittest.mock.Mock(), unittest.mock.Mock()
        summary1, summary2 = unittest.mock.Mock(), unittest.mock.Mock()
        progress1, progress2 = unittest.mock.Mock(), unittest.mock.Mock()
        start_time1, start_time2 = unittest.mock.Mock(), unittest.mock.Mock()
        geometry1, geometry2 = unittest.mock.Mock(), unittest.mock.Mock()
        input = data.Upload(id='ID', key='whatever.json', districts=districts1,
            model=model1, summary=summary1, progress=progress1, start_time=start_time1,
            incumbents=incumbents1, geometry_key=geometry1, auth_token='fake')

        self.assertIs(input.districts, districts1)
        self.assertIs(input.incumbents, incumbents1)
        self.assertIs(input.summary, summary1)
        self.assertIs(input.progress, progress1)
        self.assertEqual(input.commit_sha, os.environ['GIT_COMMIT_SHA'],
            'Upload.commit_sha should match latest GIT_COMMIT_SHA from env')

        os.environ['GIT_COMMIT_SHA'] = str(uuid.uuid4())

        output1 = input.clone(districts=districts2, summary=summary2)
        self.assertEqual(output1.id, input.id)
        self.assertEqual(output1.key, input.key)
        self.assertIs(output1.districts, districts2)
        self.assertIs(output1.summary, summary2)
        self.assertEqual(output1.commit_sha, os.environ['GIT_COMMIT_SHA'],
            'Upload.commit_sha should match latest GIT_COMMIT_SHA from env')

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

        output9 = input.clone(incumbents=geometry2)
        self.assertEqual(output9.id, input.id)
        self.assertEqual(output9.key, input.key)
        self.assertIs(output9.incumbents, geometry2)

        output10 = input.clone()
        self.assertEqual(output10.id, input.id)
        self.assertEqual(output10.key, input.key)
        self.assertIsNone(output10.auth_token)

        output11 = input.clone(auth_token='Heyo')
        self.assertEqual(output11.id, input.id)
        self.assertEqual(output11.key, input.key)
        self.assertEqual(output11.auth_token, 'Heyo')

        output12 = input.clone(library_metadata={'key': 'value'})
        self.assertEqual(output12.id, input.id)
        self.assertEqual(output12.key, input.key)
        self.assertEqual(output12.library_metadata['key'], 'value')
