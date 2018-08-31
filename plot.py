from database import BillInfo, ExecutionStatus
import pandas as pd


def make_exec_status_plot():
    data = pd.DataFrame([x.to_dict() for x in ExecutionStatus.objects])


def make_bill_info_plot():
    data = pd.DataFrame([x.to_dict() for x in BillInfo.objects])


if __name__ == "__main__":
    make_exec_status_plot()
    make_bill_info_plot()
