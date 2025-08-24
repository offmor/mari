from datetime import datetime, timedelta

from rich.columns import Columns
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from marilib.marilib_cloud import MarilibCloud
from marilib.model import MariGateway


class MarilibTUICloud:
    """A Text-based User Interface for MarilibCloud."""

    def __init__(
        self,
        max_tables=3,
        re_render_max_freq=0.2,
    ):
        self.console = Console()
        self.live = Live(console=self.console, auto_refresh=False, transient=True)
        self.live.start()
        self.max_tables = max_tables
        self.re_render_max_freq = re_render_max_freq
        self.last_render_time = datetime.now()

    def get_max_rows(self) -> int:
        """Calculate maximum rows based on terminal height."""
        terminal_height = self.console.height
        available_height = terminal_height - 10 - 2 - 2 - 1 - 2
        return max(2, available_height)

    def render(self, mari: MarilibCloud):
        """Render the TUI layout."""
        with mari.lock:
            if datetime.now() - self.last_render_time < timedelta(
                seconds=self.re_render_max_freq
            ):
                return
            self.last_render_time = datetime.now()
            layout = Layout()
            layout.split(
                Layout(self.create_header_panel(mari), size=6),
                Layout(self.create_gateways_panel(mari)),
            )
            self.live.update(layout, refresh=True)

    def create_header_panel(self, mari: MarilibCloud) -> Panel:
        """Create the header panel with MQTT connection and network info."""
        status = Text()
        status.append("MarilibCloud is ", style="bold")
        status.append("connected", style="bold green")
        status.append(
            f" to MQTT broker {mari.mqtt_interface.host}:{mari.mqtt_interface.port} "
            f"at topic /mari/{mari.network_id_str}/to_cloud "
            f"since {mari.started_ts.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        status.append("  |  ")
        secs = int((datetime.now() - mari.last_received_mqtt_data_ts).total_seconds())
        status.append(
            f"last received: {secs}s ago",
            style="bold green" if secs <= 1 else "bold red",
        )

        status.append("\n\nNetwork ID: ", style="bold cyan")
        status.append(f"0x{mari.network_id:04X}")
        status.append("  |  ")
        status.append("Gateways: ", style="bold cyan")
        status.append(f"{len(mari.gateways)}")

        return Panel(status, title="[bold]MarilibCloud Status", border_style="blue")

    def create_gateways_table(self, gateways: list[MariGateway], title="") -> Table:
        """Create a table displaying information about connected gateways."""
        table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            padding=(0, 1),
            title=title,
        )
        table.add_column("Gateway", style="cyan")
        table.add_column("Schedule", style="white")

        for gateway in gateways:
            gateway_addr = f"0x{gateway.info.address:016X}"
            schedule_repr = gateway.info.repr_schedule_cells_with_colors()
            
            table.add_row(
                gateway_addr,
                schedule_repr,
            )
        return table

    def create_gateways_panel(self, mari: MarilibCloud) -> Panel:
        """Create the panel that contains the gateways table."""
        gateways = list(mari.gateways.values())
        max_rows = self.get_max_rows()
        max_displayable_gateways = self.max_tables * max_rows
        gateways_to_display = gateways[:max_displayable_gateways]
        remaining_gateways = max(0, len(gateways) - max_displayable_gateways)
        
        tables = []
        current_table_gateways = []
        
        for i, gateway in enumerate(gateways_to_display):
            current_table_gateways.append(gateway)
            if len(current_table_gateways) == max_rows or i == len(gateways_to_display) - 1:
                title = f"Gateways {i - len(current_table_gateways) + 2}-{i + 1}"
                tables.append(self.create_gateways_table(current_table_gateways, title))
                current_table_gateways = []
                if len(tables) >= self.max_tables:
                    break
        
        if len(tables) > 1:
            content = Columns(tables, equal=True, expand=True)
        elif tables:
            content = tables[0]
        else:
            content = Table(title="No Gateways Connected")
        
        if remaining_gateways > 0:
            panel_content = Group(
                content,
                Text(
                    f"\n(...and {remaining_gateways} more gateways)",
                    style="bold yellow",
                ),
            )
        else:
            panel_content = content
        
        return Panel(
            panel_content,
            title="[bold]Connected Gateways",
            border_style="blue",
        )

    def close(self):
        """Clean up the live display."""
        self.live.stop()
        print("")
