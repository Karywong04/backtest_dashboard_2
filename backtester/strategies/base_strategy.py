import backtrader as bt

class BaseStrategy(bt.Strategy):
    params = (
        ('position_size', 0.8),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.last_direction = None

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Size: {order.executed.size}')
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Size: {order.executed.size}')

        self.order = None

    def next(self):
        if self.order:
            return
