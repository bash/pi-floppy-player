try:
    from .seven_segment import SevenSegmentDisplay as Display
except ModuleNotFoundError:
    from .terminal import TerminalDisplay as Display
