import backtrader as bt
from strategies.base_strategy import BaseStrategy

class TrendStrategy(BaseStrategy):
    params = (
        ('atr_window', 14),
        ('atr_multiplier', 3),
        ('direction_threshold', 0.05),
        ('use_absolute', True),
        ('position_size', 0.8)
    )

    def __init__(self):
        super().__init__()  # Inherit from BaseStrategy
        self.direction = self.datas[0].direction

    def next(self):
        if self.order:
            return

        current_direction = self.direction[0]

        if current_direction != self.last_direction:
            if current_direction == 1 and not self.position:
                size = int(self.broker.getcash() * self.params.position_size / self.dataclose[0])
                self.log(f'BUY CREATE, Price: {self.dataclose[0]:.2f}, Size: {size}')
                self.order = self.buy(size=size)
            elif current_direction == -1 and self.position:
                size = self.position.size
                self.log(f'SELL CREATE, Price: {self.dataclose[0]:.2f}, Size: {size}')
                self.order = self.sell(size=size)

        self.last_direction = current_direction

class PandasDataWithDirection(bt.feeds.PandasData):
    lines = ('direction',)
    params = (('direction', -1),)

