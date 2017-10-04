import json, copy

UPLOAD_PREFIX = 'uploads/{id}/upload/'
UPLOAD_INDEX_KEY = 'uploads/{id}/index.json'
UPLOAD_GEOMETRY_KEY = 'uploads/{id}/geometry.json'
UPLOAD_DISTRICTS_KEY = 'uploads/{id}/districts/{index}.json'

FIELD_NAMES = (
    # Toy fields
    'Voters', 'Blue Votes', 'Red Votes',

    # Real fields
    'Population', 'Voting-Age Population', 'Black Voting-Age Population',
    'US Senate Rep Votes', 'US Senate Dem Votes', 'US House Rep Votes', 'US House Dem Votes',
    'SLDU Rep Votes', 'SLDU Dem Votes', 'SLDL Rep Votes', 'SLDL Dem Votes',
    )

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
    
    def swing(self, amount):
        ''' Return a clone with the vote swung by a given amount (positive = Democratic).
        '''
        swung = self.clone()
        
        for district in swung.districts:
            totals = district['totals']
            
            if 'Blue Votes' in totals and 'Red Votes' in totals:
                blue_key, red_key = 'Blue Votes', 'Red Votes'
            elif 'US Senate Dem Votes' in totals and 'US Senate Rep Votes' in totals:
                blue_key, red_key = 'US Senate Dem Votes', 'US Senate Rep Votes'
            elif 'US House Dem Votes' in totals and 'US House Rep Votes' in totals:
                blue_key, red_key = 'US House Dem Votes', 'US House Rep Votes'
            elif 'SLDU Dem Votes' in totals and 'SLDU Rep Votes' in totals:
                blue_key, red_key = 'SLDU Dem Votes', 'SLDU Rep Votes'
            elif 'SLDL Dem Votes' in totals and 'SLDL Rep Votes' in totals:
                blue_key, red_key = 'SLDL Dem Votes', 'SLDL Rep Votes'
            else:
                raise KeyError('Missing expected party votes')
            
            vote_count = totals[blue_key] + totals[red_key]
            
            if vote_count > 0:
                new_blue_votes = (totals[blue_key]/vote_count + amount) * vote_count
                new_red_votes = (totals[red_key]/vote_count - amount) * vote_count
                totals[blue_key], totals[red_key] = new_blue_votes, new_red_votes
        
        return swung
    
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
            districts = districts or copy.deepcopy(self.districts),
            summary = summary or copy.deepcopy(self.summary))
    
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
