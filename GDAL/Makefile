gdal-2.1.3-python-3.6.1.tar.gz: Dockerfile
	docker run --rm --entrypoint cat $$(docker build -q .) /tmp/task.tar | gzip --stdout > $@

clean:
	rm -f gdal-2.1.3-python-3.6.1.tar.gz
