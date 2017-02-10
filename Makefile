default: repackage

clean:
	rm -rf dist/*
	rm -rf build/*

package:
	python setup.py sdist bdist_wheel

repackage: clean package

install:
	sh -c "sudo pip install dist/chopro-`cat VERSION`.tar.gz"

upload:
	sh -c "twine upload dist/chopro-`cat VERSION`-py2.py3-none-any.whl"
