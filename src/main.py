import typer

from src.commands import app as commands_app

app = typer.Typer()

app.add_typer(commands_app, name="make")

if __name__ == "__main__":
    app()
