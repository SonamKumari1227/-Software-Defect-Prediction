"""
sdp - Software Defect Prediction
================================

A small, well-structured machine-learning package for predicting defect-prone
software modules from static code metrics (NASA MDP / PROMISE datasets).

Modules
-------
config          Load and validate ``config.yaml``.
utils           Logging, seeding, path helpers, JSON I/O.
data_loader     Download and parse ARFF datasets into pandas DataFrames.
preprocessing   Cleaning, train/test split and the scikit-learn preprocessing pipeline.
models          Registry of baseline classifiers and their hyper-parameter grids.
evaluate        Metric computation, cross-validation and hold-out evaluation.
visualization   All matplotlib / seaborn figures used in the report.
eda             Exploratory data analysis driver.
"""

__version__ = "1.0.0"
