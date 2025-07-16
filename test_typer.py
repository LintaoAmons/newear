#!/usr/bin/env python3
import typer
from typing import Optional

app = typer.Typer()

@app.command()
def test(
    list_devices: bool = typer.Option(False, "--list-devices", help="List devices"),
    device: Optional[int] = typer.Option(None, "--device", "-d", help="Device index"),
):
    print(f"list_devices = {list_devices} (type: {type(list_devices)})")
    print(f"device = {device} (type: {type(device)})")
    
    if list_devices:
        print("Listing devices!")
        return
    
    print("Running main functionality")

if __name__ == "__main__":
    app()