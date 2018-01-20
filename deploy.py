#!/usr/bin/env python
import sys, argparse, boto3, os, copy, time
import botocore.exceptions

common = dict(
    Runtime='python3.6', Environment=dict(Variables={})
    )

if 'AWS_LAMBDA_DLQ_ARN' in os.environ:
    common.update(DeadLetterConfig=dict(TargetArn=os.environ['AWS_LAMBDA_DLQ_ARN']))

functions = {
    'PlanScore-UploadFields': dict(Handler='lambda.upload_fields', Timeout=3, **common),
    'PlanScore-Callback': dict(Handler='lambda.callback', Timeout=3, **common),
    'PlanScore-AfterUpload': dict(Handler='lambda.after_upload', Timeout=300, MemorySize=512, **common),
    'PlanScore-RunDistrict': dict(Handler='lambda.run_district', Timeout=300, MemorySize=512, **common),
    'PlanScore-ScoreDistrictPlan': dict(Handler='lambda.score_plan', Timeout=300, **common),
    }

def publish_function(lam, name, path, env, role):
    ''' Create or update the named function to Lambda.
    '''
    start_time = time.time()
    function_kwargs = copy.deepcopy(functions[name])
    function_kwargs['Environment']['Variables'].update(env)
    
    if role is not None:
        function_kwargs.update(Role=role)

    with open(path, 'rb') as code_file:
        code_bytes = code_file.read()

    try:
        print('    * get function', name, file=sys.stderr)
        lam.get_function(FunctionName=name)
    except botocore.exceptions.ClientError:
        # Function does not exist, create it
        print('    * create function', name, file=sys.stderr)
        lam.create_function(FunctionName=name, Code=dict(ZipFile=code_bytes), **function_kwargs)
    else:
        # Function exists, update it
        print('    * update function code', name, file=sys.stderr)
        lam.update_function_code(FunctionName=name, ZipFile=code_bytes)
        print('    * update function configuration', name, file=sys.stderr)
        lam.update_function_configuration(FunctionName=name, **function_kwargs)
    
    print('      done in {:.1f} seconds'.format(time.time() - start_time), file=sys.stderr)

parser = argparse.ArgumentParser(description='Update Lambda function.')
parser.add_argument('path', help='Function code path')
parser.add_argument('name', help='Function name')

if __name__ == '__main__':
    args = parser.parse_args()
    env = {k: os.environ[k] for k in ('PLANSCORE_SECRET', 'WEBSITE_BASE', 'AWS')
        if k in os.environ}
    
    lam = boto3.client('lambda', region_name='us-east-1')
    publish_function(lam, args.name, args.path, env, os.environ.get('AWS_IAM_ROLE'))
