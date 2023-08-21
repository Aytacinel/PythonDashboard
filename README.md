
# Flask Textile Application

## Description

This application is a Flask-based web server that interfaces with a SQL Server database to fetch invoice and sales data for a textile company. Users can provide a date range, and the application will retrieve and display various metrics related to invoices and sales during that period.

## Features

- Connects to a SQL Server database using `pyodbc`.
- Users can input a date range to fetch relevant data.
- Displays metrics like total invoice amount, total sales, and more.
- Provides visual representations and charts based on the fetched data.

## Installation and Setup

1. Ensure you have Flask and pyodbc installed:
```
pip install Flask pyodbc
```

2. Update the database connection parameters (`server`, `database`, `username`, `password`, etc.) in the `app.py` file.

3. Run the application:
```
python app.py
```

4. Navigate to `http://127.0.0.1:5000/` in your browser to access the application.

