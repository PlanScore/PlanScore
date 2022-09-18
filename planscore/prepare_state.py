import argparse
import boto3
from . import constants

BLOCKS_KEY_FORMAT = 'data/{directory}/blocks/assembled-state.parquet'

parser = argparse.ArgumentParser(description='YESS')

parser.add_argument('filename', help='Name of geographic file with precinct data')
parser.add_argument('directory', default='XX/000',
    help='Model directory infix. Default {}.'.format('XX/000'))
parser.add_argument('--geojson',
    help='Path to GeoJSON file for tile summary')
parser.add_argument('--s3', action='store_true',
    help='Upload to S3 instead of local directory')

def main():
    args = parser.parse_args()
    s3 = boto3.client('s3') if args.s3 else None
    
    assert args.filename.endswith(".parquet")
    
    if args.s3 and s3:
        key = BLOCKS_KEY_FORMAT.format(directory=args.directory)
        print('-->', 'Write', f's3://{constants.S3_BUCKET}/{key}')
        with open(args.filename, "rb") as file:
            s3.put_object(
                Bucket=constants.S3_BUCKET,
                Key=key,
                Body=file,
                ContentType='application/octet-stream',
                ACL='public-read',
            )
