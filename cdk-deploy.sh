#!/bin/sh -ex

PREFIX=$1
OPTION=$2
DIR=`pwd`
FILE=`mktemp -t output.XXXXXX`

cd $DIR/cdk-scoring

cdk deploy \
    $OPTION \
    --context formation_prefix=$PREFIX \
    --outputs-file $FILE \
    --require-approval never

cd $DIR/cdk-content

cdk deploy \
    $OPTION \
    --context formation_prefix=$PREFIX \
    --context prior_output=$FILE \
    --require-approval never

cat $FILE

# Test that /states works

export BASE=`python -m json.tool $FILE | grep APIBase | (IFS='"' read -r _ _ _ U _; echo $U)`
curl --fail "${BASE}states"  -s | head -n 25
