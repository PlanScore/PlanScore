import os, json, csv, io, time, enum, datetime, collections
from . import constants

UPLOAD_PREFIX = 'uploads/{id}/upload/'
UPLOAD_INDEX_KEY = 'uploads/{id}/index.json'
UPLOAD_PLAINTEXT_KEY = 'uploads/{id}/index.txt'
UPLOAD_GEOMETRY_KEY = 'uploads/{id}/geometry.json'
UPLOAD_DISTRICTS_KEY = 'uploads/{id}/districts/{index}.json'
UPLOAD_GEOMETRIES_KEY = 'uploads/{id}/geometries/{index}.wkt'
UPLOAD_GEOMETRY_BBOXES_KEY = 'uploads/{id}/geometry-bboxes.geojson'
UPLOAD_ASSIGNMENTS_KEY = 'uploads/{id}/assignments/{index}.txt'
UPLOAD_DISTRICTS_PARTITION_KEY = 'uploads/{id}/districts/partition.csv.gz'
UPLOAD_TILE_INDEX_KEY = 'uploads/{id}/tiles.json'
UPLOAD_ASSIGNMENT_INDEX_KEY = 'uploads/{id}/assignments.json'
UPLOAD_TIMING_KEY = 'logs/timing/ds={ds}/{id}.txt'
UPLOAD_LOGENTRY_KEY = 'logs/scoring/ds={ds}/{guid}.txt'

VersionParameters = collections.namedtuple(
    'VersionParameters',
    (
        # User-visible description
        'description',
        
        # Find matrix files in planscore/model/ directory
        'path_suffix',

        # A hard-coded year to make predictions for
        'year',

        # The presidential vote in the model is mean-deviated, so you have to
        # subtract this adjustment value from the presidential vote values in
        # each district. Values are given as Democratic vote portion from 0. to
        # 1. and become approximately -0.5 to +0.5.
        'vote_adjust_congress',
        'vote_adjust_statelege',

        # True 2016 and 2020 presidential votes may need to be scaled and
        # offset for compatibility with the C and E matrixes.
        'pvote2016_scale',
        'pvote2016_offset',
        'pvote2020_scale',
        'pvote2020_offset',
        
        # Include as option on annotation page?
        'is_public',
    ),
)

# Dict order is significant, default is first
VERSION_PARAMETERS = {
    '2025A': VersionParameters(
        'New: rerun the 2020 election with more accurate updated data (updated August 2025)',
        '-2025A', 2020, -0.523, -0.495, 1., 0., 1., 0.,
        True,
    ),
    '2021B': VersionParameters(
        'Original: rerun an average election from the past 10 years with best available data from before Census release',
        '-2021B', None, -0.496875, -0.496875, 0.91, 0.05, 0.96, 0.01,
        True,
    ),
}

class State (enum.Enum):
    XX = 'XX'

    AK = 'AK'
    AL = 'AL'
    AR = 'AR'
    AZ = 'AZ'
    CA = 'CA'
    CO = 'CO'
    CT = 'CT'
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
    MS = 'MS'
    MT = 'MT'
    NC = 'NC'
    NE = 'NE'
    ND = 'ND'
    NH = 'NH'
    NJ = 'NJ'
    NM = 'NM'
    NV = 'NV'
    NY = 'NY'
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
    WV = 'WV'
    WY = 'WY'

class House (enum.Enum):
    ushouse = 'ushouse'
    statesenate = 'statesenate'
    statehouse = 'statehouse'
    localplan = 'localplan'

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

    def __init__(self, state:State, house:House, seats:int, incumbency:bool, versions:list, key_prefix:str):
        self.state = state
        self.house = house
        self.seats = seats
        self.key_prefix = key_prefix
        self.incumbency = incumbency
        self.versions = versions
    
    def to_dict(self):
        return dict(
            state = self.state.value,
            house = self.house.value,
            seats = self.seats,
            key_prefix = self.key_prefix,
            incumbency = self.incumbency,
            versions = self.versions,
            )
    
    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))
    
    @staticmethod
    def from_dict(data):
        return Model(
            state = State[data['state']],
            house = House[data['house']],
            seats = None if data['seats'] is None else int(data['seats']),
            key_prefix = str(data['key_prefix']),
            incumbency = bool(data.get('incumbency')),
            versions = data.get('versions', [data.get('version', '2017')]),
            )
    
    @staticmethod
    def from_json(body):
        return Model.from_dict(json.loads(body))

