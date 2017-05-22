import json

UPLOAD_PREFIX = 'uploads/{id}/upload/'
UPLOAD_INDEX_KEY = 'uploads/{id}/index.json'
UPLOAD_GEOMETRY_KEY = 'uploads/{id}/geometry.json'

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
    
    def to_json(self):
        data = dict(
            id = self.id,
            key = self.key,
            districts = self.districts,
            summary = self.summary,
            )
    
        return json.dumps(data, sort_keys=True, indent=2)
    
    def clone(self, districts=None, summary=None):
        return Upload(self.id, self.key,
            districts = districts or self.districts,
            summary = summary or self.summary)
    
    @staticmethod
    def from_json(body):
        data = json.loads(body)
    
        return Upload(
            id = data['id'], 
            key = data['key'],
            districts = data.get('districts'),
            summary = data.get('summary'),
            )
