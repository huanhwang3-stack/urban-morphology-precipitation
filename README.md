# Urban Morphology and the Spatial Footprint of Urban Precipitation

**Code and model configurations associated with the manuscript "Urban morphology and the spatial footprint of urban precipitation"**

Submitted to *Nature Cities*.

## Overview

This repository contains the custom Python scripts, PALM model configuration files, and a reproducibility demonstration associated with the manuscript **"Urban morphology and the spatial footprint of urban precipitation"**.

The study combines satellite-based precipitation observations, atmospheric reanalysis, urban morphology information, and building-resolving large-eddy simulations (LES) to investigate the relationship between urban morphology and the spatial distribution of precipitation.

The observational analysis covers **34 cities across North America, Europe, and East Asia**, using GPM IMERG precipitation data and ERA5 atmospheric reanalysis for June–August 2020–2024.

Building-resolving LES are conducted using the **PALM model system (version 24.04)** to investigate the physical mechanisms associated with urban morphology, surface heating, boundary-layer development, and cloud formation.

The repository provides:

- Python scripts for observational data processing and analysis.
- Scripts for downloading ERA5 and GPM IMERG datasets.
- Python scripts for PALM LES post-processing and figure generation.
- PALM configuration files documenting the numerical simulations.
- A standalone demonstration for reproducing Fig. 1d using included processed observational data.

## 1. Repository Structure

```text
urban-morphology-precipitation/
│
├── observational_analysis/
│   ├── 1ERA5/
│   ├── 2IMERGE/
│   ├── 1.py
│   ├── Fig1b-d.py
│   └── Fig2.py
│
├── LES_postprocessing/
│   ├── Fig3a.py ... Fig3i.py
│   ├── Fig4a.py ... Fig4f.py
│   ├── Fig5a.py ... Fig5d.py
│   └── Fig6a.py ... Fig6f.py
│
├── PALM_configuration/
│   └── [PALM input and configuration files]
│
├── demo/
│   ├── Fig1d_demo.py
│   └── data/
│       ├── 1NY/
│       │   ├── out/
│       │   │   └── NYC__NORM_PROFILE_BY_WIND.npz
│       │   ├── out2/
│       │   │   └── NYC__NORM_PROFILE_BY_WIND.npz
│       │   └── out3/
│       │       └── NYC__NORM_PROFILE_BY_WIND.npz
│       │
│       └── 2Kansas/
│           ├── out/
│           │   └── NYC__NORM_PROFILE_BY_WIND.npz
│           ├── out2/
│           │   └── NYC__NORM_PROFILE_BY_WIND.npz
│           └── out3/
│               └── NYC__NORM_PROFILE_BY_WIND.npz
│
├── README.md
└── LICENSE
```

The entries representing groups of scripts or PALM configuration files are schematic. The repository directories contain the corresponding individual files.

## 2. Observational Analysis

The `observational_analysis/` directory contains scripts used for the observational component of the study.

The analysis examines wind-aligned precipitation patterns across 34 cities and their relationships with urban morphology.

### Directory Description

| Path | Description |
|---|---|
| `1ERA5/` | Scripts for downloading ERA5 atmospheric reanalysis data, including background wind fields. |
| `2IMERGE/` | Scripts for downloading GPM IMERG Version 07 precipitation data. |
| `1.py` | Main observational data processing and analysis. |
| `Fig1b-d.py` | Generates manuscript Fig. 1b–d. |
| `Fig2.py` | Generates manuscript Fig. 2. |

### Observational Data

The observational component uses:

**GPM IMERG Version 07**

- Spatial resolution: 0.1°
- Temporal resolution: 30 minutes
- Study period: June–August, 2020–2024

**ERA5 Atmospheric Reanalysis**

- Hourly atmospheric wind fields
- 850-hPa wind fields used to estimate background wind direction and wind speed

Urban morphology information is used to characterize differences in urban form across cities.

### Observational Workflow

1. Download the required ERA5 data using scripts in `1ERA5/`.
2. Download the GPM IMERG precipitation data using scripts in `2IMERGE/`.
3. Configure the input and output directories in `1.py`.
4. Run the observational processing and analysis.
5. Execute `Fig1b-d.py` and `Fig2.py` using the processed outputs to generate the corresponding manuscript figures.

