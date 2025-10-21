#!/usr/bin/env python
"""
Entry point for running the Carousel crew locally or via CLI.

The generate command exposes topic, slide count, aspect ratio, and persona so
you can spin up a bespoke PDF-ready report without touching source code.
"""

import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional
import typer

from carousel.crew import Carousel

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

ASPECT_CHOICES = ("16:9", "9:16", "1:1")

app = typer.Typer(
    add_completion=False,
    help="Generate high-end HTML + PDF reports using the Carousel multi-agent crew.",
)


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    """
    Default behavior when no subcommand is provided: offer interactive generation.
    """
    if ctx.invoked_subcommand is not None:
        return

    typer.echo("🎠 Carousel Report Studio")
    typer.echo("Generate polished HTML + PDF reports with multi-agent automation.\n")

    if typer.confirm("Would you like to generate a new report now?", default=True):
        topic_value, slides_value, aspect_value, persona_value = _collect_inputs()
        run(
            topic_content=topic_value,
            pages_numbers=slides_value,
            aspect_ratio=aspect_value,
            audience_persona=persona_value,
        )
    else:
        typer.echo("Come back anytime! Run with '--help' for usage details.")
    raise typer.Exit()


def run(
    topic_content: str = "siberian tiger",
    pages_numbers: int = 5,
    aspect_ratio: str = "16:9",
    audience_persona: str = "General executive audience",
) -> None:
    """
    Run the Carousel crew programmatically.
    """
    if aspect_ratio not in ASPECT_CHOICES:
        raise ValueError(f"Unsupported aspect ratio '{aspect_ratio}'. Choose from {ASPECT_CHOICES}.")

    Path("images").mkdir(exist_ok=True)
    print("✅ Ready to generate visuals in images/")

    inputs = {
        "topic_content": topic_content,
        "pages_numbers": pages_numbers,
        "aspect_ratio": aspect_ratio,
        "audience_persona": audience_persona,
    }

    try:
        Carousel().crew().kickoff(inputs=inputs)
    except Exception as exc:  # pragma: no cover - crew exceptions bubble up
        raise RuntimeError(f"An error occurred while running the crew: {exc}") from exc


def _prompt_aspect(default: str = "16:9") -> str:
    """
    Prompt the user until they choose a supported aspect ratio.
    """
    while True:
        value = typer.prompt(
            f"Target aspect ratio [{'/'.join(ASPECT_CHOICES)}]",
            default=default,
        ).strip()
        if value in ASPECT_CHOICES:
            return value
        typer.echo(f"Unsupported aspect ratio '{value}'. Choose from {ASPECT_CHOICES}.", err=True)


def _collect_inputs(
    topic: Optional[str] = None,
    slides: Optional[int] = None,
    aspect: Optional[str] = None,
    persona: Optional[str] = None,
) -> tuple[str, int, str, str]:
    """
    Resolve interactive input prompts and return sanitized values.
    """
    topic_value = topic.strip() if isinstance(topic, str) and topic.strip() else None
    if topic_value is None:
        topic_value = typer.prompt("Primary topic or theme for the report").strip()

    if isinstance(slides, int):
        slides_value = slides
    else:
        while True:
            raw = typer.prompt("Number of insight slides", default=5)
            try:
                slides_value = int(raw)
                if slides_value < 1:
                    raise ValueError
                break
            except (TypeError, ValueError):
                typer.echo("Please enter a positive integer for slides.", err=True)

    aspect_value = aspect.strip() if isinstance(aspect, str) and aspect.strip() else _prompt_aspect()
    persona_value = persona.strip() if isinstance(persona, str) and persona.strip() else typer.prompt(
        "Audience persona",
        default="General executive audience",
    ).strip()

    return topic_value, slides_value, aspect_value, persona_value


@app.command("generate")
def generate_command(
    topic: Optional[str] = typer.Argument(
        None,
        help="Primary topic or theme for the report. If omitted, you'll be prompted interactively.",
    ),
    slides: Optional[int] = typer.Option(
        None,
        "--slides",
        "-s",
        min=1,
        max=12,
        help="Number of insight pages to produce. Defaults to 5 if not supplied.",
    ),
    aspect: Optional[str] = typer.Option(
        None,
        "--aspect",
        "-a",
        case_sensitive=False,
        help="Target aspect ratio for visuals (16:9, 9:16, 1:1). Prompted if missing.",
    ),
    persona: Optional[str] = typer.Option(
        None,
        "--persona",
        "-p",
        help="Audience persona to guide tone, visuals, and layout decisions.",
    ),
) -> None:
    """
    Generate a brand-new report with customisable parameters.
    """
    topic_value, slides_value, aspect_value, persona_value = _collect_inputs(topic, slides, aspect, persona)

    run(
        topic_content=topic_value,
        pages_numbers=slides_value,
        aspect_ratio=aspect_value,
        audience_persona=persona_value,
    )


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year),
    }
    try:
        Carousel().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as exc:
        raise RuntimeError(f"An error occurred while training the crew: {exc}") from exc


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        Carousel().crew().replay(task_id=sys.argv[1])

    except Exception as exc:
        raise RuntimeError(f"An error occurred while replaying the crew: {exc}") from exc


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year),
    }

    try:
        Carousel().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as exc:
        raise RuntimeError(f"An error occurred while testing the crew: {exc}") from exc


if __name__ == "__main__":
    app()
