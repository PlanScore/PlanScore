all:

live-deploy:
	./cdk-deploy.sh cf-canary
	./cdk-deploy.sh cf-production

dev-deploy:
	./cdk-deploy.sh cf-development

live-metrics: metrics-lambda.zip
	aws lambda update-function-code --region us-east-1 \
		--function-name PlanScore-Update-Metrics \
		--zip-file fileb://metrics-lambda.zip
	sleep 10
	aws lambda update-function-configuration --region us-east-1 \
		--function-name PlanScore-Update-Metrics \
		--handler planscore.update_metrics.lambda_handler \
		--timeout 300

metrics-lambda.zip:
	mkdir -p metrics-lambda
	pip3 install -q -t metrics-lambda '.[metrics]'
	cd metrics-lambda && zip -rq ../metrics-lambda.zip .

planscore/website/static/supported-states.svg: design/Upload-Map.svg planscore-svg
	docker run --rm -it -v `pwd`:/vol -w /vol planscore-svg:latest

planscore-svg:
	cd SVG && docker build -t planscore-svg:latest .

clean:
	rm -rf metrics-lambda metrics-lambda.zip

.PHONY: clean all live-deploy dev-deploy planscore-svg
.SECONDARY:
