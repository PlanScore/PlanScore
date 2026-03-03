import os
import json
import csv
import io
import time
import enum
import datetime
import collections
from . import constants

UPLOAD_DIRECTORY = 'uploads/{id}/'
UPLOAD_PREFIX = 'uploads/{id}/upload/'
UPLOAD_INDEX_KEY = 'uploads/{id}/index.json'
UPLOAD_SCENARIOS_KEY = 'uploads/{id}/scenarios.json'
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

        # Hard-coded years to accept pvote from
        'pvotes',

        # A hard-coded year to make predictions for
        'year',

        # The presidential vote in the model is mean-deviated, so you have to
        # subtract this adjustment value from the presidential vote values in
        # each district. Values are given as Democratic vote portion from 0. to
        # 1. and become approximately -0.5 to +0.5.
        'vote_adjust_congress',
        'vote_adjust_statelege',

        # Include as option on annotation page?
        'is_public',
        
        # Important: cross-reference this tuple with window.version_parameters in annotate-new.js
    ),
)

# Dict order is significant, default is first
VERSION_PARAMETERS = {
    '2019Z': VersionParameters(
        'Old: rerun the 2016 election, originally published 2020 (sha:43fde227)',
        '-2019Z', [2016], 2016, -0.496875, -0.496875, True,
    ),
    '2022F': VersionParameters(
        'Old: rerun the 2020 election, originally published 2022 (sha:bc75da6e)',
        '-2022F', [2020], 2020, -0.5208897, -0.492732, True,
    ),
    '2025B': VersionParameters(
        'New: rerun the 2024 election with more accurate updated data (updated August 2025)',
        '-2025B', [2024], 2024, -0.515, -0.495, True,
    ),
    '2025A': VersionParameters(
        'New: rerun the 2020 election with more accurate updated data (updated August 2025)',
        '-2025A', [2020], 2024, -0.523, -0.495, True,
    ),
}

