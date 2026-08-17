# Unified-Logit ALNS for a Multi-Depot Location-Routing Problem with Flexible Service

This repository provides the **source code and benchmark instances** associated with the research paper:

> **<Paper title>**

The study addresses a multi-depot location-routing problem integrating depot activation, customer allocation, vehicle routing, time-window constraints, profit maximization, and penalty-based service flexibility.

Two Adaptive Large Neighborhood Search (ALNS) approaches are considered:

* **ALNS-RW:** conventional roulette-wheel operator selection.
* **ALNS-UL:** proposed unified-logit operator selection.

A Gurobi-based exact model is used for comparison.

## Repository Structure

```text
MDLVRPTW-PF/
├── Code/
│   └── Source code
├── instances_csv/
│   └── Benchmark instances
├── README.md
└── LICENSE
```

## Benchmark Instances

The instances are derived from the **Solomon R101 and RC101 benchmarks** and include different combinations of customer and candidate-depot sizes.

For example:

```text
R101_20c_3d.csv
R101_30c_5d.csv
RC101_40c_3d.csv
RC101_50c_5d.csv
```

where `20c` denotes 20 customers and `3d` denotes 3 candidate depots.

## Requirements

* Python
* NumPy
* Pandas
* Gurobi / gurobipy

A valid Gurobi license is required to run the exact optimization model.

## Reproducibility

The code and benchmark instances are provided to support reproduction of the computational experiments reported in the paper.

## License

The source code is distributed under the **MIT License**.

## Contact

**Seyyedreza Esmaeilzadeh**
E-mail: [s.r.esmaeilzadeh@gmail.com](mailto:s.r.esmaeilzadeh@gmail.com)
