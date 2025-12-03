all:

live-deploy: planscore-lambda.zip
	./cdk-deploy.sh cf-canary
	./cdk-deploy.sh cf-production

dev-deploy: planscore-lambda.zip
	./cdk-deploy.sh cf-development

# Just one Lambda codebase is created, with different entry points and environments.
planscore-lambda.zip:
	mkdir -p planscore-lambda
	pip3 install -q -t planscore-lambda .
	cp lambda.py planscore-lambda/lambda.py
	rm -r planscore-lambda/planscore/tests
	rm planscore-lambda/planscore/model/*.gz
	cd planscore-lambda && zip -rq ../planscore-lambda.zip .

planscore/website/static/supported-states.svg: design/Upload-Map.svg planscore-svg
	docker run --rm -it -v `pwd`:/vol -w /vol planscore-svg:latest

planscore-svg:
	cd SVG && docker build -t planscore-svg:latest .

clean:
	rm -rf planscore-lambda planscore-lambda.zip

.PHONY: clean all live-deploy dev-deploy planscore-svg
.SECONDARY:
