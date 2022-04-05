#!/usr/bin/env python3
import time
import boto3
import flask
import time
from planscore import util, postread_calculate

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

    for (status, dict) in util.iter_athena_exec(athena, query):
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
                <td align="right">{row['status']}</td>
                <td align="right">{row['elapsed']:.2f}</td>
                <td align="right">{row['model_state']}</td>
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

    for (status, dict) in util.iter_athena_exec(athena, query):
        if 'ResultSet' in dict:
            rows = postread_calculate.resultset_to_district_totals(dict)
        else:
            print(status)
            time.sleep(1)
    
    return f'''<p>
            <a href="{flask.url_for('get_index')}">🏠</a>
            <a href="https://planscore.campaignlegal.org/plan.html?{id}">🗺</a>
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
        + '''</table>'''

if __name__ == '__main__':
    app.run(debug=True)