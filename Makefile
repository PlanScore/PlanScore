all: planscore/website/build

live-lambda: planscore-lambda.zip
	parallel \
		aws --region us-east-1 lambda update-function-code --function-name '{1}' \
		--zip-file fileb://planscore-lambda.zip \
		:::  PlanScore-UploadFields PlanScore-AfterUpload PlanScore-RunDistrict PlanScore-ScoreDistrictPlan \
		>> /dev/null
	aws --region us-east-1 lambda update-function-configuration --dead-letter-config TargetArn=$(AWS_LAMBDA_DLQ_ARN) \
	    --function-name PlanScore-UploadFields --handler lambda.upload_fields --timeout 3 >> /dev/null
	aws --region us-east-1 lambda update-function-configuration --dead-letter-config TargetArn=$(AWS_LAMBDA_DLQ_ARN) \
	    --function-name PlanScore-AfterUpload --handler lambda.after_upload --timeout 30 >> /dev/null
	aws --region us-east-1 lambda update-function-configuration --dead-letter-config TargetArn=$(AWS_LAMBDA_DLQ_ARN) \
	    --function-name PlanScore-RunDistrict --handler lambda.run_district --timeout 300 >> /dev/null
	aws --region us-east-1 lambda update-function-configuration --dead-letter-config TargetArn=$(AWS_LAMBDA_DLQ_ARN) \
	    --function-name PlanScore-ScoreDistrictPlan --handler lambda.score_plan --timeout 30 >> /dev/null

live-website: planscore/website/build
	aws s3 sync --acl public-read --cache-control 'public, max-age=300' --delete $</ s3://planscore-website/

# Just one Lambda codebase is created, with different entry points and environments.
planscore-lambda.zip:
	mkdir -p planscore-lambda
	pip install -q -t planscore-lambda .
	curl https://planscore.s3.amazonaws.com/code/gdal-2.1.3-geos-3.6.1-python-3.6.1.tar.gz -s | tar -C planscore-lambda -xzf -
	cp lambda.py planscore-lambda/lambda.py
	cd planscore-lambda && zip -rq ../planscore-lambda.zip .

planscore/website/build:
	python -c 'import planscore.website as pw, flask_frozen as ff; ff.Freezer(pw.app).freeze()'

clean:
	rm -rf planscore/website/build
	rm -rf planscore-lambda planscore-lambda.zip

.PHONY: clean all live-lambda live-website
