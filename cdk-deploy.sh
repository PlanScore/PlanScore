#!/bin/sh -ex

PREFIX=$1
DIR=`pwd`
FILE=`mktemp -t output.XXXXXX`

cd $DIR/cdk-scoring

cdk deploy \
    --context formation_prefix=$PREFIX \
    --outputs-file $FILE \
    --require-approval never

cd $DIR/cdk-content

cdk deploy \
    --context formation_prefix=$PREFIX \
    --context prior_output=$FILE \
    --require-approval never

cat $FILE
