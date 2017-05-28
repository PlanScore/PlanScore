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
