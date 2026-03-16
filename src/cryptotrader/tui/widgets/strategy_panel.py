"""Strategy status panel widget."""

from __future__ import annotations

from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static

from ...models.signal import Signal, SignalType


class StrategyPanelWidget(Static):
    """Shows current strategy info and last signal."""

    DEFAULT_CSS = """
    StrategyPanelWidget {
        height: auto;
        margin: 1;
        padding: 1;
        border: solid $accent;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("Waiting for data...", **kwargs)
        self._strategy_name = ""
        self._last_signal: Signal | None = None

    def set_strategy(self, name: str) -> None:
        self._strategy_name = name
        self._refresh_display()

    def update_signal(self, signal: Signal) -> None:
        self._last_signal = signal
        self._refresh_display()

    def _refresh_display(self) -> None:
        text = Text()
        text.append("Strategy: ", style="bold")
        text.append(self._strategy_name or "None", style="cyan")
        text.append("\n")

        if self._last_signal:
            text.append("Last Signal: ", style="bold")
            color_map = {
                SignalType.BUY: "green",
                SignalType.SELL: "red",
                SignalType.HOLD: "yellow",
            }
            color = color_map.get(self._last_signal.signal_type, "white")
            text.append(
                self._last_signal.signal_type.value.upper(), style=f"bold {color}"
            )
            text.append(f" (confidence: {self._last_signal.confidence:.0%})")

        panel = Panel(text, title="Strategy", border_style="blue")
        self.update(panel)
