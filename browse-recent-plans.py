#!/usr/bin/env python3
import time
import boto3
import flask
import time
import datetime
import itertools
from planscore import util, postread_calculate


def iter_nearby_executions(athena, start_time):
    '''
    '''
    kwargs = dict(MaxResults=50)
    
    while True:
        print('athena.list_query_executions')
        executions = athena.list_query_executions(**kwargs)
        kwargs = dict(MaxResults=50, NextToken=executions['NextToken'])

        print('athena.batch_get_query_execution')
        executions = athena.batch_get_query_execution(
            QueryExecutionIds=executions['QueryExecutionIds'],
        )['QueryExecutions']
        
        newest_time = max([e['Status']['SubmissionDateTime'] for e in executions])
        oldest_time = min([e['Status']['SubmissionDateTime'] for e in executions])
        
        if newest_time < start_time:
            # Stop, we won't find this plan ID if we keep searching
            break
        elif start_time < oldest_time - datetime.timedelta(minutes=15):
            # Skip this batch, it's too new
            continue

        # Look at this whole batch, who knows
        for execution in executions:
            yield execution


def find_plan_query(athena, plan_id):
    '''
    '''
    start_time = datetime.datetime.strptime(f'{plan_id[:15]} +0000', '%Y%m%dT%H%M%S %z')
    
    for execution in iter_nearby_executions(athena, start_time):
        if plan_id in execution['Query'] and execution['Query'].startswith('-- cf_production_database'):
            return execution


app = flask.Flask(__name__)

@app.route('/')
def get_index():
    athena = boto3.client('athena')
    query = '''-- Prior day's production plan outcomes
WITH plans AS (
    SELECT id, ds, MAX(elapsed) AS elapsed
    FROM "default"."prod_scoring_logs"
    GROUP BY id, ds
),
successes AS (
    SELECT id, ds, status,
        MAX(elapsed) AS elapsed,
        MAX(model_state) AS model_state
    FROM "default"."prod_scoring_logs"
    WHERE status = 't'
    GROUP BY id, ds, status
),
failures AS (
    SELECT id, ds, status, message,
        MAX(elapsed) AS elapsed,
        MAX(model_state) AS model_state
    FROM "default"."prod_scoring_logs"
    WHERE status = 'f'
    GROUP BY id, ds, status, message
),
tokens AS (
    SELECT DISTINCT id, ds, token
    FROM "default"."prod_scoring_logs"
    WHERE token != ''
)

SELECT
    plans.ds, plans.id,
    CAST(COALESCE(successes.status, failures.status) AS boolean) AS status,
    COALESCE(successes.elapsed, failures.elapsed) AS elapsed,
    COALESCE(successes.model_state, failures.model_state) AS model_state,
    failures.message,
    tokens.token
FROM plans
LEFT JOIN successes
    ON successes.id = plans.id
    AND successes.ds = plans.ds
LEFT JOIN failures
    ON failures.id = plans.id
    AND failures.ds = plans.ds
LEFT JOIN tokens
    ON tokens.id = plans.id
    AND tokens.ds = plans.ds
WHERE plans.ds >= DATE_TRUNC('day', NOW() - INTERVAL '1' DAY)
ORDER BY status ASC, message ASC, id DESC
'''

    for (status, dict) in util.iter_athena_exec(athena, query, 'observe'):
        if 'ResultSet' in dict:
            rows = postread_calculate.resultset_to_district_totals(dict)
        else:
            print(status)
            time.sleep(1)
    
    return '''<table style='font-family: sans-serif; font-size: 12px'>''' \
        + '''<tr>
            <th>ds</th>
            <th>id</th>
            <th>status</th>
            <th>elapsed</th>
            <th>state</th>
            <th>token</th>
            <th>message</th>
        </tr>''' \
        + '\n'.join([
            f'''<tr>
                <td align="right" style="white-space: nowrap">{row['ds']}</td>
                <td align="right">
                    <a href="{flask.url_for('get_plan_log', ds=str(row['ds']), id=row['id'])}">{row['id']}</a></td>
                <td align="right">{row.get('status')}</td>
                <td align="right">{row.get('elapsed', -1):.2f}</td>
                <td align="right">{row.get('model_state')}</td>
                <td>{row.get('token', '')}</td>
                <td>{row.get('message', '')}</td>
            </tr>'''
            for row in rows
        ]) \
        + '''</table>'''

@app.route('/plan/<ds>/<id>')
def get_plan_log(ds, id):
    athena = boto3.client('athena')
    query = f'''-- One production plan log
SELECT
    time,
    CAST(if(status = '', null, status) AS boolean) AS status,
    elapsed,
    model_state,
    model_house,
    model_version,
    token,
    message
FROM "default"."prod_scoring_logs"
WHERE id = '{id}'
  AND ds = CAST('{ds}' AS date)
ORDER BY time ASC
'''

    athena_exec = util.iter_athena_exec(athena, query, 'observe')
    execution = find_plan_query(athena, id)
    
    for (status, dict) in athena_exec:
        if 'ResultSet' in dict:
            rows = postread_calculate.resultset_to_district_totals(dict)
            break
        else:
            print(status)
            time.sleep(1)
    
    return f'''<p>
            <a style="text-decoration: none" href="{flask.url_for('get_index')}">🏠</a>
            <a style="text-decoration: none" href="https://planscore.campaignlegal.org/plan.html?{id}">🗺</a>
            <a style="text-decoration: none" href="https://s3.console.aws.amazon.com/s3/buckets/planscore?region=us-east-1&prefix=uploads/{id}/upload/&showversions=false">📦</a>
            <a style="text-decoration: none" href="https://planscore.s3.amazonaws.com/uploads/{id}/index.json">📄</a>
        </p>''' \
        + '''<table style='font-family: sans-serif; font-size: 12px'>''' \
        + '''<tr>
            <th>time</th>
            <th>status</th>
            <th>elapsed</th>
            <th>state</th>
            <th>house</th>
            <th>version</th>
            <th>token</th>
            <th>message</th>
        </tr>''' \
        + '\n'.join([
            f'''<tr>
                <td align="right">{time.strftime('%a, %d %b %Y %H:%M:%S %Z', time.localtime(row['time']))}</td>
                <td align="right">{row.get('status', '')}</td>
                <td align="right">{row['elapsed']:.2f}</td>
                <td align="right">{row['model_state']}</td>
                <td align="right">{row['model_house']}</td>
                <td align="right">{row['model_version']}</td>
                <td>{row.get('token', '')}</td>
                <td>{row.get('message', '')}</td>
            </tr>'''
            for row in rows
        ]) \
        + '''</table>''' \
        + (
            f'''<dl style='font-family: sans-serif; font-size: 12px'>
                <dt>Execution time</dt>
                <dd>{execution['Statistics']['TotalExecutionTimeInMillis']/1000:.1f}sec</dd>
                <dt>Data scanned</dt>
                <dd>{execution['Statistics']['DataScannedInBytes']/1024/1024:,.1f}MB</dd>
            </dl>''' \
            + f'''<pre>{execution['Query']}</pre>'''
            if execution else ''
        )

if __name__ == '__main__':
    app.run(debug=True)