all: planscore-lambda.zip

live-lambda: all
	aws --region us-east-1 lambda update-function-code --function-name PlanScore-UploadFields --zip-file fileb://planscore-lambda.zip >> /dev/null
	aws --region us-east-1 lambda update-function-configuration --function-name PlanScore-UploadFields --handler lambda.upload_fields >> /dev/null
	aws --region us-east-1 lambda update-function-code --function-name PlanScore-AfterUpload --zip-file fileb://planscore-lambda.zip >> /dev/null
	aws --region us-east-1 lambda update-function-configuration --function-name PlanScore-AfterUpload --handler lambda.after_upload >> /dev/null

live-website:
	mkdir -p build
	ln -f *.html build/
	aws s3 sync --acl public-read --cache-control 'public, max-age=300' --delete build/ s3://planscore-website/

# Just one Lambda codebase is created, with different entry points and environments.
planscore-lambda.zip:
	mkdir -p planscore-lambda
	pip install -q -t planscore-lambda .
	curl https://planscore.s3.amazonaws.com/code/gdal-2.1.3-geos-3.6.1-python-3.6.1.tar.gz -s | tar -C planscore-lambda -xzf -
	cp lambda.py planscore-lambda/lambda.py
	cd planscore-lambda && zip -rq ../planscore-lambda.zip .

clean:
	rm -rf build
	rm -rf planscore-lambda planscore-lambda.zip

.PHONY: clean all live-lambda live-website
