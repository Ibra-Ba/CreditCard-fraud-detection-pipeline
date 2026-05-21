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

deploy-api:
	cp src/api/main.py cc-fraud-api-hf/app/main.py
	cp src/api/schemas.py cc-fraud-api-hf/app/schemas.py
	cp src/api/requirements.txt cc-fraud-api-hf/requirements.txt
	cd cc-fraud-api-hf && git add . && git commit -m "sync from cc-fraud-pipeline" && git push