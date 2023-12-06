build:
	  docker build . -t odnzsl/nzsl-dictionary-scripts
update_freelex_assets:
	docker run --rm -v $(shell pwd):/usr/src/app odnzsl/nzsl-dictionary-scripts build-assets-from-freelex.py
update_signbank_assets:
	docker run -e SIGNBANK_HOST -e SIGNBANK_USERNAME -e SIGNBANK_PASSWORD --rm -v $(shell pwd):/usr/src/app odnzsl/nzsl-dictionary-scripts build-assets-from-signbank.py
update_signbank_database:
	docker run -e SIGNBANK_HOST -e SIGNBANK_USERNAME -e SIGNBANK_PASSWORD --rm -v $(shell pwd):/usr/src/app odnzsl/nzsl-dictionary-scripts build-assets-from-signbank.py --skip-assets

