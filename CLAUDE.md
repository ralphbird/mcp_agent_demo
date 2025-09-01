# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a demo MCP (Model Context Protocol) agent project written in Python. This is currently a minimal project setup ready for development.

## Development Setup

Since no specific dependency management is configured yet, determine the appropriate approach based on project needs:
- For Poetry: `poetry install` and use `poetry run <cmd>` for commands
- For pip: `pip install -r requirements.txt` (when created)
- For uv: `uv sync` (when pyproject.toml is configured)

## Common Commands

### API Service (Phase 1 Complete)
```bash
# Navigate to API directory
cd api

# Install dependencies
poetry install

# Run the application
poetry run python -m currency_app.main

# Development with auto-reload
poetry run uvicorn currency_app.main:app --reload

# Run tests
poetry run pytest
poetry run pytest -v  # verbose output

# Code quality
poetry run ruff format .  # format code
poetry run ruff check .   # lint code  
poetry run pyright        # type checking

# All quality checks
poetry run ruff format . && poetry run ruff check . && poetry run pyright
```

## Code Style

Follow Python conventions:
- Use lowercase built-in types: `list`, `dict`, `set`, `tuple` (not `List`, `Dict`, etc.)
- Keep line length to 100 characters
- Use Google-style docstrings
- No trailing whitespace
- Files should end with a newline
- Follow any ruff rules when pyproject.toml is configured

## Architecture

This is a currency conversion demo application with the following structure:
- `currency_app/` - Main FastAPI application code
- `currency_app/models/` - Pydantic models and database models
- `currency_app/routers/` - API endpoint definitions
- `currency_app/services/` - Business logic (currency conversion, rate management)
- `currency_app/database.py` - Database configuration and connections
- `tests/` - Test suite

Update this section as the architecture develops with actual implementation details.