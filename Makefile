.PHONY: install train produce consume report test

install:
	pip install -r requirements.txt

train:
	python -m src.train

produce:
	python -m src.streaming.producer

consume:
	python -m src.streaming.consumer

report:
	streamlit run src/report/dashboard.py

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

HF_API_REPO=../cc-fraud-sentinel

deploy-api:
	cp src/api/main.py $(HF_API_REPO)/app/main.py
	cp src/api/schemas.py $(HF_API_REPO)/app/schemas.py
	cp src/api/config.py $(HF_API_REPO)/app/config.py
	cp src/api/preprocessing.py $(HF_API_REPO)/app/preprocessing.py
	cp src/api/requirements.txt $(HF_API_REPO)/requirements.txt
	cd $(HF_API_REPO) && git add . && git commit -m "sync from cc-fraud-pipeline" && git push