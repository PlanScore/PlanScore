all: planscore/website/build

live-lambda: planscore-lambda.zip
	env AWS=amazonaws.com WEBSITE_BASE=https://planscore.org/ \
		parallel -j9 ./deploy.py planscore-lambda.zip \
		:::  PlanScore-UploadFields PlanScore-Callback PlanScore-AfterUpload PlanScore-RunDistrict PlanScore-ScoreDistrictPlan

live-website: planscore/website/build
	# Two-part sync with deletion after to maintain consistency for web visitors
	aws s3 sync --acl public-read --cache-control 'public, max-age=300' $</ s3://planscore-website/
	aws s3 sync --acl public-read --cache-control 'public, max-age=300' --delete $</ s3://planscore-website/

localstack-env: planscore-lambda.zip
	./setup-localstack.py planscore-lambda.zip

# Just one Lambda codebase is created, with different entry points and environments.
planscore-lambda.zip: gdal-geos-python.tar.gz
	mkdir -p planscore-lambda
	pip install -q -t planscore-lambda .
	tar -C planscore-lambda -xzf gdal-geos-python.tar.gz
	cp lambda.py planscore-lambda/lambda.py
	cd planscore-lambda && zip -rq ../planscore-lambda.zip .

gdal-geos-python.tar.gz:
	curl https://planscore.s3.amazonaws.com/code/gdal-2.1.3-geos-3.6.1-python-3.6.1.tar.gz -o $@ -s

planscore/website/build:
	env AWS=amazonaws.com API_BASE=https://api.planscore.org/ \
		python -c 'import planscore.website as pw, flask_frozen as ff; ff.Freezer(pw.app).freeze()'

clean:
	rm -rf planscore/website/build
	rm -rf planscore-lambda planscore-lambda.zip
	rm -f gdal-geos-python.tar.gz

.PHONY: clean all live-lambda live-website localstack-env
