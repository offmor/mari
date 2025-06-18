from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.columns import Columns
from rich.console import Group
import os

from mira_edge.mira_edge import MiraEdge


class MiraEdgeTUI:
    def __init__(self, max_tables=3, max_rows=2):
        self.console = Console()
        self.live = Live(console=self.console, auto_refresh=False, transient=True)
        self.live.start()
        self.max_tables = max_tables
        self.max_rows = max_rows
        # Store the number of lines we last printed
        self.last_height = 0

    def render(self, mira: MiraEdge):
        # Create layout
        layout = Layout()

        # Create a layout with both components
        layout.split(
            Layout(self.create_header_panel(mira), size=8),
            Layout(self.create_nodes_panel(mira))
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
        status.append(f" via {mira.port} at {mira.baudrate} baud  |  ")
        secs = int((datetime.now() - mira.last_received_serial_data).total_seconds())
        style = "bold green" if secs <= 1 else "bold red"
        status.append(f"last received: {secs}s ago", style=style)
        status.append("\n\n")

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

    def create_nodes_table(self, nodes, title="") -> Table:
        """Create a table for a subset of nodes."""
        table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            padding=(0, 1),
            title=title
        )

        # Add columns
        table.add_column("Node Address", style="cyan")
        table.add_column("RX", justify="right", style="")

        # Add rows for each node
        for node in nodes:
            table.add_row(
                f"0x{node.address_int:016X}",
                str(node.stats.received)
            )

        return table

    def create_nodes_panel(self, mira: MiraEdge) -> Panel:
        """Create a panel containing the nodes tables."""
        nodes = mira.gateway.nodes
        total_nodes = len(nodes)

        # Calculate how many nodes we can show
        max_displayable_nodes = self.max_tables * self.max_rows
        nodes_to_display = nodes[:max_displayable_nodes]
        remaining_nodes = max(0, total_nodes - max_displayable_nodes)

        # Create tables
        tables = []
        current_table_nodes = []

        for i, node in enumerate(nodes_to_display):
            current_table_nodes.append(node)

            # Create a new table when we hit max rows or last node
            if len(current_table_nodes) == self.max_rows or i == len(nodes_to_display) - 1:
                start_idx = i - len(current_table_nodes) + 1
                end_idx = i + 1
                title = f"Nodes {start_idx + 1}-{end_idx}"
                tables.append(self.create_nodes_table(current_table_nodes, title))
                current_table_nodes = []

                # Stop if we've hit max tables
                if len(tables) >= self.max_tables:
                    break

        # Create the layout
        if len(tables) > 1:
            content = Columns(tables, equal=True, expand=True)
        else:
            content = tables[0] if tables else Table()

        # Create the panel content with optional footer
        if remaining_nodes > 0:
            panel_content = Group(
                content,
                Text(f"\n(...and {remaining_nodes} more nodes)", style="bold yellow")
            )
        else:
            panel_content = content

        return Panel(
            panel_content,
            title="[bold]Connected Nodes",
            border_style="blue"
        )

    def close(self):
        """Clean up the live display."""
        self.live.stop()
        # Move cursor to a new line to ensure prompt appears correctly
        print("")
