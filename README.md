# Unlocking Global Capital

This repository is part of my MSc Independent Research Project at Imperial College London in collaboration with AIP investments services.

The system is ML driven pipeline that predicts investor contact details from a given `(name, firm)` pair (along with an optional domain parameter). This repository contains the EDA done to guide implementation, the pattern mining portion that identifies a candidate template set as well as generates engineered features as well as the actual prediction model written in C++.

Key contributions:
- **Pattern Mining:** Discover and normalize firm-specific email templates.
- **Feature Engineering:** Extract structural features from investor names and firm domains.
- **Model Training:** CatBoost/LightGBM ranking models optimized for Accuracy@1, Recall@3, and MRR.
- **Inference Engine:** Low-latency C++ predictor with pybind11 bindings.
- **Deployment:** REST API wrapper for real-time use.

The goal is to build a robust, scalable pipeline that improves investor contact accuracy, addressing issues of data decay and closed networks.

## Repo Layout

Bellow is a map of the repo:

```bash
irp-db1724/
    |-.github/                      # CI Scripts
    |-.vscode/                      # VsCode config JSONs
    |-cpp_inference_engine/         # C++ inference engine
    |---|-api/                      # REST API service
    |---|-cpp/                      # Core C++ code for inference
    |---|-scripts/                  # Scripts for msgpack data integration and API testing
    |---|-tests/                    # GTest C++ unit tests
    |-data/                         # Test data CSV and generate SQL table location
    |-db/                           # SQLAlechemy SQL interactions (Python)
    |-deliverables/                 # Project Plan and Final Report
    |-email_prediction/             # Email Prediction pipeline. Top level for all data generation and training.
    |---|-feature_engineering/      # Feature engineering and padding code
    |-etl/                          # ETL pipeline
    |---|-extract/                  # Raw data extraction code
    |---|-load/                     # Raw and clean data loading into SQL 
    |---|-transform/                # Cleaning and validation pipeline
    |-fuzzlookup/                   # Fuzzylookup SQL data generation and early python version of functionality
    |-interim_reports/              # Interim reports for early phases
    |-logbook/                      # Logbook for supervisor meetings
    |-notebooks/                    # Notebooks that include analysis and document development before consolidation into pipeline
    |---|-EDA/                      # EDA results and notes
    |---|-ModelDevelopment/         # Model development done here
    |---|-PatternMining/            # Pattern mining done here
    |-pattern_mining/               # Pattern mining pipeline
    |-tests/                        # Pytest unit tests
```
### Python Code

Early phases of the project focused on EDA, pattern mining and model training/evaluation. This was done in python and is validated through unit tests. Initial work was done all in notebooks which can be found in the `notebooks` folder which has nested subfolders dedicated to each phase.

Work in notebooks represent early development and will largely be unrepeatable since the pipeline code that it is dependent on has matured considerably since early phases. All outputs are saved for readers to inspect, this work is the foundation of the pipeline and provides the key insights and prototype code for the final product.

The `EDA` subfolder in `notebooks` is largely synonymous with the `etl` folder and its pipeline. First phase EDA focused on understanding the data, identifying patterns and cleaning and imputation strategies which were either copied over to the pipeline or in part optimized or reworked to fit into the code. 

The `PatternMining` subfolder in `notebooks` was ported into `pattern_mining`. Similar to the EDA phase. This phase also featured its own separate EDA phase which looked into template distribution which guided feature engineering.

`ModelDevelopment` in `notebooks` shows early training attempts as well as analysis on failing cases. It also features other notebooks that were run on Google Colab when local training was computationally unfeasible. Here you will find test results (pulled from cpp inference engine) and training and validation results all the way to the final model. Some of the work here is reflected in the `email_prediction` folder where the top level pipeline for data training and generation exists, as well as the synthetic padding and feature building lives. This code was pulled from `ModelDevelopment`and in part optimized or refactored to be suitable for pipeline code. 

All SQL data interactions are kept in the `db` folder which provides low level SQLAlchemy code that allows the rest of the pipeline to work. 

Pipeline code is packaged and managed through a `poetry` toml file which manages Python dependencies. It also allows us to use to import the project as a module for reuse outside of the repository.

### C++ Code


The `cpp_inference_engine` folder holds all of the C++ code needed for the inference engine. All testing on held-out contacts are done with this engine.

It depends on the `rapidfuzz`, `LightGBM` and `CatBoost` external libraries which are included as submodules. It is built with GCC 13.3.0 and C++23 and contains GTest unit tests that prove functionality as well provide integration tests on held-out contacts.

Within this folder, there is an `api` folder which contains our REST API service. This depends on the pybindings build that wraps the C++ in a Python importable module, separate tests exist to prove this interface. The pybindings are built through the regular build and the interfaces are defined in `bindings.cpp` in the `cpp/src` subfolder. 

A Makefile exists at this level that provides multiple build options for building the Docker container that makes the REST API live and waits for post requests at `http://localhost:8000`. It also includes options for benchmark and integration tests. Scripts to make this work exist in the `scripts` subfolder. 

## Building

Firstly, the project should be clone and submodules updated.

```bash
# Clone repo 
git clone git@github.com:ese-ada-lovelace-2024/irp-db1724.git
# Update submodules
git submodule update --init --recursive
```

### Python Code

Before running any of the Python code, we must build the `conda` environment, from the project root and the yml file.

