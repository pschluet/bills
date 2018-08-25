from flask import Flask
from database import BillInfo

app = Flask(__name__)


@app.route('/')
def index():
    return 'Hello'


@app.route('/data/')
def data():
    return BillInfo.objects.to_json()
