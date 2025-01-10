import typer
import uvicorn
from fastapi import FastAPI, staticfiles
from pathlib import Path
from rich import print

app = typer.Typer()
api = FastAPI()

# Serve static files from web/dist
web_dir = Path(__file__).parent.parent / "static" / "dist"
if not web_dir.exists():
    raise FileNotFoundError(f"Static files directory not found: {web_dir}")

api.mount("/", staticfiles.StaticFiles(directory=str(web_dir), html=True))


@app.command()
def start_app():
    """Start the FastAPI server"""

    uvicorn.run(api, host="0.0.0.0", port=8000)
    print(
        "\n[bold green]🚀 Access website at[/bold green] [bold blue][http://localhost:8000](http://localhost:8000)[/bold blue]\n"
    )


if __name__ == "__main__":
    app()
