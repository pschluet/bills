from database import BillInfo, ExecutionStatus
from bokeh.models import LabelSet, ColumnDataSource
from bokeh.layouts import gridplot
from bokeh.plotting import figure, show
import pandas as pd


def make_exec_status_plot(service_name):
    marker_size = 15
    num_items_to_plot = 10

    pass_data = pd.DataFrame([x.to_dict() for x in ExecutionStatus.objects(service_name=service_name, success=True).order_by('-exec_time')[:num_items_to_plot]])
    fail_data = pd.DataFrame([x.to_dict() for x in ExecutionStatus.objects(service_name=service_name, success=False).order_by('-exec_time')[:num_items_to_plot]])

    p = figure(title=service_name, x_axis_type='datetime')
    p.circle(pass_data.exec_time, pass_data.success, size=marker_size, color='green', alpha=0.5)

    if len(fail_data) > 0:
        p.circle(fail_data.exec_time, pass_data.success, size=marker_size, color='red', alpha=0.5)

    p.xaxis[0].axis_label = 'Scraper Execution Time'
    p.yaxis[0].axis_label = 'Pass/Fail'

    return p


def make_bill_info_plot(service_name):
    marker_size = 15

    df = pd.DataFrame([x.to_dict() for x in BillInfo.objects(service_name=service_name)])
    df['amt_str'] = df.apply(lambda row: '$' + str(row['amt_due']), axis=1)

    data = ColumnDataSource(df)

    p = figure(title=service_name, x_axis_type='datetime')
    p.circle(x='date_due', y='amt_due', source=data, size=marker_size, alpha=0.5)
    p.line(x='date_due', y='amt_due', source=data)

    labels = LabelSet(x='date_due', y='amt_due', source=data, text='amt_str', level='glyph', x_offset=-18, y_offset=10, render_mode='canvas')
    p.add_layout(labels)

    return p


def make_bill_info_plots():
    vbi = make_bill_info_plot('Verizon')
    cbi = make_bill_info_plot('Comcast')
    grid = gridplot([[vbi], [cbi]], sizing_mode='scale_width', plot_height=3, plot_width=10)
    return grid


def make_exec_status_plots():
    ves = make_exec_status_plot('Verizon')
    ces = make_exec_status_plot('Comcast')
    grid = gridplot([[ves], [ces]], sizing_mode='scale_width', plot_height=2, plot_width=10)
    return grid


if __name__ == "__main__":
    make_exec_status_plot('Verizon')
    make_exec_status_plot('Comcast')
    make_bill_info_plot()
