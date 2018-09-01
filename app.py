from flask import Flask, render_template
from bokeh.embed import components
from database import BillInfo, ExecutionStatus
from bokeh.plotting import figure
from plot import make_exec_status_plots, make_bill_info_plots

app = Flask(__name__)


@app.route('/')
def index():

    exec_status_plots = make_exec_status_plots()
    bill_info_plots = make_bill_info_plots()

    script, (exec_status_plot_div, bill_info_plot_div) = components([exec_status_plots, bill_info_plots])

    return render_template('dashboard.html',
                           script=script,
                           exec_status_plot_div=exec_status_plot_div,
                           bill_info_plot_div=bill_info_plot_div)


@app.route('/data/')
def data():
    return BillInfo.objects.to_json()
