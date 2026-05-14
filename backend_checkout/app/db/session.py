"""
Database Session Management
============================
Creates the SQLAlchemy engine and session factory.
Provides a get_db() dependency for FastAPI route injection.
Will configure connection pooling and engine options based on config.
"""
