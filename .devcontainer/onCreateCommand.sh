apt-get update
python -m pip install --upgrade pip
python -m pip install pylint flake8
pip install -e '.[llvm,testing,cuda,gpu,triton]'
pip install pre-commit

# pre-commit install