from rich.console import Console


console = Console()

def eden_log(message: str):
    console.log(f"[bold cyan]Eden-MCP[/bold cyan]: {message}")
