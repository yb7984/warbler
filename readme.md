# Warbler
This is a twitter clone project using Python and PostgreSQL.


## Authors

Sunbao Wu[@yb7984](https://www.github.com/yb7984)  
Email: [bobowu@outlook.com](mailto:bobowu@outlook.com)  
Linkedin: [https://www.linkedin.com/in/sunbao-wu/](https://www.linkedin.com/in/sunbao-wu/)


## Tech Stack
[![Python](https://img.shields.io/badge/%20-Python-blue)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/%20-PostgreSQL-blue)](https://www.postgresql.org/)
[![Flask](https://img.shields.io/badge/%20-Flask-green)](https://flask.palletsprojects.com/en/2.0.x/)

## Setup

Create the Python virtual environment:

```console
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt

(venv) $ createdb warbler
(venv) $ python3 seed.py

(venv) $ flask run
```

Then you can access the website on http://127.0.0.1:5000/