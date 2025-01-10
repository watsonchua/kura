import typer
import uvicorn
from kura.cli.server import api
from rich import print

app = typer.Typer()


@app.command()
def start_app():
    """Start the FastAPI server"""

    uvicorn.run(api, host="0.0.0.0", port=8000)
    print(
        "\n[bold green]🚀 Access website at[/bold green] [bold blue][http://localhost:8000](http://localhost:8000)[/bold blue]\n"
    )


if __name__ == "__main__":
    app()
