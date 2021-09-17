gdal-3.2.1-geos-3.9.0-numpy-1.19.2-python-3.9.6.tar.gz: Dockerfile
	docker run --rm --entrypoint cat $$(docker build -q .) /tmp/task.tar | gzip --stdout > $@

clean:
	rm -f gdal-3.2.1-geos-3.9.0-numpy-1.19.2-python-3.9.6.tar.gz
