import os, json, csv, io, time, enum, datetime
from . import constants

UPLOAD_PREFIX = 'uploads/{id}/upload/'
UPLOAD_INDEX_KEY = 'uploads/{id}/index.json'
UPLOAD_PLAINTEXT_KEY = 'uploads/{id}/index.txt'
UPLOAD_GEOMETRY_KEY = 'uploads/{id}/geometry.json'
UPLOAD_DISTRICTS_KEY = 'uploads/{id}/districts/{index}.json'
UPLOAD_GEOMETRIES_KEY = 'uploads/{id}/geometries/{index}.wkt'
UPLOAD_GEOMETRY_BBOXES_KEY = 'uploads/{id}/geometry-bboxes.geojson'
UPLOAD_ASSIGNMENTS_KEY = 'uploads/{id}/assignments/{index}.txt'
UPLOAD_TILE_INDEX_KEY = 'uploads/{id}/tiles.json'
UPLOAD_ASSIGNMENT_INDEX_KEY = 'uploads/{id}/assignments.json'
UPLOAD_TILES_KEY = 'uploads/{id}/tiles/{zxy}.json'
UPLOAD_SLICES_KEY = 'uploads/{id}/slices/{geoid}.json'
UPLOAD_TIMING_KEY = 'logs/timing/ds={ds}/{id}.txt'
UPLOAD_LOGENTRY_KEY = 'logs/scoring/ds={ds}/{guid}.txt'

