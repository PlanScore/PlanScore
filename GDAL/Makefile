gdal-2.1.3-geos-3.6.1-numpy-1.19.2-python-3.9.6.tar.gz: Dockerfile
	docker run --rm --entrypoint cat $$(docker build -q .) /tmp/task.tar | gzip --stdout > $@

clean:
	rm -f gdal-2.1.3-geos-3.6.1-numpy-1.19.2-python-3.9.6.tar.gz
