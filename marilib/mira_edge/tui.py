from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
import os

from mira_edge.mira_edge import MiraEdge


class MiraEdgeTUI:
    def __init__(self):
        self.console = Console()
        self.live = Live(console=self.console, auto_refresh=False, transient=True)
        self.live.start()
        # Store the number of lines we last printed
        self.last_height = 0

    def render(self, mira: MiraEdge):
        # Create layout
        layout = Layout()

        # Add components
        header = self.create_header_panel(mira)
        nodes_table = self.create_nodes_table(mira)

        # Create a layout with both components
        layout.split(
            Layout(header, size=8),
            Layout(nodes_table)
        )

        # Update display
        self.live.update(layout, refresh=True)

    def create_header_panel(self, mira: MiraEdge) -> Panel:
        status = Text()
        status.append('MiraEdge', style="bold cyan")
        status.append(" is ", style="bold")
        if mira.serial_connected:
            status.append("connected", style="bold green")
        else:
            status.append("disconnected", style="bold red")
        status.append(f" via {mira.port} at {mira.baudrate} baud\n")
        status.append("\n")

        # Gateway info
        status.append("Gateway: ", style="bold cyan")
        status.append(f"{mira.gateway.address}  |  ")
        status.append("Network ID: ", style="bold cyan")
        status.append(f"{mira.gateway.network_id}  |  ")
        status.append("Schedule ID: ", style="bold cyan")
        status.append(f"{mira.gateway.schedule_id}\n")

        # Network stats
        status.append("\nStats:    ", style="bold yellow")
        status.append("Nodes: ", style="bold cyan")
        status.append(f"{len(mira.gateway.nodes)}  |  ")
        status.append("Frames TX: ", style="bold cyan")
        status.append(f"{mira.gateway.stats.sent}  |  ")
        status.append("Frames RX: ", style="bold cyan")
        status.append(f"{mira.gateway.stats.received}")

        return Panel(
            status,
            title="[bold]MiraEdge Status",
            border_style="blue"
        )

    def create_nodes_table(self, mira: MiraEdge) -> Table:
        table = Table(
            show_header=True,
            header_style="bold cyan",
            title="Connected Nodes",
            border_style="blue"
        )

        # Add columns
        table.add_column("Node Address", style="cyan")
        table.add_column("Last Seen", style="")
        table.add_column("TX", justify="right", style="")
        table.add_column("RX", justify="right", style="")

        # Add rows for each node
        for node in mira.gateway.nodes:
            # Calculate time since last seen
            time_diff = datetime.now() - node.last_seen
            last_seen = f"{int(time_diff.total_seconds())}s ago"

            table.add_row(
                f"0x{node.address_int:016X}",
                last_seen,
                str(node.stats.sent),
                str(node.stats.received)
            )

        return table

    def close(self):
        """Clean up the live display."""
        self.live.stop()
        # Move cursor to a new line to ensure prompt appears correctly
        print("")