class Upload:

    def __init__(self, id, key, model:Model=None, districts=None, incumbents=None,
            summary=None, progress=None, start_time=None, message=None,
            description=None, geometry_key=None, status=None,
            library_metadata=None, auth_token=None, model_version=None,
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
        self.library_metadata = library_metadata
        self.auth_token = auth_token
        self.model_version = model_version
        
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
                rows.writerow(dict(
                    District = district.get('number', index+1),
                    **dict(totals, **dict(compactness, **extra_values)),
                ))
        
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
            library_metadata = self.library_metadata,
            model_version = self.model_version,
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
            
            # User-selected model version
            self.model_version,
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
        library_metadata=None, auth_token=None, model_version=None):
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
            library_metadata = library_metadata or self.library_metadata,
            auth_token = auth_token,
            model_version = model_version or self.model_version,
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
            library_metadata = data.get('library_metadata'),
            auth_token = data.get('auth_token'),
            model_version = data.get('model_version'),
            )
    
    @staticmethod
    def from_json(body):
        return Upload.from_dict(json.loads(body))

# Active version of each state model

VERSIONS = list(VERSION_PARAMETERS.keys()) # rely on dict order
DEFAULT_VERSION = VERSIONS[0]

MODELS = [
    Model(State.XX, House.statehouse,    2,  True, VERSIONS, 'data/XX/006-tilesdir'), # b8e19879
    Model(State.AK, House.ushouse,       1,  True, VERSIONS, 'data/AK/008-acs-2020'), # c82db89
    Model(State.AK, House.statesenate,  20,  True, VERSIONS, 'data/AK/008-acs-2020'), # c82db89
    Model(State.AK, House.statehouse,   40,  True, VERSIONS, 'data/AK/008-acs-2020'), # c82db89
    Model(State.AK, House.localplan,  None,  True, VERSIONS, 'data/AK/008-acs-2020'), # c82db89
    Model(State.AL, House.ushouse,       7,  True, VERSIONS, 'data/AL/008-acs-2020'), # c82db89
    Model(State.AL, House.statesenate,  35,  True, VERSIONS, 'data/AL/008-acs-2020'), # c82db89
    Model(State.AL, House.statehouse,  105,  True, VERSIONS, 'data/AL/008-acs-2020'), # c82db89
    Model(State.AL, House.localplan,  None,  True, VERSIONS, 'data/AL/008-acs-2020'), # c82db89
    Model(State.AR, House.ushouse,       4,  True, VERSIONS, 'data/AR/008-acs-2020'), # c82db89
    Model(State.AR, House.statesenate,  35,  True, VERSIONS, 'data/AR/008-acs-2020'), # c82db89
    Model(State.AR, House.statehouse,  100,  True, VERSIONS, 'data/AR/008-acs-2020'), # c82db89
    Model(State.AR, House.localplan,  None,  True, VERSIONS, 'data/AR/008-acs-2020'), # c82db89
    Model(State.AZ, House.ushouse,       9,  True, VERSIONS, 'data/AZ/012-acs-2020'), # c82db89
    Model(State.AZ, House.statesenate,  30,  True, VERSIONS, 'data/AZ/012-acs-2020'), # c82db89
    Model(State.AZ, House.statehouse,   60,  True, VERSIONS, 'data/AZ/012-acs-2020'), # c82db89
    Model(State.AZ, House.localplan,  None,  True, VERSIONS, 'data/AZ/012-acs-2020'), # c82db89
    Model(State.CA, House.ushouse,      52,  True, VERSIONS, 'data/CA/008-acs-2020'), # c82db89
    Model(State.CA, House.statesenate,  40,  True, VERSIONS, 'data/CA/008-acs-2020'), # c82db89
    Model(State.CA, House.statehouse,   80,  True, VERSIONS, 'data/CA/008-acs-2020'), # c82db89
    Model(State.CA, House.localplan,  None,  True, VERSIONS, 'data/CA/008-acs-2020'), # c82db89
    Model(State.CO, House.ushouse,       8,  True, VERSIONS, 'data/CO/013-acs-2020'), # c82db89
    Model(State.CO, House.statesenate,  35,  True, VERSIONS, 'data/CO/013-acs-2020'), # c82db89
    Model(State.CO, House.statehouse,   65,  True, VERSIONS, 'data/CO/013-acs-2020'), # c82db89
    Model(State.CO, House.localplan,  None,  True, VERSIONS, 'data/CO/013-acs-2020'), # c82db89
    Model(State.CT, House.ushouse,       5,  True, VERSIONS, 'data/CT/006-acs-2020'), # c82db89
    Model(State.CT, House.statesenate,  36,  True, VERSIONS, 'data/CT/006-acs-2020'), # c82db89
    Model(State.CT, House.statehouse,  151,  True, VERSIONS, 'data/CT/006-acs-2020'), # c82db89
    Model(State.CT, House.localplan,  None,  True, VERSIONS, 'data/CT/006-acs-2020'), # c82db89
    Model(State.DE, House.ushouse,       1,  True, VERSIONS, 'data/DE/010-acs-2020'), # c82db89
    Model(State.DE, House.statesenate,  21,  True, VERSIONS, 'data/DE/010-acs-2020'), # c82db89
    Model(State.DE, House.statehouse,   41,  True, VERSIONS, 'data/DE/010-acs-2020'), # c82db89
    Model(State.DE, House.localplan,  None,  True, VERSIONS, 'data/DE/010-acs-2020'), # c82db89
    Model(State.FL, House.ushouse,      28,  True, VERSIONS, 'data/FL/010-acs-2020'), # c82db89
    Model(State.FL, House.statesenate,  40,  True, VERSIONS, 'data/FL/010-acs-2020'), # c82db89
    Model(State.FL, House.statehouse,  120,  True, VERSIONS, 'data/FL/010-acs-2020'), # c82db89
    Model(State.FL, House.localplan,  None,  True, VERSIONS, 'data/FL/010-acs-2020'), # c82db89
    Model(State.GA, House.ushouse,      14,  True, VERSIONS, 'data/GA/012-acs-2020'), # c82db89
    Model(State.GA, House.statesenate,  56,  True, VERSIONS, 'data/GA/012-acs-2020'), # c82db89
    Model(State.GA, House.statehouse,  180,  True, VERSIONS, 'data/GA/012-acs-2020'), # c82db89
    Model(State.GA, House.localplan,  None,  True, VERSIONS, 'data/GA/012-acs-2020'), # c82db89
    Model(State.HI, House.ushouse,       2,  True, VERSIONS, 'data/HI/008-acs-2020'), # c82db89
    Model(State.HI, House.statesenate,  25,  True, VERSIONS, 'data/HI/008-acs-2020'), # c82db89
    Model(State.HI, House.statehouse,   51,  True, VERSIONS, 'data/HI/008-acs-2020'), # c82db89
    Model(State.HI, House.localplan,  None,  True, VERSIONS, 'data/HI/008-acs-2020'), # c82db89
    Model(State.IA, House.ushouse,       4,  True, VERSIONS, 'data/IA/008-acs-2020'), # c82db89
    Model(State.IA, House.statesenate,  50,  True, VERSIONS, 'data/IA/008-acs-2020'), # c82db89
    Model(State.IA, House.statehouse,  100,  True, VERSIONS, 'data/IA/008-acs-2020'), # c82db89
    Model(State.IA, House.localplan,  None,  True, VERSIONS, 'data/IA/008-acs-2020'), # c82db89
    Model(State.ID, House.ushouse,       2,  True, VERSIONS, 'data/ID/008-acs-2020'), # c82db89
    Model(State.ID, House.statesenate,  35,  True, VERSIONS, 'data/ID/008-acs-2020'), # c82db89
    Model(State.ID, House.statehouse,   70,  True, VERSIONS, 'data/ID/008-acs-2020'), # c82db89
    Model(State.ID, House.localplan,  None,  True, VERSIONS, 'data/ID/008-acs-2020'), # c82db89
    Model(State.IL, House.ushouse,      17,  True, VERSIONS, 'data/IL/010-acs-2020'), # c82db89
    Model(State.IL, House.statesenate,  59,  True, VERSIONS, 'data/IL/010-acs-2020'), # c82db89
    Model(State.IL, House.statehouse,  118,  True, VERSIONS, 'data/IL/010-acs-2020'), # c82db89
    Model(State.IL, House.localplan,  None,  True, VERSIONS, 'data/IL/010-acs-2020'), # c82db89
    Model(State.IN, House.ushouse,       9,  True, VERSIONS, 'data/IN/009-acs-2020'), # c82db89
    Model(State.IN, House.statesenate,  50,  True, VERSIONS, 'data/IN/009-acs-2020'), # c82db89
    Model(State.IN, House.statehouse,  100,  True, VERSIONS, 'data/IN/009-acs-2020'), # c82db89
    Model(State.IN, House.localplan,  None,  True, VERSIONS, 'data/IN/009-acs-2020'), # c82db89
    Model(State.KS, House.ushouse,       5,  True, VERSIONS, 'data/KS/009-acs-2020'), # c82db89
    Model(State.KS, House.statesenate,  40,  True, VERSIONS, 'data/KS/009-acs-2020'), # c82db89
    Model(State.KS, House.statehouse,  125,  True, VERSIONS, 'data/KS/009-acs-2020'), # c82db89
    Model(State.KS, House.localplan,  None,  True, VERSIONS, 'data/KS/009-acs-2020'), # c82db89
    Model(State.KY, House.ushouse,       6,  True, VERSIONS, 'data/KY/007-acs-2020'), # c82db89
    Model(State.KY, House.statesenate,  38,  True, VERSIONS, 'data/KY/007-acs-2020'), # c82db89
    Model(State.KY, House.statehouse,  100,  True, VERSIONS, 'data/KY/007-acs-2020'), # c82db89
    Model(State.KY, House.localplan,  None,  True, VERSIONS, 'data/KY/007-acs-2020'), # c82db89
    Model(State.LA, House.ushouse,       6,  True, VERSIONS, 'data/LA/007-acs-2020'), # c82db89
    Model(State.LA, House.statesenate,  39,  True, VERSIONS, 'data/LA/007-acs-2020'), # c82db89
    Model(State.LA, House.statehouse,  105,  True, VERSIONS, 'data/LA/007-acs-2020'), # c82db89
    Model(State.LA, House.localplan,  None,  True, VERSIONS, 'data/LA/007-acs-2020'), # c82db89
    Model(State.MA, House.ushouse,       9,  True, VERSIONS, 'data/MA/010-acs-2020'), # c82db89
    Model(State.MA, House.statesenate,  40,  True, VERSIONS, 'data/MA/010-acs-2020'), # c82db89
    Model(State.MA, House.statehouse,  160,  True, VERSIONS, 'data/MA/010-acs-2020'), # c82db89
    Model(State.MA, House.localplan,  None,  True, VERSIONS, 'data/MA/010-acs-2020'), # c82db89
    Model(State.MD, House.ushouse,       8,  True, VERSIONS, 'data/MD/012-acs-2020'), # c82db89
    Model(State.MD, House.statesenate,  47,  True, VERSIONS, 'data/MD/012-acs-2020'), # c82db89
    Model(State.MD, House.statehouse,   68,  True, VERSIONS, 'data/MD/012-acs-2020'), # c82db89
    Model(State.MD, House.localplan,  None,  True, VERSIONS, 'data/MD/012-acs-2020'), # c82db89
    Model(State.ME, House.ushouse,       2,  True, VERSIONS, 'data/ME/011-acs-2020'), # c82db89
    Model(State.ME, House.statesenate,  35,  True, VERSIONS, 'data/ME/011-acs-2020'), # c82db89
    Model(State.ME, House.statehouse,  151,  True, VERSIONS, 'data/ME/011-acs-2020'), # c82db89
    Model(State.ME, House.localplan,  None,  True, VERSIONS, 'data/ME/011-acs-2020'), # c82db89
    Model(State.MI, House.ushouse,      13,  True, VERSIONS, 'data/MI/011-acs-2020'), # c82db89
    Model(State.MI, House.statesenate,  38,  True, VERSIONS, 'data/MI/011-acs-2020'), # c82db89
    Model(State.MI, House.statehouse,  110,  True, VERSIONS, 'data/MI/011-acs-2020'), # c82db89
    Model(State.MI, House.localplan,  None,  True, VERSIONS, 'data/MI/011-acs-2020'), # c82db89
    Model(State.MN, House.ushouse,       8,  True, VERSIONS, 'data/MN/010-acs-2020'), # c82db89
    Model(State.MN, House.statesenate,  67,  True, VERSIONS, 'data/MN/010-acs-2020'), # c82db89
    Model(State.MN, House.statehouse,  134,  True, VERSIONS, 'data/MN/010-acs-2020'), # c82db89
    Model(State.MN, House.localplan,  None,  True, VERSIONS, 'data/MN/010-acs-2020'), # c82db89
    Model(State.MO, House.ushouse,       8,  True, VERSIONS, 'data/MO/009-acs-2020'), # c82db89
    Model(State.MO, House.statesenate,  34,  True, VERSIONS, 'data/MO/009-acs-2020'), # c82db89
    Model(State.MO, House.statehouse,  163,  True, VERSIONS, 'data/MO/009-acs-2020'), # c82db89
    Model(State.MO, House.localplan,  None,  True, VERSIONS, 'data/MO/009-acs-2020'), # c82db89
    Model(State.MS, House.ushouse,       4,  True, VERSIONS, 'data/MS/004-acs-2020'), # c82db89
    Model(State.MS, House.statesenate,  52,  True, VERSIONS, 'data/MS/004-acs-2020'), # c82db89
    Model(State.MS, House.statehouse,  122,  True, VERSIONS, 'data/MS/004-acs-2020'), # c82db89
    Model(State.MS, House.localplan,  None,  True, VERSIONS, 'data/MS/004-acs-2020'), # c82db89
    Model(State.MT, House.ushouse,       2,  True, VERSIONS, 'data/MT/010-acs-2020'), # c82db89
    Model(State.MT, House.statesenate,  50,  True, VERSIONS, 'data/MT/010-acs-2020'), # c82db89
    Model(State.MT, House.statehouse,  100,  True, VERSIONS, 'data/MT/010-acs-2020'), # c82db89
    Model(State.MT, House.localplan,  None,  True, VERSIONS, 'data/MT/010-acs-2020'), # c82db89
    Model(State.NC, House.ushouse,      14,  True, VERSIONS, 'data/NC/022-acs-2020'), # c82db89
    Model(State.NC, House.statesenate,  50,  True, VERSIONS, 'data/NC/022-acs-2020'), # c82db89
    Model(State.NC, House.statehouse,  120,  True, VERSIONS, 'data/NC/022-acs-2020'), # c82db89
    Model(State.NC, House.localplan,  None,  True, VERSIONS, 'data/NC/022-acs-2020'), # c82db89
    Model(State.ND, House.ushouse,       1,  True, VERSIONS, 'data/ND/011-acs-2020'), # c82db89
    Model(State.ND, House.statesenate,  47,  True, VERSIONS, 'data/ND/011-acs-2020'), # c82db89
    Model(State.ND, House.statehouse,   94,  True, VERSIONS, 'data/ND/011-acs-2020'), # c82db89
    Model(State.ND, House.localplan,  None,  True, VERSIONS, 'data/ND/011-acs-2020'), # c82db89
    Model(State.NE, House.ushouse,       3,  True, VERSIONS, 'data/NE/008-acs-2020'), # c82db89
    Model(State.NE, House.statesenate,  49,  True, VERSIONS, 'data/NE/008-acs-2020'), # c82db89
    Model(State.NE, House.localplan,  None,  True, VERSIONS, 'data/NE/008-acs-2020'), # c82db89
    Model(State.NH, House.ushouse,       2,  True, VERSIONS, 'data/NH/010-acs-2020'), # c82db89
    Model(State.NH, House.statesenate,  24,  True, VERSIONS, 'data/NH/010-acs-2020'), # c82db89
    Model(State.NH, House.statehouse,  400,  True, VERSIONS, 'data/NH/010-acs-2020'), # c82db89
    Model(State.NH, House.localplan,  None,  True, VERSIONS, 'data/NH/010-acs-2020'), # c82db89
    Model(State.NJ, House.ushouse,      12,  True, VERSIONS, 'data/NJ/007-acs-2020'), # c82db89
    Model(State.NJ, House.statesenate,  40,  True, VERSIONS, 'data/NJ/007-acs-2020'), # c82db89
    Model(State.NJ, House.statehouse,   80,  True, VERSIONS, 'data/NJ/007-acs-2020'), # c82db89
    Model(State.NJ, House.localplan,  None,  True, VERSIONS, 'data/NJ/007-acs-2020'), # c82db89
    Model(State.NM, House.ushouse,       3,  True, VERSIONS, 'data/NM/008-acs-2020'), # c82db89
    Model(State.NM, House.statesenate,  42,  True, VERSIONS, 'data/NM/008-acs-2020'), # c82db89
    Model(State.NM, House.statehouse,   70,  True, VERSIONS, 'data/NM/008-acs-2020'), # c82db89
    Model(State.NM, House.localplan,  None,  True, VERSIONS, 'data/NM/008-acs-2020'), # c82db89
    Model(State.NV, House.ushouse,       4,  True, VERSIONS, 'data/NV/008-acs-2020'), # c82db89
    Model(State.NV, House.statesenate,  21,  True, VERSIONS, 'data/NV/008-acs-2020'), # c82db89
    Model(State.NV, House.statehouse,   42,  True, VERSIONS, 'data/NV/008-acs-2020'), # c82db89
    Model(State.NV, House.localplan,  None,  True, VERSIONS, 'data/NV/008-acs-2020'), # c82db89
    Model(State.NY, House.ushouse,      19,  True, VERSIONS, 'data/NY/003-acs-2020'), # c82db89
    Model(State.NY, House.statesenate,  63,  True, VERSIONS, 'data/NY/003-acs-2020'), # c82db89
    Model(State.NY, House.statehouse,  150,  True, VERSIONS, 'data/NY/003-acs-2020'), # c82db89
    Model(State.NY, House.localplan,  None,  True, VERSIONS, 'data/NY/003-acs-2020'), # c82db89
    Model(State.OH, House.ushouse,      15,  True, VERSIONS, 'data/OH/009-acs-2020'), # c82db89
    Model(State.OH, House.statesenate,  33,  True, VERSIONS, 'data/OH/009-acs-2020'), # c82db89
    Model(State.OH, House.statehouse,   99,  True, VERSIONS, 'data/OH/009-acs-2020'), # c82db89
    Model(State.OH, House.localplan,  None,  True, VERSIONS, 'data/OH/009-acs-2020'), # c82db89
    Model(State.OK, House.ushouse,       5,  True, VERSIONS, 'data/OK/008-acs-2020'), # c82db89
    Model(State.OK, House.statesenate,  48,  True, VERSIONS, 'data/OK/008-acs-2020'), # c82db89
    Model(State.OK, House.statehouse,  101,  True, VERSIONS, 'data/OK/008-acs-2020'), # c82db89
    Model(State.OK, House.localplan,  None,  True, VERSIONS, 'data/OK/008-acs-2020'), # c82db89
    Model(State.OR, House.ushouse,       6,  True, VERSIONS, 'data/OR/008-acs-2020'), # c82db89
    Model(State.OR, House.statesenate,  30,  True, VERSIONS, 'data/OR/008-acs-2020'), # c82db89
    Model(State.OR, House.statehouse,   60,  True, VERSIONS, 'data/OR/008-acs-2020'), # c82db89
    Model(State.OR, House.localplan,  None,  True, VERSIONS, 'data/OR/008-acs-2020'), # c82db89
    Model(State.PA, House.ushouse,      17,  True, VERSIONS, 'data/PA/019-acs-2020'), # c82db89
    Model(State.PA, House.statesenate,  50,  True, VERSIONS, 'data/PA/019-acs-2020'), # c82db89
    Model(State.PA, House.statehouse,  203,  True, VERSIONS, 'data/PA/019-acs-2020'), # c82db89
    Model(State.PA, House.localplan,  None,  True, VERSIONS, 'data/PA/019-acs-2020'), # c82db89
    Model(State.RI, House.ushouse,       2,  True, VERSIONS, 'data/RI/015-acs-2020'), # c82db89
    Model(State.RI, House.statesenate,  38,  True, VERSIONS, 'data/RI/015-acs-2020'), # c82db89
    Model(State.RI, House.statehouse,   75,  True, VERSIONS, 'data/RI/015-acs-2020'), # c82db89
    Model(State.RI, House.localplan,  None,  True, VERSIONS, 'data/RI/015-acs-2020'), # c82db89
    Model(State.SC, House.ushouse,       7,  True, VERSIONS, 'data/SC/008-acs-2020'), # c82db89
    Model(State.SC, House.statesenate,  46,  True, VERSIONS, 'data/SC/008-acs-2020'), # c82db89
    Model(State.SC, House.statehouse,  124,  True, VERSIONS, 'data/SC/008-acs-2020'), # c82db89
    Model(State.SC, House.localplan,  None,  True, VERSIONS, 'data/SC/008-acs-2020'), # c82db89
    Model(State.SD, House.ushouse,       1,  True, VERSIONS, 'data/SD/008-acs-2020'), # c82db89
    Model(State.SD, House.statesenate,  35,  True, VERSIONS, 'data/SD/008-acs-2020'), # c82db89
    Model(State.SD, House.statehouse,   70,  True, VERSIONS, 'data/SD/008-acs-2020'), # c82db89
    Model(State.SD, House.localplan,  None,  True, VERSIONS, 'data/SD/008-acs-2020'), # c82db89
    Model(State.TN, House.ushouse,       9,  True, VERSIONS, 'data/TN/009-acs-2020'), # c82db89
    Model(State.TN, House.statesenate,  33,  True, VERSIONS, 'data/TN/009-acs-2020'), # c82db89
    Model(State.TN, House.statehouse,   99,  True, VERSIONS, 'data/TN/009-acs-2020'), # c82db89
    Model(State.TN, House.localplan,  None,  True, VERSIONS, 'data/TN/009-acs-2020'), # c82db89
    Model(State.TX, House.ushouse,      38,  True, VERSIONS, 'data/TX/010-acs-2020'), # c82db89
    Model(State.TX, House.statesenate,  31,  True, VERSIONS, 'data/TX/010-acs-2020'), # c82db89
    Model(State.TX, House.statehouse,  150,  True, VERSIONS, 'data/TX/010-acs-2020'), # c82db89
    Model(State.TX, House.localplan,  None,  True, VERSIONS, 'data/TX/010-acs-2020'), # c82db89
    Model(State.UT, House.ushouse,       4,  True, VERSIONS, 'data/UT/008-acs-2020'), # c82db89
    Model(State.UT, House.statesenate,  29,  True, VERSIONS, 'data/UT/008-acs-2020'), # c82db89
    Model(State.UT, House.statehouse,   75,  True, VERSIONS, 'data/UT/008-acs-2020'), # c82db89
    Model(State.UT, House.localplan,  None,  True, VERSIONS, 'data/UT/008-acs-2020'), # c82db89
    Model(State.VA, House.ushouse,      11,  True, VERSIONS, 'data/VA/010-acs-2020'), # c82db89
    Model(State.VA, House.statesenate,  40,  True, VERSIONS, 'data/VA/010-acs-2020'), # c82db89
    Model(State.VA, House.statehouse,  100,  True, VERSIONS, 'data/VA/010-acs-2020'), # c82db89
    Model(State.VA, House.localplan,  None,  True, VERSIONS, 'data/VA/010-acs-2020'), # c82db89
    Model(State.VT, House.ushouse,       1,  True, VERSIONS, 'data/VT/010-acs-2020'), # c82db89
    Model(State.VT, House.statesenate,  30,  True, VERSIONS, 'data/VT/010-acs-2020'), # c82db89
    Model(State.VT, House.statehouse,  150,  True, VERSIONS, 'data/VT/010-acs-2020'), # c82db89
    Model(State.VT, House.localplan,  None,  True, VERSIONS, 'data/VT/010-acs-2020'), # c82db89
    Model(State.WA, House.ushouse,      10,  True, VERSIONS, 'data/WA/009-acs-2020'), # c82db89
    Model(State.WA, House.statesenate,  49,  True, VERSIONS, 'data/WA/009-acs-2020'), # c82db89
    Model(State.WA, House.statehouse,   98,  True, VERSIONS, 'data/WA/009-acs-2020'), # c82db89
    Model(State.WA, House.localplan,  None,  True, VERSIONS, 'data/WA/009-acs-2020'), # c82db89
    Model(State.WI, House.ushouse,       8,  True, VERSIONS, 'data/WI/014-acs-2020'), # c82db89
    Model(State.WI, House.statesenate,  33,  True, VERSIONS, 'data/WI/014-acs-2020'), # c82db89
    Model(State.WI, House.statehouse,   99,  True, VERSIONS, 'data/WI/014-acs-2020'), # c82db89
    Model(State.WI, House.localplan,  None,  True, VERSIONS, 'data/WI/014-acs-2020'), # c82db89
    Model(State.WV, House.ushouse,       3,  True, VERSIONS, 'data/WV/004-acs-2020'), # c82db89
    Model(State.WV, House.statesenate,  34,  True, VERSIONS, 'data/WV/004-acs-2020'), # c82db89
    Model(State.WV, House.statehouse,  100,  True, VERSIONS, 'data/WV/004-acs-2020'), # c82db89
    Model(State.WV, House.localplan,  None,  True, VERSIONS, 'data/WV/004-acs-2020'), # c82db89
    Model(State.WY, House.ushouse,       1,  True, VERSIONS, 'data/WY/010-acs-2020'), # c82db89
    Model(State.WY, House.statesenate,  30,  True, VERSIONS, 'data/WY/010-acs-2020'), # c82db89
    Model(State.WY, House.statehouse,   60,  True, VERSIONS, 'data/WY/010-acs-2020'), # c82db89
    Model(State.WY, House.localplan,  None,  True, VERSIONS, 'data/WY/010-acs-2020'), # c82db89
    ]
