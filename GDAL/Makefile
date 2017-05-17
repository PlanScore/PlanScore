task.zip: Dockerfile
	docker run --rm --entrypoint cat $$(docker build -q .) /tmp/task.zip > $@
	zip -r $@ task.py

clean:
	rm -f task.zip
