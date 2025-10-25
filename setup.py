"""Setup script for MOTHRA package."""

from setuptools import find_packages, setup

setup(
    name="mothra",
    version="0.1.0",
    description="Master Agent Orchestration for Carbon Database Construction",
    author="MOTHRA Team",
    packages=find_packages(exclude=["tests*", "scripts*"]),
    python_requires=">=3.10",
    install_requires=[
        # Core dependencies from requirements.txt
        "asyncpg>=0.29.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.13.0",
        "aiohttp>=3.9.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "pyyaml>=6.0.1",
        "structlog>=24.1.0",
        "python-dotenv>=1.0.0",
        "redis>=5.0.1",
        "sentence-transformers>=3.0.0",
        "torch>=2.1.0",
        "pandas>=2.1.4",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.12.0",
            "ruff>=0.1.9",
            "mypy>=1.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mothra-survey=mothra.agents.survey.survey_agent:main",
            "mothra-crawler=mothra.agents.crawler.crawler_agent:main",
            "mothra-embedding=mothra.agents.embedding.vector_manager:main",
        ],
    },
)