```bash
# Build ENV
conda env create -f environment.yml
# Activate it
conda activate irp-db1724
```

This project uses `poetry` for dependency management, so we must install the project from the toml.

```bash
# Install project dependencies defined in pyproject.toml
poetry install
```

Now we can run the pytest unit tests to confirm our package is installed. These should all pass with no errors. Alternatively, we could select the run "Run All Pytest" configuration in the "Run And Debug" pane and press F5 to do this automatically (make sure you select "irp-db1724" as the Python interpreter).

```bash 
# Run pytest in poetry
poetry run pytest -q -v
```

We are now in a position to run the `email_prediction` pipeline. This is the top level pipeline that will clean, validate, run pattern mining and feature engineering, pad with synthetic investors and generate feature matrices for the segmented model training. This will write all data (raw data, clean data, patter mining results, all metadata and feature matrices) to an SQL .db file in the `data` folder at root.

We can do this in a similar way to our pytest example.

```bash
# Run email_prediction pipeline
poetry run python -m email_prediction.pipeline
```

This lengthy process will end with all the data we need to train our models. From here, we can either take a notebook from `notebooks/ModelDevelopment/Testing` or making a notebook from the training function example in `email_prediction/cat_boost_training.py` and uploading to Google Colab. From there, the .db file can be taken to Google Drive (make sure the paths in the notebook match with the actual location Google Drive) and training can be done. The resulting .cbm files should be downloaded from Google Drive and placed in `cpp_inference_engine/cpp/model`. At which point the C++ engine can be built and integration tests can be run.

### C++ Code

The C++ code requires GCC 13.3.0 and C++23. It was also built on WSL Ubuntu, it has not been tested on other OSes but since it has Docker dependencies it is best to be built in some sort of Linux distribution. 

For all work on the C++ inference engine, you must be in the `cpp_inference_engine` directory.

```bash
# Change directories
cd cpp_inference_engine
```

The CatBoost C++ library is sparsely documented and is heavily dependent on other libraries which makes building as is very difficult. As such, it is required to be built separately.


```bash
# Move into CatBoost library
cd catboost
# Build via the provided build script
python3 build/build_native.py \
  --build-root-dir $(pwd)/catboost_native_build \
  --targets catboostmodel \
  --build-type Release \
  --parallel-build-jobs $(nproc)
```

Once CatBoost is built, we are free to build the inference engine from the provided CMakeLists.txt.

```bash
# Move back to cpp_inference_engine
cd ..
# Build engine
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

This will create three binaries. The first of interest is the `libemail_predictor_lib.a` static library archive. This is the core engine library and C++ SDK that can be brought across for other projects to link to. This library is linked to the GTest unit tests into the `test_email_predictor` binary. Running this will run the unit tests, all of these are expected to pass and encompass individual functionality tests as well as integration tests on held-out contacts.

```bash
# Run unit tests binary
./build/tests/test_email_predictor
```

Finally, the `email_predictor.cpython-312-x86_64-linux-gnu.so` shared object dynamic library contains the pybingings module for importing into python scripts. A python test in `cpp_inference_engine/tests/test_python_bindings_integration.py` can be found for an example of how to run. This test mimics the C++ integration test and will produce similar results. To import into your own script, the path must be made visible to Python.

```python
from pathlib import Path
import sys
# Import PyBinidings
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build" / "cpp"))
from email_predictor import (
    CatBoostEmailPredictionEngine,
    CatBoostTemplatePredictor,
)
```

These pybindings are what powers the REST API service. POST commands can be made to call these bindings which makes inferences. The Dockerfile in `cpp_inference_engine/Dockerfile` provides a containerized build and runtime for launching the service. The entry point is in `cpp_inference_engine/api/rest_api.py` which gives users an entrance point to interact with the service.

`cpp_inference_engine/scripts/build.sh` will build the container and attach it to `http://localhost:8000`. This serves both as an example for running as well as utility to run integration tests. From here, a couple test files exist to do integration and benchmarking tests. These can both be run by make the relevant build in the Makefile (`cpp_inference_engine/Makefile`).

```bash
# Make integration test
make test
```

## Input/Output

By running the `email_prediction.pipeline` pipeline, around ~49GB of training and test data will be generated into `db` in an SQL db file called `database.db`. 

Training in Colab will produce around ~93% Accuracy@1 and ~99% Recall@3 for the standard set and ~84% Accuracy@1 and ~98% Recall@3 in the complex set. 

In order to train the model, you will need to upload the .db file into `MyDrive/Colab Notebooks/database.db` in Google drive, otherwise you will have to change the path in the training notebook. 

You will also have to upload `val_std_ids.csv` and `val_comp_ids.csv` from `cpp_inference_engine/cpp/data` into Colab. 

You will have to do the same for `test_std_ids.csv` and `test_comp_ids.csv` from `cpp_inference_engine/tests/test_data`. 

The `email_prediction.pipeline` pipeline produces all of these files.

The produced .cbm files are then to be downloaded and placed into `cpp_inference_engine/cpp/model` at which point the integration tests can be run. 

For the most realistic results that mimic actual production environments, the regular build path for the C++ inference engine and then running the REST API integration test through the Makefile (as per the previous example) is recommend. This will achieve ~93% Accuracy@1 and ~99% Recall@3 with a latency of 3-5ms average query time.  