### Data Sources

- **ERA5:** [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/)
- **GPM IMERG:** [NASA Global Precipitation Measurement](https://gpm.nasa.gov/data/imerg)

The full observational datasets are not included in the repository because of their large size.

Additional urban morphology inputs may be required for the full observational workflow.

## 3. LES Post-processing

The `LES_postprocessing/` directory contains Python scripts used to analyze PALM LES output and generate the manuscript figures.

The LES component investigates physical processes associated with urban morphology, including boundary-layer development, cloud formation, and precipitation-related atmospheric responses.

### Scripts and Figures

| Scripts | Manuscript figures |
|---|---|
| `Fig3a.py`–`Fig3i.py` | Fig. 3a–i |
| `Fig4a.py`–`Fig4f.py` | Fig. 4a–f |
| `Fig5a.py`–`Fig5d.py` | Fig. 5a–d |
| `Fig6a.py`–`Fig6f.py` | Fig. 6a–f |

### LES Post-processing Workflow

1. Obtain the required PALM simulation outputs.
2. Configure input directories and simulation-specific settings.
3. Run the corresponding Python scripts.
4. Generate the diagnostic quantities and manuscript figures.

The complete PALM output files are not included because of their large data volume.

Some scripts contain file paths from the original computing environment and may require modification before execution.

## 4. PALM Model Configuration

The `PALM_configuration/` directory contains configuration files documenting the building-resolving LES experiments.

The simulations were performed using:

**PALM Model System Version 24.04**

The configuration files document the numerical setup and prescribed atmospheric and surface conditions, including:

- Computational domain dimensions and grid resolution.
- Building geometry and urban-area configuration.
- Initial atmospheric temperature and humidity profiles.
- Background wind conditions.
- Urban and rural surface sensible heat fluxes.
- Boundary conditions and turbulence parameterizations.
- Simulation duration and output configurations.
- Case-specific modifications.

### Reproducing the LES

To reproduce a simulation:

1. Install or access PALM version 24.04.
2. Select the corresponding simulation configuration.
3. Provide any necessary external input and static driver files.
4. Adapt machine-specific settings and computational resource configurations.
5. Run the simulation using PALM.
6. Analyze the generated outputs with scripts in `LES_postprocessing/`.

Re-running the complete LES experiments requires a compatible PALM installation and substantial computational resources.

**PALM Documentation:** [PALM Model System](https://palm.muk.uni-hannover.de/)

## 5. Reproducibility Demo: Figure 1d

To facilitate reproducibility, this repository includes a **standalone demonstration script and processed observational datasets** for reproducing Fig. 1d of the manuscript.

The demonstration compares wind-aligned normalized precipitation profiles for two cities:

- New York City, USA
- Kansas City, USA

The comparison includes sensitivity tests using three precipitation thresholds.

The demonstration can be executed using the included processed data, without downloading the original ERA5 and IMERG datasets.

### Demo Directory

```text
demo/
├── Fig1d_demo.py
└── data/
    ├── 1NY/
    │   ├── out/
    │   │   └── NYC__NORM_PROFILE_BY_WIND.npz
    │   ├── out2/
    │   │   └── NYC__NORM_PROFILE_BY_WIND.npz
    │   └── out3/
    │       └── NYC__NORM_PROFILE_BY_WIND.npz
    │
    └── 2Kansas/
        ├── out/
        │   └── NYC__NORM_PROFILE_BY_WIND.npz
        ├── out2/
        │   └── NYC__NORM_PROFILE_BY_WIND.npz
        └── out3/
            └── NYC__NORM_PROFILE_BY_WIND.npz
```

Each output directory contains a processed NumPy `.npz` file used to generate the corresponding normalized precipitation profile.

### Step 1. Clone the Repository

```bash
git clone https://github.com/huanhwang3-stack/urban-morphology-precipitation.git

cd urban-morphology-precipitation
```

### Step 2. Install Python Dependencies

The demonstration uses standard scientific Python packages.

```bash
python -m pip install numpy scipy matplotlib
```

### Step 3. Run the Demonstration

```bash
python demo/Fig1d_demo.py
```

The script reads the processed precipitation profiles and generates the comparison figure corresponding to manuscript Fig. 1d.

The demonstration assumes that input paths are resolved relative to the demo script directory.

### Reproducibility Scope

This demonstration provides a minimal example of the figure-generation workflow.

It allows users to reproduce a selected manuscript figure directly from the included processed data.

The full observational processing pipeline, complete satellite precipitation datasets, and PALM LES outputs are not included in this standalone example.

The scripts required for the broader observational and numerical analyses are documented in the other repository directories.

## 6. Software Requirements

The original observational and LES post-processing scripts were developed using:

- Python 3.6.9
- NumPy
- SciPy
- Matplotlib
- Additional scientific Python packages required by individual scripts

Additional dependencies may be necessary for reading NetCDF, HDF5, ERA5, IMERG, or PALM datasets.

Users should inspect the imports in each script and install compatible package versions.

The original LES simulations used:

- PALM Model System 24.04
- Linux-based high-performance computing resources

The exact software environment for the full workflow is not provided as a complete dependency specification. Package compatibility may need to be adjusted for individual scripts.

## 7. Reproducing Manuscript Figures

The following table summarizes the scripts associated with the manuscript figures.

| Manuscript figure | Script location |
|---|---|
| Fig. 1b–d | `observational_analysis/Fig1b-d.py` |
| Fig. 1d (standalone demo) | `demo/Fig1d_demo.py` |
| Fig. 2 | `observational_analysis/Fig2.py` |
| Fig. 3a–i | `LES_postprocessing/Fig3a.py`–`Fig3i.py` |
| Fig. 4a–f | `LES_postprocessing/Fig4a.py`–`Fig4f.py` |
| Fig. 5a–d | `LES_postprocessing/Fig5a.py`–`Fig5d.py` |
| Fig. 6a–f | `LES_postprocessing/Fig6a.py`–`Fig6f.py` |

The complete figure-generation workflows generally require the corresponding processed observational data or PALM simulation outputs.

The standalone Fig. 1d demonstration is an exception because the required processed data are included in `demo/data/`.

## 8. Data Availability

The observational datasets used in this study are available from their original providers:

- ERA5 atmospheric reanalysis: [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/)
- GPM IMERG precipitation: [NASA GPM](https://gpm.nasa.gov/data/imerg)

The complete raw observational datasets and PALM simulation outputs are not hosted in this repository because of their large size.

A subset of processed observational data for New York City and Kansas City is included in the `demo/data/` directory to support direct reproduction of the Fig. 1d demonstration.

Additional processed observational datasets and LES outputs may be requested from the corresponding author, subject to storage and transfer constraints.

## 9. Notes on Reproducibility

This repository is intended to improve transparency and reproducibility by providing the custom analysis scripts and numerical model configurations associated with the manuscript.

Important considerations include:

- The standalone Fig. 1d demonstration is designed to run using the processed observational data included in the repository.
- The complete observational analysis requires additional input datasets, including ERA5, IMERG, and urban morphology information.
- Some scripts contain machine-specific absolute paths that must be adjusted before execution.
- Reproducing the PALM simulations requires appropriate model software, case configurations, input data, and computing resources.
- Each LES configuration was simulated once; no independent replicate simulations were performed.
- The observational findings were assessed using alternative precipitation thresholds and statistical uncertainty analyses, as described in the manuscript.

The standalone demonstration is not a substitute for reproducing the complete study, but provides an accessible example of the data-to-figure workflow.

## 10. License

This repository is distributed under the **MIT License**.

See the [LICENSE](LICENSE) file for details.

The license applies to the original code distributed in this repository. External datasets and PALM model software remain subject to their respective licenses and terms of use.

## 11. Citation

If you use the scripts or model configurations in this repository, please cite the associated manuscript:

*Urban morphology and the spatial footprint of urban precipitation*. Submitted to *Nature Cities*.

The citation information will be updated following publication.
