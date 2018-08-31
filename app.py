from flask import Flask, render_template
from bokeh.embed import components
from database import BillInfo, ExecutionStatus
from bokeh.plotting import figure

app = Flask(__name__)


@app.route('/')
def index():
    p = figure()
    p.circle([1, 2, 3, 4, 5], [6, 7, 2, 4, 5], size=20, color="navy", alpha=0.5)

    script, div = components(p)

    return render_template('dashboard.html', exec_status_script=script, exec_status_div=div)


@app.route('/data/')
def data():
    return BillInfo.objects.to_json()
