install:
	pip install -r requirements.txt

format:
	isort .
	black .

shortput-report:
	python src/options/expected_move.py
	python src/options/expected_move_reliability.py
	python src/reporting/shortput_report.py