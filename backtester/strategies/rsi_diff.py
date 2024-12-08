import backtrader as bt
from strategies.base_strategy import BaseStrategy

class RSIDiffStrategy(bt.Strategy):
    params = (
        ('rsi_diff_threshold', 20),
        ('position_size', 0.8),
        ('rsi_short', 7),
        ('rsi_long', 30),
    )

    def __init__(self):
        super().__init__()  # Inherit from BaseStrategy
        self.rsi_diff = self.datas[0].rsi_diff

        def next(self):
            if self.order:
                return

            if not self.position:
                if self.rsi_diff[0] > self.params.rsi_diff_threshold:
                    size = int(self.broker.getcash() * self.params.position_size / self.dataclose[0])
                    self.log(f'BUY CREATE, Price: {self.dataclose[0]:.2f}, Size: {size}')
                    self.order = self.buy(size=size)
            else:
                if self.rsi_diff[0] < -self.params.rsi_diff_threshold:
                    size = self.position.size
                    self.log(f'SELL CREATE, Price: {self.dataclose[0]:.2f}, Size: {size}')
                    self.order = self.sell(size=size)

class PandasDataWithRSIDiff(bt.feeds.PandasData):
        lines = ('rsi_diff',)
        params = (('rsi_diff', -1),)