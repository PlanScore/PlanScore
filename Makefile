all: planscore/website/build

live-lambda: planscore-lambda.zip
	aws s3api put-object --bucket planscore \
		--key "code/lambda-`shasum -p planscore-lambda.zip | cut -f1 -d' '`.zip" \
		--body planscore-lambda.zip --acl public-read

	env WEBSITE_BASE='https://planscore.org/' \
		API_BASE='https://api.planscore.org/' \
		parallel -j9 --delay 1 ./deploy.py planscore-lambda.zip \
		PlanScore planscore \
		"code/lambda-`shasum -p planscore-lambda.zip | cut -f1 -d' '`.zip" \
		::: PlanScore-UploadFields PlanScore-Callback PlanScore-AfterUpload \
		    PlanScore-UploadFieldsNew PlanScore-Preread PlanScore-PrereadFollowup \
		    PlanScore-PostreadCallback PlanScore-PostreadCalculate \
		    PlanScore-RunTile PlanScore-ObserveTiles \
		    PlanScore-APIUpload PlanScore-Authorizer

	aws s3api delete-object --bucket planscore \
		--key "code/lambda-`shasum -p planscore-lambda.zip | cut -f1 -d' '`.zip"
	
	./deploy-apigateway.py PlanScore

live-website: planscore/website/build
	# Two-part sync with deletion after to maintain consistency for web visitors
	aws s3 sync --acl public-read --cache-control 'public, max-age=300' $</ s3://planscore.org-website/
	aws s3 sync --acl public-read --cache-control 'public, max-age=300' --delete $</ s3://planscore.org-website/

dev-lambda: planscore-lambda.zip
	cdk deploy \
		--context stack_id=cf-development \
		--require-approval never \
		--outputs-file cdk-outputs.json

dev-website: website-dev-build
	aws s3 sync --acl public-read --cache-control 'no-store, max-age=0' --delete $</ s3://planscore.org-dev-website/

# Just one Lambda codebase is created, with different entry points and environments.
planscore-lambda.zip: gdal-geos-numpy-python.tar.gz
	mkdir -p planscore-lambda
	pip install -q -t planscore-lambda .
	tar -C planscore-lambda -xzf gdal-geos-numpy-python.tar.gz
	cp lambda.py planscore-lambda/lambda.py
	cd planscore-lambda && zip -rq ../planscore-lambda.zip .

gdal-geos-numpy-python.tar.gz:
	curl https://planscore.s3.amazonaws.com/code/gdal-2.1.3-geos-3.6.1-numpy-1.19.2-python-3.6.1.tar.gz -o $@ -s

planscore/website/build:
	env API_BASE='https://api.planscore.org/' \
		python -c 'import planscore.website as pw, flask_frozen as ff; ff.Freezer(pw.app).freeze()'

website-dev-build:
	env API_BASE='https://api.dev.planscore.org/' \
		FREEZER_DESTINATION="`pwd`/$@" \
		S3_BUCKET='planscore--dev' \
		python -c 'import planscore.website as pw, flask_frozen as ff; ff.Freezer(pw.app).freeze()'

# It's a pain to have to redownload gdal-geos-numpy-python.tar.gz so this sort-of cleans things
cleanish:
	rm -rf planscore/website/build
	rm -rf website-dev-build
	rm -rf planscore-lambda planscore-lambda.zip

clean: cleanish
	rm -f gdal-geos-numpy-python.tar.gz

.PHONY: clean cleanish all live-lambda live-website
