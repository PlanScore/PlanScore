all: planscore-uploadfields.zip

live-lambda: all
	aws --region us-east-1 lambda update-function-code --function-name PlanScore-UploadFields --zip-file fileb://planscore-uploadfields.zip >> /dev/null
	aws --region us-east-1 lambda update-function-configuration --function-name PlanScore-UploadFields --handler planscore.upload_fields.lambda_handler >> /dev/null

live-website:
	mkdir -p build
	ln -f *.html build/
	aws s3 sync --acl public-read --cache-control 'public, max-age=300' --delete build/ s3://planscore-website/

planscore-uploadfields.zip:
	mkdir -p planscore-uploadfields
	pip install -q -t planscore-uploadfields .
	cd planscore-uploadfields && zip -rq ../planscore-uploadfields.zip .

clean:
	rm -rf planscore-uploadfields planscore-uploadfields.zip

.PHONY: clean all live-lambda live-website
