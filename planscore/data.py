import json

UPLOAD_PREFIX = 'uploads/{id}/upload/'
UPLOAD_INDEX_KEY = 'uploads/{id}/index.json'

class Upload:

    def __init__(self, id, key, tiles=None):
        self.id = id
        self.key = key
        self.tiles = tiles
    
    def index_key(self):
        return UPLOAD_INDEX_KEY.format(id=self.id)
    
    def to_json(self):
        data = dict(
            id = self.id,
            key = self.key,
            tiles = self.tiles,
            )
    
        return json.dumps(data, sort_keys=True, indent=2)
    
    @staticmethod
    def from_json(body):
        data = json.loads(body)
    
        return Upload(
            id = data['id'], 
            key = data['key'],
            tiles = data.get('tiles'),
            )
