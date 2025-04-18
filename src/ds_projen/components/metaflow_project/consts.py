"""Constants for the MetaflowProject component."""

from typing import Literal

REQUIRES_PYTHON = ">=3.9"

DATA_SCIENCE_DOMAINS = {
    "content": ["Phil Huebner"],
    "operations": ["Jacob Miller", "Colton Fowler"],
    "forecasting": ["Brad Eustice"],
    "market-intelligence": ["Hamilton Noel", "Utsav Savaliya", "Pradnesh Lachake"],
    "demand-generation": ["Yi Gong"],
    "advertising": ["Krishna Priya", "Siva Rajananda"],
    "reference": ["Eric Riddoch"],
}
TDataScienceDomain = Literal[
    "content",
    "operations",
    "forecasting",
    "market-intelligence",
    "demand-generation",
    "advertising",
    "reference",
]
