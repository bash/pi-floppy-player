class TerminalDisplay:
    def show(self, symbol, busy=False):
        if busy:
            print(f'{symbol}...')
        else:
            print(symbol)
