from database import BillInfo, ExecutionStatus
from bokeh.embed import components
from bokeh.plotting import figure, show
import pandas as pd


def make_exec_status_plot(service_name):
    pass_data = pd.DataFrame([x.to_dict() for x in ExecutionStatus.objects(service_name=service_name, success=True)])
    fail_data = pd.DataFrame([x.to_dict() for x in ExecutionStatus.objects(service_name=service_name, success=False)])

    #p = figure(title=service_name + ' Scraping Executions', plot_width=10, plot_height=4, x_axis_type='datetime')
    p = figure(title=service_name + ' Scraping Executions', x_axis_type='datetime')
    marker_size = 15
    #p.sizing_mode = 'scale_both'
    p.circle(pass_data.exec_time, pass_data.success, size=marker_size, color='green', alpha=0.5)

    if len(fail_data) > 0:
        p.circle(fail_data.exec_time, pass_data.success, size=marker_size, color='green', alpha=0.5)

    p.xaxis[0].axis_label = 'Scraper Execution Time'
    p.yaxis[0].axis_label = 'Pass/Fail'

    return components(p)


def make_bill_info_plot():
    data = pd.DataFrame([x.to_dict() for x in BillInfo.objects])


if __name__ == "__main__":
    make_exec_status_plot('Verizon')
    make_exec_status_plot('Comcast')
    make_bill_info_plot()
