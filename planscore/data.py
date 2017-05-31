import json

UPLOAD_PREFIX = 'uploads/{id}/upload/'
UPLOAD_INDEX_KEY = 'uploads/{id}/index.json'
UPLOAD_GEOMETRY_KEY = 'uploads/{id}/geometry.json'
UPLOAD_DISTRICTS_KEY = 'uploads/{id}/districts/{index}.json'

class Storage:
    ''' Wrapper for S3-related details.
    '''
    def __init__(self, s3, bucket, prefix):
        self.s3 = s3
        self.bucket = bucket
        self.prefix = prefix
    
    def to_event(self):
        return dict(bucket=self.bucket, prefix=self.prefix)
    
    @staticmethod
    def from_event(event, s3):
        bucket = event['bucket']
        prefix = event.get('prefix')
        return Storage(s3, bucket, prefix)

class Upload:

    def __init__(self, id, key, districts=None, summary=None, **kwargs):
        self.id = id
        self.key = key
        self.districts = districts or []
        self.summary = summary or {}
    
    def index_key(self):
        return UPLOAD_INDEX_KEY.format(id=self.id)
    
    def geometry_key(self):
        return UPLOAD_GEOMETRY_KEY.format(id=self.id)
    
    def district_key(self, index):
        return UPLOAD_DISTRICTS_KEY.format(id=self.id, index=index)
    
    def to_dict(self):
        return dict(
            id = self.id,
            key = self.key,
            districts = self.districts,
            summary = self.summary,
            )
    
    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)
    
    def clone(self, districts=None, summary=None):
        return Upload(self.id, self.key,
            districts = districts or self.districts,
            summary = summary or self.summary)
    
    @staticmethod
    def from_dict(data):
        return Upload(
            id = data['id'], 
            key = data['key'],
            districts = data.get('districts'),
            summary = data.get('summary'),
            )
    
    @staticmethod
    def from_json(body):
        return Upload.from_dict(json.loads(body))
