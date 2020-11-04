import json, csv, io, time, enum
from . import constants

UPLOAD_PREFIX = 'uploads/{id}/upload/'
UPLOAD_INDEX_KEY = 'uploads/{id}/index.json'
UPLOAD_PLAINTEXT_KEY = 'uploads/{id}/index.txt'
UPLOAD_GEOMETRY_KEY = 'uploads/{id}/geometry.json'
UPLOAD_DISTRICTS_KEY = 'uploads/{id}/districts/{index}.json'
UPLOAD_GEOMETRIES_KEY = 'uploads/{id}/geometries/{index}.wkt'
UPLOAD_TILE_INDEX_KEY = 'uploads/{id}/tiles.json'
UPLOAD_TILES_KEY = 'uploads/{id}/tiles/{zxy}.json'

class State (enum.Enum):
    XX = 'XX'
    MD = 'MD'; NC = 'NC'; PA = 'PA'; VA = 'VA'; WI = 'WI'

class House (enum.Enum):
    ushouse = 'ushouse'; statesenate = 'statesenate'; statehouse = 'statehouse'

class Incumbency (enum.Enum):
    Open = 'O'
    Democrat = 'D'
    Republican = 'R'

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

class Progress:
    ''' Fraction-like value representing number of completed districts.
    
        Not using fractions.Fraction because it reduces to lowest terms.
    '''
    def __init__(self, completed, expected):
        self.completed = completed
        self.expected = expected
    
    def to_list(self):
        return [self.completed, self.expected]
    
    def to_percentage(self):
        try:
            return '{:.0f}%'.format(100 * self.completed / self.expected)
        except ZeroDivisionError:
            return '???%'
    
    def is_complete(self):
        return bool(self.completed >= self.expected)
    
    def __eq__(self, other):
        return (self.completed / self.expected) == (other.completed / other.expected)

class Model:

    def __init__(self, state:State, house:House, seats:int, incumbency:bool, version:str, key_prefix:str):
        self.state = state
        self.house = house
        self.seats = seats
        self.key_prefix = key_prefix
        self.incumbency = incumbency
        self.version = version
    
    def to_dict(self):
        return dict(
            state = self.state.value,
            house = self.house.value,
            seats = self.seats,
            key_prefix = self.key_prefix,
            incumbency = self.incumbency,
            version = self.version,
            )
    
    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)
    
    @staticmethod
    def from_dict(data):
        return Model(
            state = State[data['state']],
            house = House[data['house']],
            seats = int(data['seats']),
            key_prefix = str(data['key_prefix']),
            incumbency = bool(data.get('incumbency')),
            version = str(data.get('version', '2017')),
            )
    
    @staticmethod
    def from_json(body):
        return Model.from_dict(json.loads(body))

class Upload:

    def __init__(self, id, key, model:Model=None, districts=None, incumbents=None, summary=None,
            progress=None, start_time=None, message=None, description=None, **ignored):
        self.id = id
        self.key = key
        self.model = model
        self.districts = districts or []
        self.incumbents = incumbents or []
        self.summary = summary or {}
        self.progress = progress
        self.start_time = start_time or time.time()
        self.message = message
        self.description = description
        
        if not incumbents:
            self.incumbents = [Incumbency.Open.value for i in range(len(self.districts))]
    
    def is_overdue(self):
        return bool(time.time() > (self.start_time + constants.UPLOAD_TIME_LIMIT))
    
    def index_key(self):
        return UPLOAD_INDEX_KEY.format(id=self.id)
    
    def plaintext_key(self):
        return UPLOAD_PLAINTEXT_KEY.format(id=self.id)
    
    def geometry_key(self):
        return UPLOAD_GEOMETRY_KEY.format(id=self.id)
    
    def district_key(self, index):
        return UPLOAD_DISTRICTS_KEY.format(id=self.id, index=index)
    
    def to_plaintext(self):
        ''' Export district totals to a tab-delimited plaintext file
        '''
        sorting_hints = dict({k: i for (i, k) in enumerate((
            'District', 'Democratic Votes', 'Democratic Votes SD',
            'Republican Votes', 'Republican Votes, SD', 'Population 2015',
            'US President 2016 - DEM', 'US President 2016 - REP',
            'US Senate 2016 - DEM', 'US Senate 2016 - REP'))})
        
        has_incumbency = bool(self.model and self.model.incumbency)
        
        try:
            column_names = sorted(self.districts[0]['totals'].keys(),
                key=lambda k: (sorting_hints.get(k, 999), k))
            
            column_names.extend(self.districts[0]['compactness'].keys())
            extra_columns = ['Candidate Scenario'] if has_incumbency else []
                
            out = io.StringIO()
            rows = csv.DictWriter(out,
                ['District'] + extra_columns + column_names, dialect='excel-tab')
            rows.writeheader()
            for (index, district) in enumerate(self.districts):
                totals, compactness = district['totals'], district['compactness']
                extra_values = {'Candidate Scenario': self.incumbents[index]} if has_incumbency else {}
                rows.writerow(dict(District=index+1, **dict(totals, **dict(compactness, **extra_values))))
        
        except Exception as e:
            return f'Error: {e}\n'

        else:
            return out.getvalue()
    
    def to_dict(self):
        progress = self.progress.to_list() if (self.progress is not None) else None

        return dict(
            id = self.id,
            key = self.key,
            model = (self.model.to_dict() if self.model else None),
            districts = self.districts,
            incumbents = self.incumbents,
            summary = self.summary,
            progress = progress,
            start_time = self.start_time,
            message = self.message,
            description = self.description,
            )
    
    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)
    
    def clone(self, model=None, districts=None, incumbents=None, summary=None, progress=None,
        start_time=None, message=None, description=None):
        return Upload(self.id, self.key,
            model = model or self.model,
            districts = districts or self.districts,
            incumbents = incumbents or self.incumbents,
            summary = summary or self.summary,
            progress = progress if (progress is not None) else self.progress,
            start_time = start_time or self.start_time,
            message = message or self.message,
            description = description or self.description,
            )
    
    @staticmethod
    def from_dict(data):
        progress = Progress(*data['progress']) if data.get('progress') else None
        model = Model.from_dict(data['model']) if data.get('model') else None
    
        return Upload(
            id = data['id'], 
            key = data['key'],
            model = model,
            districts = data.get('districts'),
            incumbents = data.get('incumbents'),
            summary = data.get('summary'),
            progress = progress,
            start_time = data.get('start_time'),
            message = data.get('message'),
            description = data.get('description'),
            )
    
    @staticmethod
    def from_json(body):
        return Upload.from_dict(json.loads(body))

