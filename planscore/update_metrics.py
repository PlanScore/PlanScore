import time
import csv
import sys
import json
import datetime

import boto3
import oauth2client.service_account
import apiclient.discovery

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

FIELDS = ','.join([
    "userEnteredValue",
    "userEnteredFormat.numberFormat.type",
    "userEnteredFormat.numberFormat.pattern",
    "userEnteredFormat.horizontalAlignment",
    "userEnteredFormat.textFormat.bold",
    ])

def make_service(cred_data):
    ''' Create a Google service account instance from credentials object.
    '''
    creds = oauth2client.service_account.ServiceAccountCredentials.from_json_keyfile_dict(cred_data, SCOPES)
    return apiclient.discovery.build('sheets', 'v4', credentials=creds)

def exec_and_wait(ath, query_string):
    query_id = ath.start_query_execution(QueryString=query_string)['QueryExecutionId']
    
    while True:
        execution = ath.get_query_execution(QueryExecutionId=query_id)
        state = execution['QueryExecution']['Status']['State']
        print(execution['QueryExecution']['Status'])
        
        if state in ('SUCCEEDED', 'FAILED'):
            break
    
        time.sleep(2)
    
    return state, ath.get_query_results(QueryExecutionId=query_id)

def update_metrics(cred_data, spreadsheet_id):
    ath = boto3.client('athena')
    
    service = make_service(cred_data)
    print(service)
    
    resp1 = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_id = resp1['sheets'][0]['properties']['sheetId']
    print(resp1)
    print(sheet_id)

    exec_and_wait(ath, '''
        CREATE EXTERNAL TABLE IF NOT EXISTS `prod_scoring_logs`
        (
          `id` string, 
          `time` double, 
          `elapsed` float, 
          `message` string, 
          `model_state` string, 
          `model_house` string, 
          `model_json` string, 
          `key` string
        )
        PARTITIONED BY ( 
          `ds` date)
        ROW FORMAT DELIMITED 
          FIELDS TERMINATED BY '\t' 
        STORED AS INPUTFORMAT 
          'org.apache.hadoop.mapred.TextInputFormat' 
        OUTPUTFORMAT 
          'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
        LOCATION
          's3://planscore/logs/scoring'
        TBLPROPERTIES (
          'has_encrypted_data'='false')
        '''
    )
    
    exec_and_wait(ath, 'MSCK REPAIR TABLE prod_scoring_logs')
    
    state, result = exec_and_wait(ath, '''
        WITH all_states AS (
            SELECT count(distinct id) AS plans,
                 model_state
            FROM prod_scoring_logs
            WHERE model_state IS NOT NULL
              AND model_state != ''
            GROUP BY  model_state
            ORDER BY  model_state
        ), last_7days AS (
            SELECT count(distinct id) AS plans,
                 model_state
            FROM prod_scoring_logs
            WHERE ds
                BETWEEN date_add('day', -7, now())
                    AND date_add('day', 0, now())
            GROUP BY  model_state
            ORDER BY  model_state
        ), last_30days AS (
            SELECT count(distinct id) AS plans,
                 model_state
            FROM prod_scoring_logs
            WHERE ds
                BETWEEN date_add('day', -30, now())
                    AND date_add('day', 0, now())
            GROUP BY  model_state
            ORDER BY  model_state
        ), prior_30days AS (
            SELECT count(distinct id) AS plans,
                 model_state
            FROM prod_scoring_logs
            WHERE ds
                BETWEEN date_add('day', -60, now())
                    AND date_add('day', -31, now())
            GROUP BY  model_state
            ORDER BY  model_state
        )
        SELECT all_states.model_state,
                 all_states.plans AS total,
                 prior_30days.plans AS prior_30days,
                 last_30days.plans AS last_30days,
                 coalesce(last_30days.plans,
                 0) - coalesce(prior_30days.plans,
                 0) AS change,
                 last_7days.plans AS last_7days
        FROM all_states
        LEFT JOIN last_7days
            ON last_7days.model_state = all_states.model_state
        LEFT JOIN last_30days
            ON last_30days.model_state = all_states.model_state
        LEFT JOIN prior_30days
            ON prior_30days.model_state = all_states.model_state
        ORDER BY  all_states.model_state
        '''
    )
    
    print(state)
    print(result)
    
    column_count = len(result['ResultSet']['ResultSetMetadata']['ColumnInfo'])
    row_count = len(result['ResultSet']['Rows'])
    
    body = {
        'requests': [
            # Date stamp
            {
                'updateCells': {
                    'rows':
                    [
                        {
                            'values': [
                                {
                                    "userEnteredValue": {
                                        # The whole number portion of the value (left of the decimal) counts the days since December 30th 1899
                                        # https://developers.google.com/sheets/api/reference/rest/v4/DateTimeRenderOption
                                        'numberValue': (datetime.date.today() - datetime.date(1899, 12, 30)).days
                                    },
                                    "userEnteredFormat": {
                                        'numberFormat': {
                                            'type': 'DATE',
                                            'pattern': 'ddd, mmm d yyyy',
                                        },
                                        'horizontalAlignment': 'LEFT',
                                        'textFormat': {'bold': True},
                                    },
                                }
                            ]
                        }
                    ],
                    "fields": FIELDS,
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": 1
                    }
                }
            },
            # Header
            {
                'updateCells': {
                    'rows':
                    [
                        {
                            'values': [
                                {
                                    "userEnteredValue": {
                                        'stringValue': datum.get('VarCharValue')
                                    },
                                    "userEnteredFormat": {
                                        'textFormat': {'bold': True},
                                    },
                                }
                                for datum in result['ResultSet']['Rows'][0]['Data']
                            ]
                        }
                    ],
                    "fields": FIELDS,
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 1,
                        "endColumnIndex": 1 + column_count
                    }
                }
            },
            # States
            {
                'updateCells': {
                    'rows':
                    [
                        {
                            'values': [
                                {
                                    "userEnteredValue": {
                                        'stringValue': row['Data'][0].get('VarCharValue')
                                    },
                                }
                            ]
                        }
                        for row
                        in result['ResultSet']['Rows'][1:]
                    ],
                    "fields": FIELDS,
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": row_count,
                        "startColumnIndex": 1,
                        "endColumnIndex": 2
                    }
                }
            },
            # Numbers
            {
                'updateCells': {
                    'rows':
                    [
                        {
                            'values': [
                                {
                                    "userEnteredValue": {
                                        'numberValue': int(datum.get('VarCharValue', 0))
                                    },
                                    "userEnteredFormat": {
                                        'numberFormat': {
                                            'type': 'NUMBER',
                                            'pattern': '###0',
                                        }
                                    },
                                }
                                for datum in row['Data'][1:]
                            ]
                        }
                        for row
                        in result['ResultSet']['Rows'][1:]
                    ],
                    "fields": FIELDS,
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": row_count,
                        "startColumnIndex": 2,
                        "endColumnIndex": 1 + column_count
                    }
                }
            },
        ]
    }
    
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    
    out = csv.writer(sys.stdout, dialect='excel-tab')
    
    for row in result['ResultSet']['Rows']:
        out.writerow([d.get('VarCharValue') for d in row['Data']])

def lambda_handler(event, context):
    return update_metrics(event['Google-Key'], event['Spreadsheet-ID'])

def main():
    event = json.load(sys.stdin)
    return update_metrics(event['Google-Key'], event['Spreadsheet-ID'])
