import time
import csv
import sys

import boto3

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

def main():
    ath = boto3.client('athena')

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
    
    out = csv.writer(sys.stdout, dialect='excel-tab')
    
    for row in result['ResultSet']['Rows']:
        out.writerow([d.get('VarCharValue') for d in row['Data']])

def lambda_handler(event, context):
    return main()

if __name__ == '__main__':
    exit(main(1))
