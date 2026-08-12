# Unified-Logit ALNS for a Multi-Depot Location-Routing Problem with Flexible Service

This repository contains the **benchmark instances, source code, experimental settings, and computational results** associated with the research paper:

> **<Insert final paper title>**

The study considers a multi-depot location-routing problem integrating depot activation, customer allocation, vehicle routing, time-window constraints, profit maximization, and penalty-based service flexibility.

The repository is provided to support the **transparency, reproducibility, and reuse** of the computational experiments reported in the paper.

---

## Overview

The proposed framework jointly determines:

* which depots should be opened;
* how customers are assigned to depots;
* which customers should be served;
* how much demand should be delivered;
* how vehicles should be routed;
* how time-window violations and unmet demand should be handled.

The objective balances customer-related revenues against routing costs, depot-opening costs, shortage penalties, and lateness penalties.

Two Adaptive Large Neighborhood Search (ALNS) variants are investigated:

1. **ALNS-RW** — conventional roulette-wheel adaptive operator selection;
2. **ALNS-UL** — the proposed unified-logit operator-selection mechanism.

An exact mixed-integer programming formulation implemented in **Gurobi** is used as a reference method for computational comparison.

---

## Solution Methods

### Exact Optimization

The mathematical model is implemented using Gurobi and includes decisions related to:

* depot activation;
* vehicle-depot assignment;
* vehicle routing;
* customer service;
* delivered quantities;
* unmet demand;
* arrival times;
* lateness;
* vehicle utilization.

The exact model is primarily used to obtain optimal or best-known reference solutions for computationally tractable instances.

### Adaptive Large Neighborhood Search

The ALNS framework iteratively applies destroy and repair operators to explore the solution space.

The operator portfolio includes several removal and insertion mechanisms designed to modify routing, service, profit, and cost-related decisions.

### Roulette-Wheel Selection

In **ALNS-RW**, operators are selected using the conventional adaptive roulette-wheel mechanism. Operator weights are periodically updated based on their observed performance during the search.

### Unified-Logit Selection

In **ALNS-UL**, adaptive operator selection is formulated as a utility-based discrete-choice mechanism.

The utility of an operator may incorporate information such as:

* recent reward;
* acceptance performance;
* improvement performance;
* operator age;
* vehicle-related savings;
* routing-cost savings;
* profit-related savings;
* historical operator weight.

Operator utilities are transformed into selection probabilities using a softmax/logit mechanism. Temperature scaling and an exploration component are used to maintain sufficient exploration throughout the search.

---

## Benchmark Instances

The computational experiments are based on modified instances derived from the well-known **Solomon vehicle-routing benchmarks**, particularly the `R101` and `RC101` instance families.

The benchmark construction considers different combinations of:

* customer-set size;
* number of candidate depots;
* customer demand;
* time windows;
* depot capacities and/or fleet restrictions;
* customer revenue;
* shortage penalties;
* lateness penalties.

The exact instance-generation rules and parameter values used in the paper are documented in the benchmark files and accompanying documentation.

### Instance Naming Convention

Instance names follow a structure such as:

```text
R101_20c_3d
R101_20c_5d
RC101_30c_3d
RC101_40c_5d
```

where:

* `R101` / `RC101` identifies the Solomon instance family;
* `20c`, `30c`, etc. indicate the number of customers;
* `3d` / `5d` indicate the number of candidate depots.

---

## Repository Structure

```text
.
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
│
├── data/
│   ├── original/
│   └── modified_instances/
│
├── src/
│   ├── mip/
│   ├── alns_rw/
│   ├── alns_ul/
│   └── common/
│
├── experiments/
│   ├── run_gurobi.py
│   ├── run_alns_rw.py
│   ├── run_alns_ul.py
│   └── experiment_config.json
│
├── results/
│   ├── raw/
│   ├── summary/
│   └── tables/
│
├── figures/
│   ├── convergence/
│   └── operator_weights/
│
└── docs/
    └── instance_description.md
```

The exact organization may evolve as the repository is finalized.

---

## Requirements

The computational framework is implemented in Python.

Main dependencies include:

```text
Python
NumPy
Pandas
Matplotlib
Gurobi / gurobipy
```

Install the required Python packages using:

```bash
pip install -r requirements.txt
```

### Gurobi

The exact optimization model requires a valid installation and license for **Gurobi Optimizer**.

Gurobi is not distributed with this repository. Users should obtain the software and an appropriate license directly from Gurobi Optimization.

---

## Running the Experiments

### Exact Model

Example:

