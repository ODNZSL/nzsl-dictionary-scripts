build:
	  docker build . -t odnzsl/nzsl-dictionary-scripts
update_assets:
	docker run --rm -v $(shell pwd):/usr/src/app odnzsl/nzsl-dictionary-scripts 
	 
