# urban-morphology-precipitation
Python code for multi-city observational analysis of urban precipitation and PALM building-resolving large-eddy simulations associated with the manuscript "Urban morphology and the spatial footprint of urban precipitation".
# Code Availability

## Urban morphology and the spatial footprint of urban precipitation

This repository contains the custom Python scripts and PALM model configuration files associated with the manuscript **“Urban morphology and the spatial footprint of urban precipitation”** (submitted to *Nature Cities*).

The study combines precipitation observations, atmospheric reanalysis, urban morphology information, and building-resolving large-eddy simulations (LES) to investigate how urban morphology relates to the spatial distribution of precipitation.

## Repository structure

```text

├── observational_analysis/
│   ├── 1ERA5/
│   ├── 2IMERGE/
│   ├── 1.py
│   ├── Fig1b-d.py
│   └── Fig2.py
├── LES_postprocessing/
│   ├── Fig3a.py ... Fig3i.py
│   ├── Fig4a.py ... Fig4f.py
│   ├── Fig5a.py ... Fig5d.py
│   └── Fig6a.py ... Fig6f.py
└── PALM_configuration/
    └── [PALM input and configuration files for the simulation cases]
```

The line inside `PALM_configuration/` is a placeholder describing the intended contents, **not a literal filename**. Replace it with the actual filenames after uploading them.

## 1. Observational analysis

The `Code/observational_analysis/` directory contains scripts used for the observational component of the study, which analyzes 34 cities across North America, Europe, and East Asia.

| Path | Purpose |
| --- | --- |
| `1ERA5/` | Scripts for downloading ERA5 reanalysis data, including winds used to estimate background flow and align precipitation fields with wind direction. |
| `2IMERGE/` | Scripts for downloading GPM IMERG Version 07 precipitation data. |
| `1.py` | Main observational data processing and analysis. |
| `Fig1b-d.py` | Generates manuscript Fig. 1b–d. |
| `Fig2.py` | Generates manuscript Fig. 2. |

The observational analysis uses June–August data from 2020–2024.

### Observational workflow

1. Download the required ERA5 data with scripts in `1ERA5/`.
2. Download the required IMERG data with scripts in `2IMERGE/`.
3. Configure input and output paths, then run `1.py` for the main data processing and analysis.
4. Run `Fig1b-d.py` and `Fig2.py` using the processed outputs to generate the corresponding figures.

**Data sources**

- ERA5: [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/)
- GPM IMERG: [NASA Global Precipitation Measurement](https://gpm.nasa.gov/data/imerg)

The full raw observational datasets are not included because of their size. Additional urban morphology inputs required by individual scripts must also be obtained from the sources specified in the manuscript or script documentation.

## 2. LES post-processing

The `Code/LES_postprocessing/` directory contains Python scripts that calculate diagnostics from PALM LES output and generate manuscript figures.

| Scripts | Manuscript panels |
| --- | --- |
| `Fig3a.py`–`Fig3i.py` | Fig. 3a–i |
| `Fig4a.py`–`Fig4f.py` | Fig. 4a–f |
| `Fig5a.py`–`Fig5d.py` | Fig. 5a–d |
| `Fig6a.py`–`Fig6f.py` | Fig. 6a–f |

### LES post-processing workflow

1. Obtain the PALM output files needed by the relevant script.
2. Adjust input and output file paths and any case-specific settings.
3. Run the figure-specific scripts to calculate diagnostics and generate the corresponding figure panels.

Complete PALM output files are not included because of their large volume. Requests for processed datasets or simulation output can be directed to the corresponding author, subject to storage and transfer constraints.

## 3. PALM model configuration

The `Code/PALM_configuration/` directory is intended to contain the **PALM input and configuration files** used for the building-resolving LES cases in the manuscript.

The simulations were performed with **PALM model system version 24.04**. The model configurations document the settings used to define and run the LES, as applicable to each case, including:

- Computational-domain dimensions, grid spacing, and vertical grid structure.
- Building geometry and urban-area layout.
- Initial atmospheric profiles and boundary conditions.
- Urban and rural surface forcing, including prescribed heat fluxes.
- Simulation duration, output settings, and case-specific parameter choices.

These configuration files are provided to document the simulation setup; **they are not executable substitutes for the PALM model itself**. Re-running the LES requires a compatible PALM installation, appropriate model input files, and high-performance computing resources. Depending on the PALM setup, additional static or input datasets may be necessary.

### Reproducing an LES case

1. Install or access PALM version 24.04 in a compatible computing environment.
2. Choose the relevant case configuration from `PALM_configuration/`.
3. Supply any external input files required for that case and adapt machine-specific paths or job settings.
4. Run the simulation following the PALM model documentation.
5. Apply the scripts in `LES_postprocessing/` to the generated output.

PALM documentation: [PALM model system](https://palm.muk.uni-hannover.de/)

## 4. Software requirements

The original analysis environment used **Python 3.6.9** on Linux. The analysis scripts use scientific Python packages, including **NumPy, SciPy, and Matplotlib**. Other dependencies may be required for downloading and reading ERA5, IMERG, and PALM output files; users should check imports in the individual scripts and use compatible package versions.

The original simulations used **PALM 24.04** in a high-performance computing environment.

Package versions and a complete environment specification should be documented separately when available (for example, in `requirements.txt` or `environment.yml`).

## 5. Reproducing manuscript figures

| Manuscript figure | Script location |
| --- | --- |
| Fig. 1b–d | `Code/observational_analysis/Fig1b-d.py` |
| Fig. 2 | `Code/observational_analysis/Fig2.py` |
| Fig. 3a–i | `Code/LES_postprocessing/Fig3a.py`–`Fig3i.py` |
| Fig. 4a–f | `Code/LES_postprocessing/Fig4a.py`–`Fig4f.py` |
| Fig. 5a–d | `Code/LES_postprocessing/Fig5a.py`–`Fig5d.py` |
| Fig. 6a–f | `Code/LES_postprocessing/Fig6a.py`–`Fig6f.py` |

Scripts require the corresponding input datasets. Some contain absolute file paths from the original computing environment and will need to be adapted before running on another system. The raw observational datasets and complete LES outputs are **not** distributed with this repository.

## 6. Data availability

ERA5 and IMERG datasets are available from their original data providers using the links above. The complete raw datasets and large PALM simulation outputs are not hosted here because of their size. Processed observational datasets and LES outputs may be requested from the corresponding author, subject to storage and transfer constraints.

## 7. Notes on reproducibility

- The code documents the analyses and figure-generation procedures used in the manuscript, but obtaining the required input data and adjusting paths are necessary before execution.
- Reproducing PALM simulations requires compatible model software, case inputs, and substantial computing resources.
- The directory tree above summarizes the intended repository layout. Ensure all files described as available are actually uploaded before providing this repository to the editor.

## 8. Citation

If you use these scripts or configurations, please cite the manuscript:

*Urban morphology and the spatial footprint of urban precipitation*. Submitted to *Nature Cities*.
