"""
Handles all user interface interactions for the Flickr Stats application.

This module uses the 'click' library to provide styled and consistent
console output for progress messages, errors, warnings, and successes.
"""

import click


def print_progress(message: str):
    """Prints a standard progress message."""
    click.echo(message)


def print_error(message: str):
    """Prints a styled error message in red."""
    click.echo(click.style(f"Error: {message}", fg="red"))


def print_warning(message: str):
    """Prints a styled warning message in yellow."""
    click.echo(click.style(f"Warning: {message}", fg="yellow"))


def print_success(message: str):
    """Prints a styled success message in green."""
    click.echo(click.style(message, fg="green"))
