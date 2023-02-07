
cd /home/runner/work/
pip install -r requirements.txt
pip install -r dev-requirements.txt
pip install -e .
pytest ckanext/resource_type_validation/test_mime_type_validation.py