```bash
python experiments/run_gurobi.py --instance data/modified_instances/R101_20c_3d.txt
```

### ALNS-RW

Example:

```bash
python experiments/run_alns_rw.py \
    --instance data/modified_instances/R101_40c_3d.txt \
    --seed <SEED>
```

### ALNS-UL

Example:

```bash
python experiments/run_alns_ul.py \
    --instance data/modified_instances/R101_40c_3d.txt \
    --seed <SEED>
```

Please adjust the commands according to the final filenames and command-line interface included in the repository.

---

## Experimental Settings

The repository provides the parameter settings used in the computational study.

These include, where applicable:

* maximum ALNS iterations;
* segment length;
* removal-size limits;
* reward scores;
* reaction factor;
* simulated-annealing temperature parameters;
* cooling rate;
* stopping criteria;
* Unified-Logit coefficients;
* softmax temperature;
* exploration parameter;
* random seeds.

The purpose of providing these settings is to allow the computational experiments reported in the paper to be reproduced as closely as possible.

---

## Random Seeds

Because ALNS is stochastic, all random seeds used to generate the reported computational results are provided with the experiment configuration files.

For reproducibility, users should run the algorithms using the same:

* benchmark instance;
* parameter configuration;
* random seed;
* stopping criterion;
* software environment.

---

## Computational Results

The `results/` directory contains the computational outputs underlying the tables and figures reported in the paper.

Where available, results are separated into:

```text
results/raw/
```

for individual algorithm runs, and

```text
results/summary/
```

for processed summary statistics.

The repository may include:

* objective values;
* computation times;
* optimality gaps;
* best and average ALNS results;
* run-level results across random seeds;
* operator-selection statistics;
* convergence histories.

---

## Figures

Scripts and/or data used to generate the computational figures are included whenever possible.

These may include:

* convergence profiles;
* ALNS-RW operator-weight trajectories;
* ALNS-UL operator-weight trajectories;
* comparative performance figures;
* routing visualizations.

The figures in the manuscript are generated from the computational outputs rather than manually altered data.

---

## Reproducing the Paper Results

A recommended workflow is:

1. Install the required Python environment.
2. Install and activate Gurobi if exact-model experiments are required.
3. Select the benchmark instance.
4. Use the parameter configuration provided in the repository.
5. Run the relevant method using the reported random seeds.
6. Store the resulting raw output.
7. Run the provided processing scripts to reproduce summary statistics, tables, and figures.

Minor runtime differences may occur across machines because of differences in processors, operating systems, Python versions, solver versions, and parallelization settings.

---

## Data and Code Availability

The benchmark instances, computational code, experiment configurations, and supporting results associated with this study are made available through this repository to facilitate reproducibility.

A permanent archived version of the repository will be deposited in a research-data repository upon publication/submission of the associated manuscript.

**Permanent archive / DOI:** `<Zenodo or repository DOI to be added>`

---

## Benchmark Attribution

The benchmark instances used in this study are derived from the Solomon benchmark instances for vehicle-routing problems with time windows.

Users of this repository should also acknowledge and cite the original Solomon benchmark source where appropriate.

The modified instances distributed in this repository contain the adaptations required for the problem investigated in the associated paper.

---

## Citation

If you use the code, benchmark instances, or methodology contained in this repository, please cite the associated paper:

```bibtex
@article{<citation_key>,
  title   = {<Final paper title>},
  author  = {<Authors>},
  journal = {<Journal>},
  year    = {<Year>},
  doi     = {<DOI>}
}
```

A `CITATION.cff` file will also be provided to support automatic citation through GitHub.

---

## License

Unless otherwise stated, the source code developed specifically for this project is distributed under the **MIT License**.

Please note that third-party data, software, and benchmark material may remain subject to their original licenses, copyright conditions, and terms of use.

---

## Reproducibility

Reproducibility is a central objective of this repository.

To the extent permitted by third-party licenses and software restrictions, the repository provides the materials necessary to reproduce the computational analysis reported in the accompanying manuscript, including:

* benchmark-instance definitions;
* model and algorithm implementations;
* experimental parameters;
* random seeds;
* run-level computational results;
* scripts used to produce reported outputs.

If you identify a reproducibility issue, please open a GitHub issue describing the problem.

---

## Contact

For questions regarding the code, benchmark instances, or computational experiments, please contact:

**Seyyedreza Esmaeilzadeh**
E-mail: `<s.r.esmaeilzadeh@gmail.com>`

Alternatively, please use the **Issues** section of this GitHub repository for questions related to implementation or reproducibility.
