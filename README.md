# PA workflow helper / snakemake runner (smaker)

## Motivation
This module-based workflow allows for grouping generic snakemake
rules that can be:

1) flexibly partitioned and interchanged

2) without having to manually manage rule targets

3) while still benefitting from the static snakemake DAG checking

This architecture is instended for large batch-style jobs that 
change often. Similarly, this sort of setup impedes cron or static work
better suited for Jenkins/Airflow.

How PA uses modules to organize our machine learning setup:

+ Preprocess modules: input raw data, output test/train data
+ Train modules: input train data, output model/model weights/model params
+ Evaluate modules: input test data and model, output statistics/plots

All of our work fits within those categories, and new
modules with the same pattern input/output can be swapped 
without disrupting/rewriting other steps. For example, new pre-processors with different 
parameter requirements can be added without other modules needing to be
aware of those changes.

Optional/supported:
+ Additional helper modules
+ working outside of the ML structure

The inter-module dependencies enforce an organization that 
only makes sense for repetitively changing workflows, however. At a
certain level of customization, workflows should just be written 
as standalone Snakefiles.

## Download

```
pip3 install --extra-index-url http://pypi.corp.factual.com/pypi/ smaker --trusted-host pypi.corp.factual.com
```

## Usage

+ Create/find existing construct file with `SnakeRunner` (default is
    `Smakefile` currently in `training/smk`)
+ Add an endpoint with parameters
+ invoke `smaker [endpoint_name]` in the docker container

An example `Smakefile` looks like:
```python
import snakerunner
sn = snakerunner.runner.SnakeRunner(default_snakefile='Snakefile.base', default_config='conf/original')
sn.add_endpoint(name='original_engine_workflow', params={'source':['engine']})
```

If you setup the endpoints correctly, the following will list the
available rules:
```
sudo docker -E training/smk/docker_run_workflow.sh smaker list
```

The `run` command currently defaults to a dryrun. The `--quiet` flag
disables rule printing if you just want to statically check if an
endpoint is configured to run the correct rules.
```
sudo docker -E training/smk/docker_run_workflow.sh smaker run original_engine_workflow --quiet
```
This command runs a workflow:
```
sudo docker -E training/smk/docker_run_workflow.sh smaker run original_engine_workflow --no-dryrun
```

Open the container in interactive mode to use the executable directly:
```
sudo docker -E training/smk/docker_run_workflow.sh /bin/bash

smaker list
smaker run original_engine_workflow --quiet
smaker run original_engine_workflow --quiet --no-dryrun
```

## Executable  organization:
The `SnakeRunner` class does the following:

+ Generate configfile given defaults + function args
+ Organize and aggregate submodule rules

The `cli.py` script takes care of parsing the `Smakefile` file to
provide and call endpoints.

## Modules:
The top-level snakefile iteratively includes `modules` specified in the config. 
Each module uses generic path names to specify rules, but are otherwise
just standard collections of snakemake rules. Because the rule paths are
generic, you must specify some top level variables that are built at
run-time:

+ `rule_targets`: Basename targets for each DAG
+ `data_targets`: Data can live outside of the workflow output
    directories for caching/reuse between endpoints. (`source` fields indicate
    intra-workflow caching that is not shared between endpoints).
+ `required_params`: Wildcard variables that are used in modules, and
    thereby must be specified in top-level config.
+ `required_flags`: Wildgard boolean flags that are used in modules, and
    thereby must be specified in top-level config.

## Other notes:
The `path_gen.py` file takes care of dynamically generating the target
paths for rules depending on which preprocess, train and evaluate
modules are used. The runner assumes target basenames are specified as
`rule_targets` and `data_targets` within respective modules (small
feedbackward necessary to include full target paths at top-level
config).

Refer to the [snakemake
API](https://snakemake.readthedocs.io/en/stable/api_reference/snakemake.html)
for the full breadth of options you can add to runs.

## Pip package management
```
[Upload](https://wiki.corp.factual.com/pages/viewpage.action?spaceKey=ENG&title=Factual+Internal+PyPi+Server):
```
python3 setup.py sdist upload -r factual
```

