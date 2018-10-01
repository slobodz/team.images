#upgrade
python -m pip install --user --upgrade setuptools wheel

# build
python setup.py sdist bdist_wheel

#install 

pip install C:\Project\team.images\dist\team.images-0.0.2-py3-none-any.whl
python setup.py install
pip install --extra-index-url https://teampypi.herokuapp.com/ team.images