class State (enum.Enum):
    XX = 'XX'

    AK = 'AK'
    AL = 'AL'
    AR = 'AR'
    AZ = 'AZ'
    CA = 'CA'
    CO = 'CO'
    DE = 'DE'
    FL = 'FL'
    GA = 'GA'
    HI = 'HI'
    IA = 'IA'
    ID = 'ID'
    IL = 'IL'
    IN = 'IN'
    KS = 'KS'
    KY = 'KY'
    LA = 'LA'
    MA = 'MA'
    MD = 'MD'
    ME = 'ME'
    MI = 'MI'
    MN = 'MN'
    MO = 'MO'
    MT = 'MT'
    NC = 'NC'
    NE = 'NE'
    ND = 'ND'
    NH = 'NH'
    NJ = 'NJ'
    NM = 'NM'
    NV = 'NV'
    OH = 'OH'
    OK = 'OK'
    OR = 'OR'
    PA = 'PA'
    RI = 'RI'
    SC = 'SC'
    SD = 'SD'
    TN = 'TN'
    TX = 'TX'
    UT = 'UT'
    VA = 'VA'
    VT = 'VT'
    WA = 'WA'
    WI = 'WI'
    WY = 'WY'

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
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))
    
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

    def __init__(self, id, key, model:Model=None, districts=None, incumbents=None,
            summary=None, progress=None, start_time=None, message=None,
            description=None, geometry_key=None, status=None, auth_token=None,
            **ignored):
        self.id = id
        self.key = key
        self.model = model
        self.status = status
        self.districts = districts or []
        self.incumbents = incumbents or []
        self.summary = summary or {}
        self.progress = progress
        self.start_time = start_time or time.time()
        self.message = message
        self.description = description
        self.geometry_key = geometry_key
        self.commit_sha = os.environ.get('GIT_COMMIT_SHA')
        self.auth_token = auth_token
        
        if not incumbents:
            self.incumbents = [Incumbency.Open.value for i in range(len(self.districts))]
    
    def is_overdue(self):
        return bool(time.time() > (self.start_time + constants.UPLOAD_TIME_LIMIT))
    
    def index_key(self):
        return UPLOAD_INDEX_KEY.format(id=self.id)
    
    def plaintext_key(self):
        return UPLOAD_PLAINTEXT_KEY.format(id=self.id)
    
    def district_key(self, index):
        return UPLOAD_DISTRICTS_KEY.format(id=self.id, index=index)
    
    def logentry_key(self, guid):
        ds = datetime.date.fromtimestamp(self.start_time).strftime('%Y-%m-%d')
        return UPLOAD_LOGENTRY_KEY.format(ds=ds, guid=guid)
    
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
            status = self.status,
            districts = self.districts,
            incumbents = self.incumbents,
            summary = self.summary,
            progress = progress,
            start_time = self.start_time,
            message = self.message,
            description = self.description,
            geometry_key = self.geometry_key,
            commit_sha = self.commit_sha,
            )
    
    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)
    
    def to_logentry(self):
        ''' Export current plan information to a tab-delimited plaintext file
        '''
        if self.auth_token:
            obscured_token = self.auth_token[:len(self.auth_token)//2] + '********'
        else:
            obscured_token = None
        
        # Important: only append to this list to maintain 
        # backward-compatibility with older entries for PrestoDB
        logentry = [
            # ID string from generate_signed_id()
            self.id,
            
            # Current unix timestamp double
            time.time(),
            
            # Elapsed time in seconds float
            time.time() - self.start_time,
            
            # Text message string
            self.message,
            
            # Model state string
            (self.model.to_dict().get('state') if self.model else None),
            
            # Model house string
            (self.model.to_dict().get('house') if self.model else None),
            
            # Model JSON string
            (self.model.to_json() if self.model else None),
            
            # Upload key string
            self.key,
            
            # Upload status
            {True: 't', False: 'f', None: ''}.get(self.status),
            
            # Auth token
            obscured_token,
        ]
        
        try:
            out = io.StringIO()
            rows = csv.writer(out, dialect='excel-tab', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            rows.writerow(logentry)
        
        except Exception as e:
            return f'Error: {e}\n'

        else:
            return out.getvalue()
    
    def clone(self, model=None, districts=None, incumbents=None, summary=None, progress=None,
        start_time=None, message=None, description=None, geometry_key=None, status=None,
        auth_token=None):
        return Upload(self.id, self.key,
            model = model or self.model,
            status = status if (self.status is None) else self.status,
            districts = districts or self.districts,
            incumbents = incumbents or self.incumbents,
            summary = summary or self.summary,
            progress = progress if (progress is not None) else self.progress,
            start_time = start_time or self.start_time,
            message = message or self.message,
            description = description or self.description,
            geometry_key = geometry_key or self.geometry_key,
            auth_token = auth_token,
            )
    
    @staticmethod
    def from_dict(data):
        progress = Progress(*data['progress']) if data.get('progress') else None
        model = Model.from_dict(data['model']) if data.get('model') else None
    
        return Upload(
            id = data['id'], 
            key = data['key'],
            model = model,
            status = data.get('status'),
            districts = data.get('districts'),
            incumbents = data.get('incumbents'),
            summary = data.get('summary'),
            progress = progress,
            start_time = data.get('start_time'),
            message = data.get('message'),
            description = data.get('description'),
            geometry_key = data.get('geometry_key'),
            auth_token = data.get('auth_token'),
            )
    
    @staticmethod
    def from_json(body):
        return Upload.from_dict(json.loads(body))

# Active version of each state model

VERSION = '2021A'

MODELS = [
    Model(State.XX, House.statehouse,    2,  True, VERSION, 'data/XX/006-tilesdir'), # b8e19879
    Model(State.AK, House.ushouse,       1,  True, VERSION, 'data/AK/002-2021A'), # 3017cc8
    Model(State.AK, House.statesenate,  20,  True, VERSION, 'data/AK/002-2021A'), # 3017cc8
    Model(State.AK, House.statehouse,   40,  True, VERSION, 'data/AK/002-2021A'), # 3017cc8
    Model(State.AL, House.ushouse,       7,  True, VERSION, 'data/AL/002-2021A'), # 3017cc8
    Model(State.AL, House.statesenate,  35,  True, VERSION, 'data/AL/002-2021A'), # 3017cc8
    Model(State.AL, House.statehouse,  105,  True, VERSION, 'data/AL/002-2021A'), # 3017cc8
    Model(State.AR, House.ushouse,       4,  True, VERSION, 'data/AR/002-vest2020'), # 07af6c9
    Model(State.AR, House.statesenate,  35,  True, VERSION, 'data/AR/002-vest2020'), # 07af6c9
    Model(State.AR, House.statehouse,  100,  True, VERSION, 'data/AR/002-vest2020'), # 07af6c9
    Model(State.AZ, House.ushouse,       9,  True, VERSION, 'data/AZ/005-newvotes'), # 7dd1d71
    Model(State.AZ, House.statesenate,  30,  True, VERSION, 'data/AZ/005-newvotes'), # 7dd1d71
    Model(State.AZ, House.statehouse,   60,  True, VERSION, 'data/AZ/005-newvotes'), # 7dd1d71
    Model(State.CA, House.ushouse,      55,  True, VERSION, 'data/CA/002-tilesdir'), # b969229
    Model(State.CA, House.statesenate,  40,  True, VERSION, 'data/CA/002-tilesdir'), # b969229
    Model(State.CA, House.statehouse,   80,  True, VERSION, 'data/CA/002-tilesdir'), # b969229
    Model(State.CO, House.ushouse,       7,  True, VERSION, 'data/CO/003-vest2020'), # 924e34c
    Model(State.CO, House.statesenate,  35,  True, VERSION, 'data/CO/003-vest2020'), # 924e34c
    Model(State.CO, House.statehouse,   65,  True, VERSION, 'data/CO/003-vest2020'), # 924e34c
    Model(State.DE, House.ushouse,       1,  True, VERSION, 'data/DE/004-2021A'), # 3017cc8
    Model(State.DE, House.statesenate,  21,  True, VERSION, 'data/DE/004-2021A'), # 3017cc8
    Model(State.DE, House.statehouse,   41,  True, VERSION, 'data/DE/004-2021A'), # 3017cc8
    Model(State.FL, House.ushouse,      27,  True, VERSION, 'data/FL/003-tilesdir'), # 56f7c85
    Model(State.FL, House.statesenate,  40,  True, VERSION, 'data/FL/003-tilesdir'), # 56f7c85
    Model(State.FL, House.statehouse,  120,  True, VERSION, 'data/FL/003-tilesdir'), # 56f7c85
    Model(State.GA, House.ushouse,      14,  True, VERSION, 'data/GA/006-vest2020'), # 924e34c
    Model(State.GA, House.statesenate,  56,  True, VERSION, 'data/GA/006-vest2020'), # 924e34c
    Model(State.GA, House.statehouse,  180,  True, VERSION, 'data/GA/006-vest2020'), # 924e34c
    Model(State.HI, House.ushouse,       2,  True, VERSION, 'data/HI/002-2021A'), # 3017cc8
    Model(State.HI, House.statesenate,  25,  True, VERSION, 'data/HI/002-2021A'), # 3017cc8
    Model(State.HI, House.statehouse,   51,  True, VERSION, 'data/HI/002-2021A'), # 3017cc8
    Model(State.IA, House.ushouse,       4,  True, VERSION, 'data/IA/002-2021A'), # 3017cc8
    Model(State.IA, House.statesenate,  50,  True, VERSION, 'data/IA/002-2021A'), # 3017cc8
    Model(State.IA, House.statehouse,  100,  True, VERSION, 'data/IA/002-2021A'), # 3017cc8
    Model(State.ID, House.ushouse,       2,  True, VERSION, 'data/ID/002-2021A'), # 3017cc8
    Model(State.ID, House.statesenate,  35,  True, VERSION, 'data/ID/002-2021A'), # 3017cc8
    Model(State.ID, House.statehouse,   70,  True, VERSION, 'data/ID/002-2021A'), # 3017cc8
    Model(State.IL, House.ushouse,      18,  True, VERSION, 'data/IL/004-2021A'), # 3017cc8
    Model(State.IL, House.statesenate,  59,  True, VERSION, 'data/IL/004-2021A'), # 3017cc8
    Model(State.IL, House.statehouse,  118,  True, VERSION, 'data/IL/004-2021A'), # 3017cc8
    Model(State.IN, House.ushouse,       9,  True, VERSION, 'data/IN/002-tilesdir'), # 45a92e3
    Model(State.IN, House.statesenate,  50,  True, VERSION, 'data/IN/002-tilesdir'), # 45a92e3
    Model(State.IN, House.statehouse,  100,  True, VERSION, 'data/IN/002-tilesdir'), # 45a92e3
    Model(State.KS, House.ushouse,       5,  True, VERSION, 'data/KS/003-2021A'), # 3017cc8
    Model(State.KS, House.statesenate,  40,  True, VERSION, 'data/KS/003-2021A'), # 3017cc8
    Model(State.KS, House.statehouse,  125,  True, VERSION, 'data/KS/003-2021A'), # 3017cc8
    Model(State.KY, House.ushouse,       6,  True, VERSION, 'data/KY/001-tilesdir'), # bcf3dd1
    Model(State.KY, House.statesenate,  38,  True, VERSION, 'data/KY/001-tilesdir'), # bcf3dd1
    Model(State.KY, House.statehouse,  100,  True, VERSION, 'data/KY/001-tilesdir'), # bcf3dd1
    Model(State.LA, House.ushouse,       6,  True, VERSION, 'data/LA/002-2021A'), # 3017cc8
    Model(State.LA, House.statesenate,  39,  True, VERSION, 'data/LA/002-2021A'), # 3017cc8
    Model(State.LA, House.statehouse,  105,  True, VERSION, 'data/LA/002-2021A'), # 3017cc8
    Model(State.MA, House.ushouse,       9,  True, VERSION, 'data/MA/003-tilesdir'), # 56f7c85
    Model(State.MA, House.statesenate,  40,  True, VERSION, 'data/MA/003-tilesdir'), # 56f7c85
    Model(State.MA, House.statehouse,  160,  True, VERSION, 'data/MA/003-tilesdir'), # 56f7c85
    Model(State.MD, House.ushouse,       8,  True, VERSION, 'data/MD/005-tilesdir'), # 56f7c85
    Model(State.MD, House.statesenate,  47,  True, VERSION, 'data/MD/005-tilesdir'), # 56f7c85
    Model(State.MD, House.statehouse,   68,  True, VERSION, 'data/MD/005-tilesdir'), # 56f7c85
    Model(State.ME, House.ushouse,       2,  True, VERSION, 'data/ME/004-vest2020'), # 924e34c
    Model(State.ME, House.statesenate,  35,  True, VERSION, 'data/ME/004-vest2020'), # 924e34c
    Model(State.ME, House.statehouse,  151,  True, VERSION, 'data/ME/004-vest2020'), # 924e34c
    Model(State.MI, House.ushouse,      14,  True, VERSION, 'data/MI/005-vest2020'), # 07af6c9
    Model(State.MI, House.statesenate,  38,  True, VERSION, 'data/MI/005-vest2020'), # 07af6c9
    Model(State.MI, House.statehouse,  110,  True, VERSION, 'data/MI/005-vest2020'), # 07af6c9
    Model(State.MN, House.ushouse,       8,  True, VERSION, 'data/MN/004-2021A'), # 3017cc8
    Model(State.MN, House.statesenate,  67,  True, VERSION, 'data/MN/004-2021A'), # 3017cc8
    Model(State.MN, House.statehouse,  134,  True, VERSION, 'data/MN/004-2021A'), # 3017cc8
    Model(State.MO, House.ushouse,       8,  True, VERSION, 'data/MO/002-tilesdir'), # 9f98656
    Model(State.MO, House.statesenate,  34,  True, VERSION, 'data/MO/002-tilesdir'), # 9f98656
    Model(State.MO, House.statehouse,  163,  True, VERSION, 'data/MO/002-tilesdir'), # 9f98656
    Model(State.MT, House.ushouse,       1,  True, VERSION, 'data/MT/004-2021A'), # 3017cc8
    Model(State.MT, House.statesenate,  50,  True, VERSION, 'data/MT/004-2021A'), # 3017cc8
    Model(State.MT, House.statehouse,  100,  True, VERSION, 'data/MT/004-2021A'), # 3017cc8
    Model(State.NC, House.ushouse,      13,  True, VERSION, 'data/NC/016-vest2020'), # 924e34c
    Model(State.NC, House.statesenate,  50,  True, VERSION, 'data/NC/016-vest2020'), # 924e34c
    Model(State.NC, House.statehouse,  120,  True, VERSION, 'data/NC/016-vest2020'), # 924e34c
    Model(State.ND, House.ushouse,       1,  True, VERSION, 'data/ND/004-vest2020'), # 07af6c9
    Model(State.ND, House.statesenate,  47,  True, VERSION, 'data/ND/004-vest2020'), # 07af6c9
    Model(State.ND, House.statehouse,   94,  True, VERSION, 'data/ND/004-vest2020'), # 07af6c9
    Model(State.NE, House.ushouse,       3,  True, VERSION, 'data/NE/002-vest2020'), # 07af6c9
    Model(State.NE, House.statesenate,  49,  True, VERSION, 'data/NE/002-vest2020'), # 07af6c9
    Model(State.NH, House.ushouse,       2,  True, VERSION, 'data/NH/004-2021A'), # 3017cc8
    Model(State.NH, House.statesenate,  24,  True, VERSION, 'data/NH/004-2021A'), # 3017cc8
    Model(State.NH, House.statehouse,  400,  True, VERSION, 'data/NH/004-2021A'), # 3017cc8
    Model(State.NJ, House.ushouse,      12,  True, VERSION, 'data/NJ/001-tilesdir'), # bcf3dd1
    Model(State.NJ, House.statesenate,  40,  True, VERSION, 'data/NJ/001-tilesdir'), # bcf3dd1
    Model(State.NJ, House.statehouse,   80,  True, VERSION, 'data/NJ/001-tilesdir'), # bcf3dd1
    Model(State.NM, House.ushouse,       3,  True, VERSION, 'data/NM/001-ACS2019'), # ac34e68
    Model(State.NM, House.statesenate,  42,  True, VERSION, 'data/NM/001-ACS2019'), # ac34e68
    Model(State.NM, House.statehouse,   70,  True, VERSION, 'data/NM/001-ACS2019'), # ac34e68
    Model(State.NV, House.ushouse,       4,  True, VERSION, 'data/NV/002-vest2020'), # 924e34c
    Model(State.NV, House.statesenate,  21,  True, VERSION, 'data/NV/002-vest2020'), # 924e34c
    Model(State.NV, House.statehouse,   42,  True, VERSION, 'data/NV/002-vest2020'), # 924e34c
    Model(State.OH, House.ushouse,      16,  True, VERSION, 'data/OH/003-2021A'), # 3017cc8
    Model(State.OH, House.statesenate,  33,  True, VERSION, 'data/OH/003-2021A'), # 3017cc8
    Model(State.OH, House.statehouse,   99,  True, VERSION, 'data/OH/003-2021A'), # 3017cc8
    Model(State.OK, House.ushouse,       5,  True, VERSION, 'data/OK/002-2021A'), # 3017cc8
    Model(State.OK, House.statesenate,  48,  True, VERSION, 'data/OK/002-2021A'), # 3017cc8
    Model(State.OK, House.statehouse,  101,  True, VERSION, 'data/OK/002-2021A'), # 3017cc8
    Model(State.OR, House.ushouse,       5,  True, VERSION, 'data/OR/002-tilesdir'), # 57155ad
    Model(State.OR, House.statesenate,  30,  True, VERSION, 'data/OR/002-tilesdir'), # 57155ad
    Model(State.OR, House.statehouse,   60,  True, VERSION, 'data/OR/002-tilesdir'), # 57155ad
    Model(State.PA, House.ushouse,      18,  True, VERSION, 'data/PA/011-2021A'), # 2b48a6a
    Model(State.PA, House.statesenate,  50,  True, VERSION, 'data/PA/011-2021A'), # 2b48a6a
    Model(State.PA, House.statehouse,  203,  True, VERSION, 'data/PA/011-2021A'), # 2b48a6a
    Model(State.RI, House.ushouse,       2,  True, VERSION, 'data/RI/004-2021A'), # 3017cc8
    Model(State.RI, House.statesenate,  38,  True, VERSION, 'data/RI/004-2021A'), # 3017cc8
    Model(State.RI, House.statehouse,   75,  True, VERSION, 'data/RI/004-2021A'), # 3017cc8
    Model(State.SC, House.ushouse,       7,  True, VERSION, 'data/SC/002-2021A'), # 3017cc8
    Model(State.SC, House.statesenate,  46,  True, VERSION, 'data/SC/002-2021A'), # 3017cc8
    Model(State.SC, House.statehouse,  124,  True, VERSION, 'data/SC/002-2021A'), # 3017cc8
    Model(State.SD, House.ushouse,       1,  True, VERSION, 'data/SD/003-ACS2019'), # 0d7207e
    Model(State.SD, House.statesenate,  35,  True, VERSION, 'data/SD/003-ACS2019'), # 0d7207e
    Model(State.SD, House.statehouse,   70,  True, VERSION, 'data/SD/003-ACS2019'), # 0d7207e
    Model(State.TN, House.ushouse,       9,  True, VERSION, 'data/TN/003-tilesdir'), # 56f7c85
    Model(State.TN, House.statesenate,  33,  True, VERSION, 'data/TN/003-tilesdir'), # 56f7c85
    Model(State.TN, House.statehouse,   99,  True, VERSION, 'data/TN/003-tilesdir'), # 56f7c85
    Model(State.TX, House.ushouse,      36,  True, VERSION, 'data/TX/004-vest2020'), # 07af6c9
    Model(State.TX, House.statesenate,  31,  True, VERSION, 'data/TX/004-vest2020'), # 07af6c9
    Model(State.TX, House.statehouse,  150,  True, VERSION, 'data/TX/004-vest2020'), # 07af6c9
    Model(State.UT, House.ushouse,       4,  True, VERSION, 'data/UT/002-vest2020'), # 924e34c
    Model(State.UT, House.statesenate,  29,  True, VERSION, 'data/UT/002-vest2020'), # 924e34c
    Model(State.UT, House.statehouse,   75,  True, VERSION, 'data/UT/002-vest2020'), # 924e34c
    Model(State.VA, House.ushouse,      11,  True, VERSION, 'data/VA/004-2021A'), # 2b48a6a
    Model(State.VA, House.statesenate,  40,  True, VERSION, 'data/VA/004-2021A'), # 2b48a6a
    Model(State.VA, House.statehouse,  100,  True, VERSION, 'data/VA/004-2021A'), # 2b48a6a
    Model(State.VT, House.ushouse,       1,  True, VERSION, 'data/VT/004-vest2020'), # 924e34c
    Model(State.VT, House.statesenate,  30,  True, VERSION, 'data/VT/004-vest2020'), # 924e34c
    Model(State.VT, House.statehouse,  150,  True, VERSION, 'data/VT/004-vest2020'), # 924e34c
    Model(State.WA, House.ushouse,      10,  True, VERSION, 'data/WA/002-tilesdir'), # 57155ad
    Model(State.WA, House.statesenate,  49,  True, VERSION, 'data/WA/002-tilesdir'), # 57155ad
    Model(State.WA, House.statehouse,   98,  True, VERSION, 'data/WA/002-tilesdir'), # 57155ad
    Model(State.WI, House.ushouse,       8,  True, VERSION, 'data/WI/008-2021A'), # 3017cc8
    Model(State.WI, House.statesenate,  33,  True, VERSION, 'data/WI/008-2021A'), # 3017cc8
    Model(State.WI, House.statehouse,   99,  True, VERSION, 'data/WI/008-2021A'), # 3017cc8
    Model(State.WY, House.ushouse,       1,  True, VERSION, 'data/WY/004-2021A'), # 3017cc8
    Model(State.WY, House.statesenate,  30,  True, VERSION, 'data/WY/004-2021A'), # 3017cc8
    Model(State.WY, House.statehouse,   60,  True, VERSION, 'data/WY/004-2021A'), # 3017cc8
    ]
