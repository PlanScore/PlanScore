all: planscore-uploadfields.zip planscore-afterupload.zip

live-lambda: all
	aws --region us-east-1 lambda update-function-code --function-name PlanScore-UploadFields --zip-file fileb://planscore-uploadfields.zip >> /dev/null
	aws --region us-east-1 lambda update-function-configuration --function-name PlanScore-UploadFields --handler lambda.upload_fields >> /dev/null
	aws --region us-east-1 lambda update-function-code --function-name PlanScore-AfterUpload --zip-file fileb://planscore-afterupload.zip >> /dev/null
	aws --region us-east-1 lambda update-function-configuration --function-name PlanScore-AfterUpload --handler lambda.after_upload >> /dev/null

live-website:
	mkdir -p build
	ln -f *.html build/
	aws s3 sync --acl public-read --cache-control 'public, max-age=300' --delete build/ s3://planscore-website/

# planscore-uploadfields.zip, planscore-afterupload.zip
# https://www.gnu.org/software/make/manual/html_node/Pattern-Examples.html
planscore-%.zip:
	mkdir -p planscore-$*
	pip install -q -t planscore-$* .
	curl https://planscore.s3.amazonaws.com/code/gdal-2.1.3-geos-3.6.1-python-3.6.1.tar.gz -s | tar -C planscore-$* -xzvf -
	cp lambda.py planscore-$*/lambda.py
	cd planscore-$* && zip -rq ../planscore-$*.zip .

clean:
	rm -rf build
	rm -rf planscore-uploadfields planscore-uploadfields.zip
	rm -rf planscore-afterupload planscore-afterupload.zip

.PHONY: clean all live-lambda live-website
