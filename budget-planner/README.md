# Budget Planner (Flask + SQLite)

A simple web app to track income and expenses, set a monthly budget, and see spending by category.

## Project structure

```
budget-planner/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    └── style.css
```

## Run it in VS Code

1. Open the `budget-planner` folder in VS Code (File > Open Folder).
2. Open the terminal (Ctrl + `) and create a virtual environment:
   - Windows: `python -m venv venv` then `venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv venv` then `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python app.py`
5. Open http://127.0.0.1:5000 in your browser.

The database file `budget.db` is created automatically on first run.

## Recommended VS Code extensions

- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Jinja (wholroyd.jinja) for the HTML templates
- SQLite Viewer (qwtel.sqlite-viewer) to browse budget.db
- Live Server is NOT needed (Flask serves the pages)
- Optional: Prettier (esbenp.prettier-vscode), Black Formatter (ms-python.black-formatter)
