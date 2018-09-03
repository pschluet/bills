from database import BillInfo, ExecutionStatus
from bokeh.models import LabelSet, ColumnDataSource
from bokeh.layouts import gridplot
from bokeh.plotting import figure
import pandas as pd
from abc import ABCMeta, abstractmethod


class Plotter(metaclass=ABCMeta):
    """
    Abstract base class for all classes that generate plot layouts
    """
    def make_plot_layout(self):
        """
        :return: bokeh Row or Column with the generated plot components
        """
        plots = []
        for service in self.get_unique_service_names():
            plots.append([self._make_single_plot(service)])
        height, width = self._get_plot_height_width_tuple()
        grid = gridplot(plots, sizing_mode='scale_width', plot_height=height, plot_width=width)
        return grid

    @abstractmethod
    def _make_single_plot(self, service_name):
        """
        Create a single plot in the layout

        :param service_name: string name of the service (i.e. 'Comcast') being plotted
        :return: bokeh Figure representing a single plot in the layout
        """
        pass

    @abstractmethod
    def _get_plot_height_width_tuple(self):
        """
        :return: a (height, width) tuple representing the desired aspect ratio of the plot
        """
        pass

    @staticmethod
    def get_unique_service_names():
        """
        :return: a list of unique service names from the database
        """
        return ExecutionStatus.objects().distinct(field='service_name')


class ExecutionStatusPlotter(Plotter):
    """
    Handles creating plots of scraper execution status
    """

    def __init__(self):
        self.MARKER_SIZE = 15
        self.NUM_ITEMS_TO_PLOT = 10

    def _get_plot_height_width_tuple(self):
        return 2, 10

    def _make_single_plot(self, service_name):
        pass_data = pd.DataFrame([x.to_dict() for x in ExecutionStatus.objects(service_name=service_name, success=True).order_by('-exec_time')[:self.NUM_ITEMS_TO_PLOT]])
        fail_data = pd.DataFrame([x.to_dict() for x in ExecutionStatus.objects(service_name=service_name, success=False).order_by('-exec_time')[:self.NUM_ITEMS_TO_PLOT]])

        p = figure(title=service_name, x_axis_type='datetime')
        p.circle(pass_data.exec_time, pass_data.success, size=self.MARKER_SIZE, color='green', alpha=0.5)

        if len(fail_data) > 0:
            p.circle(fail_data.exec_time, pass_data.success, size=self.MARKER_SIZE, color='red', alpha=0.5)

        p.xaxis[0].axis_label = 'Scraper Execution Time'
        p.yaxis[0].axis_label = 'Pass/Fail'

        return p


class BillInfoPlotter(Plotter):
    """
    Handles creating plots of scraped billing information
    """

    def __init__(self):
        self.MARKER_SIZE = 15

    def _get_plot_height_width_tuple(self):
        return 3, 10

    def _make_single_plot(self, service_name):
        df = pd.DataFrame([x.to_dict() for x in BillInfo.objects(service_name=service_name)])
        df['amt_str'] = df.apply(lambda row: '$' + str(row['amt_due']), axis=1)

        data = ColumnDataSource(df)

        p = figure(title=service_name, x_axis_type='datetime')
        p.circle(x='date_due', y='amt_due', source=data, size=self.MARKER_SIZE, alpha=0.5)
        p.line(x='date_due', y='amt_due', source=data)

        labels = LabelSet(x='date_due', y='amt_due', source=data, text='amt_str', level='glyph', x_offset=-18,
                          y_offset=10, render_mode='canvas')
        p.add_layout(labels)

        return p


if __name__ == "__main__":
    gp = ExecutionStatusPlotter().make_plot_layout()
    gp2 = BillInfoPlotter().make_plot_layout()