import subprocess

# TODO: Add run tests

# Scripts to make requirements files
make_requirements = "poetry export --without-hashes -f requirements.txt --output requirements.txt"
make_requirements_docs = "poetry export --without-hashes --with docs -f requirements.txt --output docs/requirements.txt"
# Run the scripts
subprocess.run(make_requirements, shell=True)
subprocess.run(make_requirements_docs, shell=True)