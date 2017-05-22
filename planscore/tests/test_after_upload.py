import unittest, unittest.mock, io, os, contextlib
from .. import after_upload, data

class TestAfterUpload (unittest.TestCase):
    
    @unittest.mock.patch('planscore.after_upload.get_uploaded_info')
    def test_lambda_handler(self, get_uploaded_info):
        query = {'id': 'id.k0_XwbOLGLUdv241zsPluNc3HYs', 'bucket': 'planscore',
            'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson'}

        os.environ.update(PLANSCORE_SECRET='fake-secret', WEBSITE_BASE='https://example.com/',
            AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')

        get_uploaded_info.return_value = 'get_uploaded_info.return_value'
        response = after_upload.lambda_handler({'queryStringParameters': query}, None)
        
        self.assertEqual(response['statusCode'], '302')
        self.assertIn(get_uploaded_info.return_value, response['body'])
        self.assertEqual(response['headers']['Location'], 'https://example.com/plan.html?id')
        
        self.assertEqual(get_uploaded_info.mock_calls[0][1][1:],
            (query['bucket'], query['key'], 'id'))
    
    @unittest.mock.patch('planscore.after_upload.get_uploaded_info')
    def test_lambda_handler_bad_id(self, get_uploaded_info):
        event = {
            'queryStringParameters': {'id': 'id.WRONG'}
            }

        os.environ.update(PLANSCORE_SECRET='fake-secret', AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')
        response = after_upload.lambda_handler(event, None)
        
        self.assertFalse(get_uploaded_info.mock_calls)
        self.assertEqual(response['statusCode'], '400')
        self.assertIn('Bad ID', response['body'])
    
    def test_put_upload_index(self):
        '''
        '''
        s3, bucket, upload = unittest.mock.Mock(), unittest.mock.Mock(), unittest.mock.Mock()
        after_upload.put_upload_index(s3, bucket, upload)
        s3.put_object.assert_called_once_with(Bucket=bucket,
            Key=upload.index_key.return_value,
            Body=upload.to_json.return_value.encode.return_value,
            ACL='public-read', ContentType='text/json')
    
    def test_put_geojson_file(self):
        ''' Geometry GeoJSON file is posted to S3
        '''
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        s3, bucket, upload = unittest.mock.Mock(), unittest.mock.Mock(), unittest.mock.Mock()
        after_upload.put_geojson_file(s3, bucket, upload, nullplan_path)
        s3.put_object.assert_called_once_with(Bucket=bucket,
            Key=upload.geometry_key.return_value,
            Body=b'{"type": "FeatureCollection", "features": [\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.000236, 0.0004533 ], [ -0.0006813, 0.0002468 ], [ -0.0006357, -0.0003487 ], [ -0.0000268, -0.0004694 ], [ -0.0000188, -0.0000215 ], [ -0.000236, 0.0004533 ] ] ] }},\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.0002259, 0.0004311 ], [ 0.000338, 0.0006759 ], [ 0.0004452, 0.0006142 ], [ 0.0005525, 0.000059 ], [ 0.0005257, -0.0005069 ], [ 0.0003862, -0.0005659 ], [ -0.0000939, -0.0004935 ], [ -0.0001016, -0.0004546 ], [ -0.0000268, -0.0004694 ], [ -0.0000188, -0.0000215 ], [ -0.0002259, 0.0004311 ] ] ] }}\n]}',
            ACL='public-read', ContentType='text/json')
    
    def test_get_redirect_url(self):
        '''
        '''
        redirect_url = after_upload.get_redirect_url('https://planscore.org/', 'ID')
        self.assertEqual(redirect_url, 'https://planscore.org/plan.html?ID')
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.after_upload.put_upload_index')
    @unittest.mock.patch('planscore.after_upload.put_geojson_file')
    @unittest.mock.patch('planscore.score.score_plan')
    def test_get_uploaded_info_good_file(self, score_plan, put_geojson_file, put_upload_index, temporary_buffer_file):
        ''' A valid district plan file is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.geojson'
        upload, output = data.Upload(id, upload_key), unittest.mock.Mock()
        score_plan.return_value = upload, output
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file

        s3, bucket = unittest.mock.Mock(), unittest.mock.Mock()
        s3.get_object.return_value = {'Body': None}

        info = after_upload.get_uploaded_info(s3, bucket, upload_key, id)

        self.assertEqual(len(score_plan.mock_calls), 1)
        self.assertEqual(score_plan.mock_calls[0][1][:2], (s3, bucket))
        self.assertEqual(score_plan.mock_calls[0][1][3:], (nullplan_path, 'data/XX'))

        temporary_buffer_file.assert_called_once_with('null-plan.geojson', None)
        self.assertIs(info, output)
    
        put_upload_index.assert_called_once_with(s3, bucket, upload)
        put_geojson_file.assert_called_once_with(s3, bucket, upload, nullplan_path)
    
    def test_get_uploaded_info_bad_file(self):
        '''
        '''
        s3, bucket = unittest.mock.Mock(), unittest.mock.Mock()
        s3.get_object.return_value = {'Body': io.BytesIO(b'Bad data')}

        with self.assertRaises(RuntimeError) as error:
            after_upload.get_uploaded_info(s3, bucket, 'uploads/id/null-plan.geojson', 'id')

        self.assertEqual(str(error.exception), 'Failed to read GeoJSON data')