PRESIDENTIAL_YEARS = (2016, 2020, 2024)
US_SENATE_YEARS = (2016, 2018, 2020, 2022, 2024)

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
    Undefined = 'U' # Internal special value for all-open plans

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

    def __init__(self, id, key, model:Model=None, districts=None, scenarios=None,
            incumbents=None, vote_swings=None, summary=None, progress=None,
            start_time=None, message=None, description=None, geometry_key=None,
            status=None, library_metadata=None, auth_token=None, model_version=None,
            pvote_year=None, model_year=None, execution_id=None, execution_token=None,
            **ignored):
        self.id = id
        self.key = key
        self.model = model
        self.status = status
        self.districts = districts or []
        # Preserve explicit None for scenarios when not generated (e.g., due to pre-applied swings)
        self.scenarios = scenarios
        self.incumbents = incumbents or []
        self.vote_swings = vote_swings or []
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
        self.pvote_year = pvote_year
        self.model_year = model_year
        self.execution_id = execution_id
        self.execution_token = execution_token

        if not incumbents:
            self.incumbents = [Incumbency.Open.value for i in range(len(self.districts))]

        if not vote_swings:
            self.vote_swings = [0.0 for i in range(len(self.districts))]
    
    def is_overdue(self):
        return bool(time.time() > (self.start_time + constants.UPLOAD_TIME_LIMIT))
    
    def index_key(self):
        return UPLOAD_INDEX_KEY.format(id=self.id)
    
    def scenarios_key(self):
        return UPLOAD_SCENARIOS_KEY.format(id=self.id)

    def plaintext_key(self):
        return UPLOAD_PLAINTEXT_KEY.format(id=self.id)
    
    def district_key(self, index):
        return UPLOAD_DISTRICTS_KEY.format(id=self.id, index=index)
    
    def logentry_key(self, guid):
        ds = datetime.date.fromtimestamp(self.start_time).strftime('%Y-%m-%d')
        return UPLOAD_LOGENTRY_KEY.format(ds=ds, guid=guid)
    
    def obscured_token(self):
        '''An obscured version of the token safe for logs, etc.
        '''
        if not self.auth_token:
            return None

        if self.auth_token.endswith('********'):
            # Already obscured, bravo
            return self.auth_token

        return self.auth_token[:len(self.auth_token)//2] + '********'

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
                ['District', 'Source District'] + extra_columns + column_names, dialect='excel-tab')
            rows.writeheader()
            for (index, district) in enumerate(self.districts):
                totals, compactness = district['totals'], district['compactness']
                extra_values = {'Candidate Scenario': self.incumbents[index]} if has_incumbency else {}
                rows.writerow(dict(
                    District = district.get('number', index+1),
                    **{'Source District': district.get('source_district') or ''},
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
            scenarios = self.scenarios,
            incumbents = self.incumbents,
            vote_swings = self.vote_swings,
            summary = self.summary,
            progress = progress,
            start_time = self.start_time,
            message = self.message,
            description = self.description,
            geometry_key = self.geometry_key,
            commit_sha = self.commit_sha,
            library_metadata = self.library_metadata,
            auth_token = self.obscured_token(),
            model_version = self.model_version,
            pvote_year = self.pvote_year,
            model_year = self.model_year,
            execution_id = self.execution_id,
            execution_token = self.execution_token,
            )
    
    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)
    
    def to_logentry(self):
        ''' Export current plan information to a tab-delimited plaintext file
        '''
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
            self.obscured_token(),
            
            # User-selected model version
            self.model_version,

            # State machine execution
            self.execution_id,
        ]
        
        try:
            out = io.StringIO()
            rows = csv.writer(out, dialect='excel-tab', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            rows.writerow(logentry)
        
        except Exception as e:
            return f'Error: {e}\n'

        else:
            return out.getvalue()
    
    def clone(self, model=None, districts=None, scenarios=None, incumbents=None, vote_swings=None, summary=None,
        progress=None, start_time=None, message=None, description=None, geometry_key=None, status=None,
        library_metadata=None, auth_token=None, model_version=None, pvote_year=None, model_year=None, execution_id=None, execution_token=None):
        return Upload(self.id, self.key,
            model = model or self.model,
            status = status if (self.status is None) else self.status,
            districts = districts or self.districts,
            scenarios = scenarios or self.scenarios,
            incumbents = incumbents or self.incumbents,
            vote_swings = vote_swings or self.vote_swings,
            summary = summary or self.summary,
            progress = progress if (progress is not None) else self.progress,
            start_time = start_time or self.start_time,
            message = message or self.message,
            description = description or self.description,
            geometry_key = geometry_key or self.geometry_key,
            library_metadata = library_metadata or self.library_metadata,
            auth_token = auth_token or self.obscured_token(),
            model_version = model_version or self.model_version,
            pvote_year = pvote_year or self.pvote_year,
            model_year = model_year or self.model_year,
            execution_id = execution_id or self.execution_id,
            execution_token = execution_token or self.execution_token,
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
            scenarios = data.get('scenarios'),
            incumbents = data.get('incumbents'),
            vote_swings = data.get('vote_swings'),
            summary = data.get('summary'),
            progress = progress,
            start_time = data.get('start_time'),
            message = data.get('message'),
            description = data.get('description'),
            geometry_key = data.get('geometry_key'),
            library_metadata = data.get('library_metadata'),
            auth_token = data.get('auth_token'),
            model_version = data.get('model_version'),
            pvote_year = data.get('pvote_year'),
            model_year = data.get('model_year'),
            execution_id = data.get('execution_id'),
            execution_token = data.get('execution_token'),
            )
    
    @staticmethod
    def from_json(body):
        return Upload.from_dict(json.loads(body))

# Active version of each state model

VERSIONS_16_20_24A = ['2019Z', '2022F', '2025A']
VERSIONS_16_20_24B = ['2019Z', '2022F', '2025B']
VERSIONS_20_24A = ['2022F', '2025A']
VERSIONS_20_24B = ['2022F', '2025B']

MODELS = [
    Model(State.XX, House.statehouse,    2,  True, VERSIONS_16_20_24A, 'data/XX/007-pvote-2024'), # b8e19879 and more
    Model(State.AK, House.ushouse,       1,  True, VERSIONS_20_24B, 'data/AK/010-pvote-2024'), # 6bacc75
    Model(State.AK, House.statesenate,  20,  True, VERSIONS_20_24B, 'data/AK/009-pvote-2024'), # 6bacc75
    Model(State.AK, House.statehouse,   40,  True, VERSIONS_20_24B, 'data/AK/009-pvote-2024'), # 6bacc75
    Model(State.AK, House.localplan,  None,  True, VERSIONS_20_24A, 'data/AK/008-acs-2020'), # c82db89
    Model(State.AL, House.ushouse,       7,  True, VERSIONS_16_20_24B, 'data/AL/010-cvap-2023'), # d4b3c7d
    Model(State.AL, House.statesenate,  35,  True, VERSIONS_16_20_24B, 'data/AL/010-cvap-2023'), # d4b3c7d
    Model(State.AL, House.statehouse,  105,  True, VERSIONS_16_20_24B, 'data/AL/010-cvap-2023'), # d4b3c7d
    Model(State.AL, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/AL/008-acs-2020'), # c82db89
    Model(State.AR, House.ushouse,       4,  True, VERSIONS_16_20_24B, 'data/AR/010-cvap-2023'), # d4b3c7d
    Model(State.AR, House.statesenate,  35,  True, VERSIONS_16_20_24B, 'data/AR/010-cvap-2023'), # d4b3c7d
    Model(State.AR, House.statehouse,  100,  True, VERSIONS_16_20_24B, 'data/AR/010-cvap-2023'), # d4b3c7d
    Model(State.AR, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/AR/008-acs-2020'), # c82db89
    Model(State.AZ, House.ushouse,       9,  True, VERSIONS_16_20_24B, 'data/AZ/014-cvap-2023'), # d4b3c7d
    Model(State.AZ, House.statesenate,  30,  True, VERSIONS_16_20_24B, 'data/AZ/014-cvap-2023'), # d4b3c7d
    Model(State.AZ, House.statehouse,   60,  True, VERSIONS_16_20_24B, 'data/AZ/014-cvap-2023'), # d4b3c7d
    Model(State.AZ, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/AZ/012-acs-2020'), # c82db89
    Model(State.CA, House.ushouse,      52,  True, VERSIONS_16_20_24B, 'data/CA/011-pvote-2016'), # 5c24f37
    Model(State.CA, House.statesenate,  40,  True, VERSIONS_20_24B, 'data/CA/011-pvote-2016'), # 5c24f37
    Model(State.CA, House.statehouse,   80,  True, VERSIONS_20_24B, 'data/CA/011-pvote-2016'), # 5c24f37
    Model(State.CA, House.localplan,  None,  True, VERSIONS_20_24A, 'data/CA/008-acs-2020'), # c82db89
    Model(State.CO, House.ushouse,       8,  True, VERSIONS_16_20_24B, 'data/CO/015-cvap-2023'), # d4b3c7d
    Model(State.CO, House.statesenate,  35,  True, VERSIONS_16_20_24B, 'data/CO/015-cvap-2023'), # d4b3c7d
    Model(State.CO, House.statehouse,   65,  True, VERSIONS_16_20_24B, 'data/CO/015-cvap-2023'), # d4b3c7d
    Model(State.CO, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/CO/013-acs-2020'), # c82db89
    Model(State.CT, House.ushouse,       5,  True, VERSIONS_16_20_24B, 'data/CT/008-cvap-2020'), # d4b3c7d
    Model(State.CT, House.statesenate,  36,  True, VERSIONS_16_20_24B, 'data/CT/008-cvap-2020'), # d4b3c7d
    Model(State.CT, House.statehouse,  151,  True, VERSIONS_16_20_24B, 'data/CT/008-cvap-2020'), # d4b3c7d
    Model(State.CT, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/CT/006-acs-2020'), # c82db89
    Model(State.DE, House.ushouse,       1,  True, VERSIONS_16_20_24B, 'data/DE/012-cvap-2023'), # d4b3c7d
    Model(State.DE, House.statesenate,  21,  True, VERSIONS_16_20_24B, 'data/DE/012-cvap-2023'), # d4b3c7d
    Model(State.DE, House.statehouse,   41,  True, VERSIONS_16_20_24B, 'data/DE/012-cvap-2023'), # d4b3c7d
    Model(State.DE, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/DE/010-acs-2020'), # c82db89
    Model(State.FL, House.ushouse,      28,  True, VERSIONS_16_20_24B, 'data/FL/012-cvap-2023'), # d4b3c7d
    Model(State.FL, House.statesenate,  40,  True, VERSIONS_16_20_24B, 'data/FL/012-cvap-2023'), # d4b3c7d
    Model(State.FL, House.statehouse,  120,  True, VERSIONS_16_20_24B, 'data/FL/012-cvap-2023'), # d4b3c7d
    Model(State.FL, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/FL/010-acs-2020'), # c82db89
    Model(State.GA, House.ushouse,      14,  True, VERSIONS_16_20_24B, 'data/GA/014-cvap-2023'), # d4b3c7d
    Model(State.GA, House.statesenate,  56,  True, VERSIONS_16_20_24B, 'data/GA/014-cvap-2023'), # d4b3c7d
    Model(State.GA, House.statehouse,  180,  True, VERSIONS_16_20_24B, 'data/GA/014-cvap-2023'), # d4b3c7d
    Model(State.GA, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/GA/012-acs-2020'), # c82db89
    Model(State.HI, House.ushouse,       2,  True, VERSIONS_16_20_24B, 'data/HI/010-cvap-2023'), # d4b3c7d
    Model(State.HI, House.statesenate,  25,  True, VERSIONS_16_20_24B, 'data/HI/010-cvap-2023'), # d4b3c7d
    Model(State.HI, House.statehouse,   51,  True, VERSIONS_16_20_24B, 'data/HI/010-cvap-2023'), # d4b3c7d
    Model(State.HI, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/HI/008-acs-2020'), # c82db89
    Model(State.IA, House.ushouse,       4,  True, VERSIONS_16_20_24B, 'data/IA/010-cvap-2023'), # d4b3c7d
    Model(State.IA, House.statesenate,  50,  True, VERSIONS_16_20_24B, 'data/IA/010-cvap-2023'), # d4b3c7d
    Model(State.IA, House.statehouse,  100,  True, VERSIONS_16_20_24B, 'data/IA/010-cvap-2023'), # d4b3c7d
    Model(State.IA, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/IA/008-acs-2020'), # c82db89
    Model(State.ID, House.ushouse,       2,  True, VERSIONS_16_20_24B, 'data/ID/010-pvote-2024'), # 26cc51f
    Model(State.ID, House.statesenate,  35,  True, VERSIONS_16_20_24B, 'data/ID/010-pvote-2024'), # 26cc51f
    Model(State.ID, House.statehouse,   70,  True, VERSIONS_16_20_24B, 'data/ID/010-pvote-2024'), # 26cc51f
    Model(State.ID, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/ID/008-acs-2020'), # c82db89
    Model(State.IL, House.ushouse,      17,  True, VERSIONS_16_20_24B, 'data/IL/012-cvap-2023'), # d4b3c7d
    Model(State.IL, House.statesenate,  59,  True, VERSIONS_16_20_24B, 'data/IL/012-cvap-2023'), # d4b3c7d
    Model(State.IL, House.statehouse,  118,  True, VERSIONS_16_20_24B, 'data/IL/012-cvap-2023'), # d4b3c7d
    Model(State.IL, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/IL/010-acs-2020'), # c82db89
    Model(State.IN, House.ushouse,       9,  True, VERSIONS_16_20_24B, 'data/IN/011-cvap-2023'), # d4b3c7d
    Model(State.IN, House.statesenate,  50,  True, VERSIONS_16_20_24B, 'data/IN/011-cvap-2023'), # d4b3c7d
    Model(State.IN, House.statehouse,  100,  True, VERSIONS_16_20_24B, 'data/IN/011-cvap-2023'), # d4b3c7d
    Model(State.IN, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/IN/009-acs-2020'), # c82db89
    Model(State.KS, House.ushouse,       5,  True, VERSIONS_16_20_24B, 'data/KS/011-cvap-2023'), # d4b3c7d
    Model(State.KS, House.statesenate,  40,  True, VERSIONS_16_20_24B, 'data/KS/011-cvap-2023'), # d4b3c7d
    Model(State.KS, House.statehouse,  125,  True, VERSIONS_16_20_24B, 'data/KS/011-cvap-2023'), # d4b3c7d
    Model(State.KS, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/KS/009-acs-2020'), # c82db89
    Model(State.KY, House.ushouse,       6,  True, VERSIONS_16_20_24B, 'data/KY/009-cvap-2023'), # d4b3c7d
    Model(State.KY, House.statesenate,  38,  True, VERSIONS_16_20_24B, 'data/KY/009-cvap-2023'), # d4b3c7d
    Model(State.KY, House.statehouse,  100,  True, VERSIONS_16_20_24B, 'data/KY/009-cvap-2023'), # d4b3c7d
    Model(State.KY, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/KY/007-acs-2020'), # c82db89
    Model(State.LA, House.ushouse,       6,  True, VERSIONS_16_20_24B, 'data/LA/009-cvap-2023'), # d4b3c7d
    Model(State.LA, House.statesenate,  39,  True, VERSIONS_16_20_24B, 'data/LA/009-cvap-2023'), # d4b3c7d
    Model(State.LA, House.statehouse,  105,  True, VERSIONS_16_20_24B, 'data/LA/009-cvap-2023'), # d4b3c7d
    Model(State.LA, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/LA/007-acs-2020'), # c82db89
    Model(State.MA, House.ushouse,       9,  True, VERSIONS_16_20_24B, 'data/MA/012-cvap-2023'), # d4b3c7d
    Model(State.MA, House.statesenate,  40,  True, VERSIONS_16_20_24B, 'data/MA/012-cvap-2023'), # d4b3c7d
    Model(State.MA, House.statehouse,  160,  True, VERSIONS_16_20_24B, 'data/MA/012-cvap-2023'), # d4b3c7d
    Model(State.MA, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/MA/010-acs-2020'), # c82db89
    Model(State.MD, House.ushouse,       8,  True, VERSIONS_16_20_24B, 'data/MD/014-cvap-2023'), # d4b3c7d
    Model(State.MD, House.statesenate,  47,  True, VERSIONS_16_20_24B, 'data/MD/014-cvap-2023'), # d4b3c7d
    Model(State.MD, House.statehouse,   68,  True, VERSIONS_16_20_24B, 'data/MD/014-cvap-2023'), # d4b3c7d
    Model(State.MD, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/MD/012-acs-2020'), # c82db89
    Model(State.ME, House.ushouse,       2,  True, VERSIONS_16_20_24B, 'data/ME/013-cvap-2023'), # d4b3c7d
    Model(State.ME, House.statesenate,  35,  True, VERSIONS_16_20_24B, 'data/ME/013-cvap-2023'), # d4b3c7d
    Model(State.ME, House.statehouse,  151,  True, VERSIONS_16_20_24B, 'data/ME/013-cvap-2023'), # d4b3c7d
    Model(State.ME, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/ME/011-acs-2020'), # c82db89
    Model(State.MI, House.ushouse,      13,  True, VERSIONS_16_20_24B, 'data/MI/013-pvote-2024'), # 87112a0
    Model(State.MI, House.statesenate,  38,  True, VERSIONS_16_20_24B, 'data/MI/013-pvote-2024'), # 87112a0
    Model(State.MI, House.statehouse,  110,  True, VERSIONS_16_20_24B, 'data/MI/013-pvote-2024'), # 87112a0
    Model(State.MI, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/MI/011-acs-2020'), # c82db89
    Model(State.MN, House.ushouse,       8,  True, VERSIONS_16_20_24B, 'data/MN/012-cvap-2023'), # d4b3c7d
    Model(State.MN, House.statesenate,  67,  True, VERSIONS_16_20_24B, 'data/MN/012-cvap-2023'), # d4b3c7d
    Model(State.MN, House.statehouse,  134,  True, VERSIONS_16_20_24B, 'data/MN/012-cvap-2023'), # d4b3c7d
    Model(State.MN, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/MN/010-acs-2020'), # c82db89
    Model(State.MO, House.ushouse,       8,  True, VERSIONS_16_20_24B, 'data/MO/011-cvap-2023'), # d4b3c7d
    Model(State.MO, House.statesenate,  34,  True, VERSIONS_16_20_24B, 'data/MO/011-cvap-2023'), # d4b3c7d
    Model(State.MO, House.statehouse,  163,  True, VERSIONS_16_20_24B, 'data/MO/011-cvap-2023'), # d4b3c7d
    Model(State.MO, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/MO/009-acs-2020'), # c82db89
    Model(State.MS, House.ushouse,       4,  True, VERSIONS_16_20_24B, 'data/MS/006-cvap-2023'), # d4b3c7d
    Model(State.MS, House.statesenate,  52,  True, VERSIONS_16_20_24B, 'data/MS/006-cvap-2023'), # d4b3c7d
    Model(State.MS, House.statehouse,  122,  True, VERSIONS_16_20_24B, 'data/MS/006-cvap-2023'), # d4b3c7d
    Model(State.MS, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/MS/004-acs-2020'), # c82db89
    Model(State.MT, House.ushouse,       2,  True, VERSIONS_16_20_24B, 'data/MT/012-cvap-2023'), # d4b3c7d
    Model(State.MT, House.statesenate,  50,  True, VERSIONS_16_20_24B, 'data/MT/012-cvap-2023'), # d4b3c7d
    Model(State.MT, House.statehouse,  100,  True, VERSIONS_16_20_24B, 'data/MT/012-cvap-2023'), # d4b3c7d
    Model(State.MT, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/MT/010-acs-2020'), # c82db89
    Model(State.NC, House.ushouse,      14,  True, VERSIONS_16_20_24B, 'data/NC/024-cvap-2023'), # d4b3c7d
    Model(State.NC, House.statesenate,  50,  True, VERSIONS_16_20_24B, 'data/NC/024-cvap-2023'), # d4b3c7d
    Model(State.NC, House.statehouse,  120,  True, VERSIONS_16_20_24B, 'data/NC/024-cvap-2023'), # d4b3c7d
    Model(State.NC, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/NC/022-acs-2020'), # c82db89
    Model(State.ND, House.ushouse,       1,  True, VERSIONS_16_20_24B, 'data/ND/013-pvote-2024'), # 3581561
    Model(State.ND, House.statesenate,  47,  True, VERSIONS_16_20_24B, 'data/ND/013-pvote-2024'), # 3581561
    Model(State.ND, House.statehouse,   94,  True, VERSIONS_16_20_24B, 'data/ND/013-pvote-2024'), # 3581561
    Model(State.ND, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/ND/011-acs-2020'), # c82db89
    Model(State.NE, House.ushouse,       3,  True, VERSIONS_16_20_24B, 'data/NE/010-cvap-2023'), # d4b3c7d
    Model(State.NE, House.statesenate,  49,  True, VERSIONS_16_20_24B, 'data/NE/010-cvap-2023'), # d4b3c7d
    Model(State.NE, House.localplan,  None,  True, VERSIONS_16_20_24B, 'data/NE/010-cvap-2023'), # d4b3c7d
    Model(State.NH, House.ushouse,       2,  True, VERSIONS_16_20_24B, 'data/NH/012-cvap-2023'), # d4b3c7d
    Model(State.NH, House.statesenate,  24,  True, VERSIONS_16_20_24B, 'data/NH/012-cvap-2023'), # d4b3c7d
    Model(State.NH, House.statehouse,  400,  True, VERSIONS_16_20_24B, 'data/NH/012-cvap-2023'), # d4b3c7d
    Model(State.NH, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/NH/010-acs-2020'), # c82db89
    Model(State.NJ, House.ushouse,      12,  True, VERSIONS_16_20_24B, 'data/NJ/009-pvote-2024'), # ab04d3c
    Model(State.NJ, House.statesenate,  40,  True, VERSIONS_16_20_24B, 'data/NJ/009-pvote-2024'), # ab04d3c
    Model(State.NJ, House.statehouse,   80,  True, VERSIONS_16_20_24B, 'data/NJ/009-pvote-2024'), # ab04d3c
    Model(State.NJ, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/NJ/007-acs-2020'), # c82db89
    Model(State.NM, House.ushouse,       3,  True, VERSIONS_16_20_24B, 'data/NM/010-cvap-2023'), # d4b3c7d
    Model(State.NM, House.statesenate,  42,  True, VERSIONS_16_20_24B, 'data/NM/010-cvap-2023'), # d4b3c7d
    Model(State.NM, House.statehouse,   70,  True, VERSIONS_16_20_24B, 'data/NM/010-cvap-2023'), # d4b3c7d
    Model(State.NM, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/NM/008-acs-2020'), # c82db89
    Model(State.NV, House.ushouse,       4,  True, VERSIONS_16_20_24B, 'data/NV/010-cvap-2023'), # d4b3c7d
    Model(State.NV, House.statesenate,  21,  True, VERSIONS_16_20_24B, 'data/NV/010-cvap-2023'), # d4b3c7d
    Model(State.NV, House.statehouse,   42,  True, VERSIONS_16_20_24B, 'data/NV/010-cvap-2023'), # d4b3c7d
    Model(State.NV, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/NV/008-acs-2020'), # c82db89
    Model(State.NY, House.ushouse,      19,  True, VERSIONS_16_20_24B, 'data/NY/005-cvap-2023'), # d4b3c7d
    Model(State.NY, House.statesenate,  63,  True, VERSIONS_16_20_24B, 'data/NY/005-cvap-2023'), # d4b3c7d
    Model(State.NY, House.statehouse,  150,  True, VERSIONS_16_20_24B, 'data/NY/005-cvap-2023'), # d4b3c7d
    Model(State.NY, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/NY/003-acs-2020'), # c82db89
    Model(State.OH, House.ushouse,      15,  True, VERSIONS_16_20_24B, 'data/OH/011-cvap-2023'), # d4b3c7d
    Model(State.OH, House.statesenate,  33,  True, VERSIONS_16_20_24B, 'data/OH/011-cvap-2023'), # d4b3c7d
    Model(State.OH, House.statehouse,   99,  True, VERSIONS_16_20_24B, 'data/OH/011-cvap-2023'), # d4b3c7d
    Model(State.OH, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/OH/009-acs-2020'), # c82db89
    Model(State.OK, House.ushouse,       5,  True, VERSIONS_16_20_24B, 'data/OK/010-pvote-2024'), # 6bacc75
    Model(State.OK, House.statesenate,  48,  True, VERSIONS_16_20_24B, 'data/OK/009-pvote-2024'), # 6bacc75
    Model(State.OK, House.statehouse,  101,  True, VERSIONS_16_20_24B, 'data/OK/009-pvote-2024'), # 6bacc75
    Model(State.OK, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/OK/008-acs-2020'), # c82db89
    Model(State.OR, House.ushouse,       6,  True, VERSIONS_16_20_24B, 'data/OR/010-pvote-2024'), # dcd1742
    Model(State.OR, House.statesenate,  30,  True, VERSIONS_16_20_24B, 'data/OR/010-pvote-2024'), # dcd1742
    Model(State.OR, House.statehouse,   60,  True, VERSIONS_16_20_24B, 'data/OR/010-pvote-2024'), # dcd1742
    Model(State.OR, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/OR/008-acs-2020'), # c82db89
    Model(State.PA, House.ushouse,      17,  True, VERSIONS_16_20_24B, 'data/PA/021-cvap-2023'), # d4b3c7d
    Model(State.PA, House.statesenate,  50,  True, VERSIONS_16_20_24B, 'data/PA/021-cvap-2023'), # d4b3c7d
    Model(State.PA, House.statehouse,  203,  True, VERSIONS_16_20_24B, 'data/PA/021-cvap-2023'), # d4b3c7d
    Model(State.PA, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/PA/019-acs-2020'), # c82db89
    Model(State.RI, House.ushouse,       2,  True, VERSIONS_16_20_24B, 'data/RI/017-cvap-2023'), # d4b3c7d
    Model(State.RI, House.statesenate,  38,  True, VERSIONS_16_20_24B, 'data/RI/017-cvap-2023'), # d4b3c7d
    Model(State.RI, House.statehouse,   75,  True, VERSIONS_16_20_24B, 'data/RI/017-cvap-2023'), # d4b3c7d
    Model(State.RI, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/RI/015-acs-2020'), # c82db89
    Model(State.SC, House.ushouse,       7,  True, VERSIONS_16_20_24B, 'data/SC/010-cvap-2023'), # d4b3c7d
    Model(State.SC, House.statesenate,  46,  True, VERSIONS_16_20_24B, 'data/SC/010-cvap-2023'), # d4b3c7d
    Model(State.SC, House.statehouse,  124,  True, VERSIONS_16_20_24B, 'data/SC/010-cvap-2023'), # d4b3c7d
    Model(State.SC, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/SC/008-acs-2020'), # c82db89
    Model(State.SD, House.ushouse,       1,  True, VERSIONS_16_20_24B, 'data/SD/010-pvote-2024'), # 6bacc75
    Model(State.SD, House.statesenate,  35,  True, VERSIONS_16_20_24B, 'data/SD/009-pvote-2024'), # 6bacc75
    Model(State.SD, House.statehouse,   70,  True, VERSIONS_16_20_24B, 'data/SD/009-pvote-2024'), # 6bacc75
    Model(State.SD, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/SD/008-acs-2020'), # c82db89
    Model(State.TN, House.ushouse,       9,  True, VERSIONS_20_24B, 'data/TN/011-cvap-2023'), # d4b3c7d
    Model(State.TN, House.statesenate,  33,  True, VERSIONS_20_24B, 'data/TN/011-cvap-2023'), # d4b3c7d
    Model(State.TN, House.statehouse,   99,  True, VERSIONS_20_24B, 'data/TN/011-cvap-2023'), # d4b3c7d
    Model(State.TN, House.localplan,  None,  True, VERSIONS_20_24A, 'data/TN/009-acs-2020'), # c82db89
    Model(State.TX, House.ushouse,      38,  True, VERSIONS_16_20_24B, 'data/TX/012-cvap-2023'), # d4b3c7d
    Model(State.TX, House.statesenate,  31,  True, VERSIONS_16_20_24B, 'data/TX/012-cvap-2023'), # d4b3c7d
    Model(State.TX, House.statehouse,  150,  True, VERSIONS_16_20_24B, 'data/TX/012-cvap-2023'), # d4b3c7d
    Model(State.TX, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/TX/010-acs-2020'), # c82db89
    Model(State.UT, House.ushouse,       4,  True, VERSIONS_16_20_24B, 'data/UT/010-cvap-2023'), # d4b3c7d
    Model(State.UT, House.statesenate,  29,  True, VERSIONS_16_20_24B, 'data/UT/010-cvap-2023'), # d4b3c7d
    Model(State.UT, House.statehouse,   75,  True, VERSIONS_16_20_24B, 'data/UT/010-cvap-2023'), # d4b3c7d
    Model(State.UT, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/UT/008-acs-2020'), # c82db89
    Model(State.VA, House.ushouse,      11,  True, VERSIONS_16_20_24B, 'data/VA/012-cvap-2023'), # d4b3c7d
    Model(State.VA, House.statesenate,  40,  True, VERSIONS_16_20_24B, 'data/VA/012-cvap-2023'), # d4b3c7d
    Model(State.VA, House.statehouse,  100,  True, VERSIONS_16_20_24B, 'data/VA/012-cvap-2023'), # d4b3c7d
    Model(State.VA, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/VA/010-acs-2020'), # c82db89
    Model(State.VT, House.ushouse,       1,  True, VERSIONS_16_20_24B, 'data/VT/012-pvote-2024'), # 82923d3
    Model(State.VT, House.statesenate,  30,  True, VERSIONS_16_20_24B, 'data/VT/012-pvote-2024'), # 82923d3
    Model(State.VT, House.statehouse,  150,  True, VERSIONS_16_20_24B, 'data/VT/012-pvote-2024'), # 82923d3
    Model(State.VT, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/VT/010-acs-2020'), # c82db89
    Model(State.WA, House.ushouse,      10,  True, VERSIONS_16_20_24B, 'data/WA/011-cvap-2023'), # d4b3c7d
    Model(State.WA, House.statesenate,  49,  True, VERSIONS_16_20_24B, 'data/WA/011-cvap-2023'), # d4b3c7d
    Model(State.WA, House.statehouse,   98,  True, VERSIONS_16_20_24B, 'data/WA/011-cvap-2023'), # d4b3c7d
    Model(State.WA, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/WA/009-acs-2020'), # c82db89
    Model(State.WI, House.ushouse,       8,  True, VERSIONS_16_20_24B, 'data/WI/016-cvap-2023'), # d4b3c7d
    Model(State.WI, House.statesenate,  33,  True, VERSIONS_16_20_24B, 'data/WI/016-cvap-2023'), # d4b3c7d
    Model(State.WI, House.statehouse,   99,  True, VERSIONS_16_20_24B, 'data/WI/016-cvap-2023'), # d4b3c7d
    Model(State.WI, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/WI/014-acs-2020'), # c82db89
    Model(State.WV, House.ushouse,       3,  True, VERSIONS_16_20_24B, 'data/WV/006-cvap-2023'), # d4b3c7d
    Model(State.WV, House.statesenate,  34,  True, VERSIONS_16_20_24B, 'data/WV/006-cvap-2023'), # d4b3c7d
    Model(State.WV, House.statehouse,  100,  True, VERSIONS_16_20_24B, 'data/WV/006-cvap-2023'), # d4b3c7d
    Model(State.WV, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/WV/004-acs-2020'), # c82db89
    Model(State.WY, House.ushouse,       1,  True, VERSIONS_16_20_24B, 'data/WY/012-cvap-2023'), # d4b3c7d
    Model(State.WY, House.statesenate,  30,  True, VERSIONS_16_20_24B, 'data/WY/012-cvap-2023'), # d4b3c7d
    Model(State.WY, House.statehouse,   60,  True, VERSIONS_16_20_24B, 'data/WY/012-cvap-2023'), # d4b3c7d
    Model(State.WY, House.localplan,  None,  True, VERSIONS_16_20_24A, 'data/WY/010-acs-2020'), # c82db89
    ]
