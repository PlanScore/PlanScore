all:

live-deploy: planscore-lambda.zip
	./cdk-deploy.sh cf-production

dev-deploy: planscore-lambda.zip
	./cdk-deploy.sh cf-development

# Just one Lambda codebase is created, with different entry points and environments.
planscore-lambda.zip: gdal-geos-numpy-python.tar.gz
	mkdir -p planscore-lambda
	pip3 install -q -t planscore-lambda .
	tar -C planscore-lambda -xzf gdal-geos-numpy-python.tar.gz
	cp lambda.py planscore-lambda/lambda.py
	cd planscore-lambda && zip -rq ../planscore-lambda.zip .

gdal-geos-numpy-python.tar.gz:
	curl https://planscore.s3.amazonaws.com/code/gdal-2.1.3-geos-3.6.1-numpy-1.19.2-python-3.6.1.tar.gz -o $@ -s

# It's a pain to have to redownload gdal-geos-numpy-python.tar.gz so this sort-of cleans things
cleanish:
	rm -rf planscore-lambda planscore-lambda.zip

clean: cleanish
	rm -f gdal-geos-numpy-python.tar.gz

.PHONY: clean cleanish all live-deploy dev-deploy
.SECONDARY:
