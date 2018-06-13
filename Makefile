build:
	  docker build . -t rabid/nzsl-dictionary-scripts
		git clone git://github.com/rabid/nzsl-dictionary-ios.git
		git clone git://github.com/rabid/nzsl-dictionary-android.git
update_assets:
	docker run --rm -it -v $(shell pwd)/nzsl-dictionary-android:/usr/src/android-app -v $(shell pwd)/nzsl-dictionary-ios:/usr/src/ios-app -v $(shell pwd):/usr/src/app rabid/nzsl-dictionary-scripts -i /usr/src/ios-app -a /usr/src/android-app
	 
