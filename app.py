from flask import Flask, render_template
from bokeh.embed import components
from database import BillInfo
from plot import ExecutionStatusPlotter, BillInfoPlotter

app = Flask(__name__)


@app.route('/')
def index():

    plotters = [ExecutionStatusPlotter(), BillInfoPlotter()]

    script, (exec_status_plot_div, bill_info_plot_div) = components([x.make_plot_layout() for x in plotters])

    return render_template('dashboard.html',
                           script=script,
                           exec_status_plot_div=exec_status_plot_div,
                           bill_info_plot_div=bill_info_plot_div)


@app.route('/data/')
def data():
    return BillInfo.objects.to_json()
