from gpiozero import LED

class SevenSegmentDisplay:
    # Maps segments of the seven-segment display to the corresponding GPIO pins.
    SEGMENTS_TO_PINS = { 'g': 15, 'f': 18, 'a': 23, 'b': 24, 'e': 3, 'd': 4, 'c': 17, '.': 27 }
    SYMBOLS_TO_SEGMENTS = { 'I': ['e', 'f'], 'E': ['a', 'd', 'e', 'f', 'g'], 'P': ['a', 'b', 'e', 'f', 'g'] }

    def __init__(self):
        self.leds = { segment: LED(pin) for (segment, pin) in SevenSegmentDisplay.SEGMENTS_TO_PINS.items() }

    def show(self, symbol, busy=False):
        on = set(SevenSegmentDisplay.SYMBOLS_TO_SEGMENTS[symbol])
        for segment, led in self.leds.items():
            if segment in on:
                led.on()
            else:
                led.off()
        if busy:
            self.leds['.'].blink()
