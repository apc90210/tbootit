# Architecture

## Components
- **Core API**: Central system owning the database and storage. Uses FastAPI, SQLite, and SQLAlchemy.
- **Admin Shell**: Separate frontend interacting purely via HTTP API to the Core.

## Principles
1. Core API is the single source of truth.
2. Direct database access from outside the Core is forbidden.
3. Media files are served by the Core API.