# Active version of each state model

MODELS2017 = [
    Model(State.XX, House.statehouse,    2,  True, '2017', 'data/XX/004'),
    Model(State.MD, House.ushouse,       8, False, '2017', 'data/MD/001-ushouse-open'),
    Model(State.NC, House.ushouse,      13,  True, '2017', 'data/NC/008-ushouse'), # 0116f23
    Model(State.NC, House.statesenate,  50, False, '2017', 'data/NC/006-ncsenate'),
    Model(State.NC, House.statehouse,  120, False, '2017', 'data/NC/006-nchouse'),
    Model(State.PA, House.ushouse,      18, False, '2017', 'data/PA/008-ushouse'), # 8c546bb
    Model(State.PA, House.statesenate,  50, False, '2017', 'data/PA/006-statesenate-multizoom'), # 25d464159
    Model(State.PA, House.statehouse,  203, False, '2017', 'data/PA/006-statehouse-multizoom'), # 25d464159
    Model(State.VA, House.statehouse,  100, False, '2017', 'data/VA/001-statehouse-open'), # d2f65a55f
    Model(State.WI, House.ushouse,       8, False, '2017', 'data/WI/002-ushouse'),
    Model(State.WI, House.statesenate,  33, False, '2017', 'data/WI/002-statesenate'),
    Model(State.WI, House.statehouse,   99, False, '2017', 'data/WI/003-stateassembly-open'), # a073026
    ]

MODELS2020 = [
    Model(State.XX, House.statehouse,    2,  True, '2020', 'data/XX/005-unified'), # b8e19879
    Model(State.MD, House.ushouse,       8,  True, '2020', 'data/MD/002-unified'), # d30a99b
    Model(State.MD, House.statesenate,  47,  True, '2020', 'data/MD/002-unified'), # d30a99b
    Model(State.MD, House.statehouse,  141,  True, '2020', 'data/MD/002-unified'), # d30a99b
    Model(State.NC, House.ushouse,      13,  True, '2020', 'data/NC/010-unified'), # 514e73a
    Model(State.NC, House.statesenate,  50,  True, '2020', 'data/NC/010-unified'), # 514e73a
    Model(State.NC, House.statehouse,  120,  True, '2020', 'data/NC/010-unified'), # 514e73a
    Model(State.PA, House.ushouse,      18,  True, '2020', 'data/PA/009-unified'), # d9fcd35
    Model(State.PA, House.statesenate,  50,  True, '2020', 'data/PA/009-unified'), # d9fcd35
    Model(State.PA, House.statehouse,  203,  True, '2020', 'data/PA/009-unified'), # d9fcd35
    Model(State.VA, House.ushouse,      11,  True, '2020', 'data/VA/002-unified'), # 08df871
    Model(State.VA, House.statesenate,  40,  True, '2020', 'data/VA/002-unified'), # 08df871
    Model(State.VA, House.statehouse,  100,  True, '2020', 'data/VA/002-unified'), # 08df871
    Model(State.WI, House.ushouse,       8,  True, '2020', 'data/WI/004-unified'), # 17e16d3
    Model(State.WI, House.statesenate,  33,  True, '2020', 'data/WI/004-unified'), # 17e16d3
    Model(State.WI, House.statehouse,   99,  True, '2020', 'data/WI/004-unified'), # 17e16d3
    ]
