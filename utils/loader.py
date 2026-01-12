import threading
import time
from rich.live import Live
from rich.text import Text
from rich.console import Console

console = Console()

class HackerLoader:
    def __init__(self, description="Processing"):
        self.desc = description
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._animate)
        self.is_running = False

    def start(self):
        if not self.is_running:
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._animate)
            self.thread.start()
            self.is_running = True

    def stop(self):
        if self.is_running:
            self.stop_event.set()
            self.thread.join()
            self.is_running = False

    def _animate(self):
        with Live(console=console, refresh_per_second=10, transient=True) as live:
            dot_idx = 0
            while not self.stop_event.is_set():
                dots = "." * (dot_idx % 4)
                dot_idx += 1
                text = Text(f"🤖 AI ANALISIS : {self.desc}{dots}", style="bold cyan")
                live.update(text)
                time.sleep(0.15)
