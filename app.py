from flask import Flask, render_template
from bokeh.embed import components
from database import BillInfo, ExecutionStatus
from bokeh.plotting import figure
from plot import make_exec_status_plot

app = Flask(__name__)


@app.route('/')
def index():

    v_script, v_div = make_exec_status_plot('Verizon')
    c_script, c_div = make_exec_status_plot('Comcast')


    return render_template('dashboard.html',
                           verizon_exec_stat_script=v_script,
                           verizon_exec_stat_div=v_div,
                           comcast_exec_stat_script=c_script,
                           comcast_exec_stat_div=c_div)


@app.route('/data/')
def data():
    return BillInfo.objects.to_json()
