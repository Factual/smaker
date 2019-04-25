# PA workflow helper / snakemake runner (smaker)

## Motivation
This module-based workflow was intended to allow for grouping generic snakemake
rules that can be:

1) flexibly partitioned and interchanged

2) without having to manually manage rule targets

3) while still benefitting from the static snakemake DAG checking

This architecture supports large batch-style jobs that 
change often. Similarly, this sort of setup impedes cron or static work
that better suited for Jenkins/Airflow.

An example of module restrictions that support a machine learning setup:

+ Preprocess modules: input raw data, output test/train data
+ Train modules: input train data, output model/model weights/model params
+ Evaluate modules: input test data and model, output statistics/plots

Most of my general work fits within those categories, and new
modules with the same pattern input/output can be swapped 
without disrupting other steps. New pre-processors with different
parameters can be added without changing any other step.

Nothing stops you from including additional helper modules, or working outside of that 
structure, but you have to be aware of inter-module dependencies and
make sure that structure helps rather than hinders you. At a
certain point of customization, workflows should just be standalone
Snakefiles executed the regular way.

## Download

```
pip3 install --extra-index-url http://pypi.corp.factual.com/pypi/ smaker
--trusted-host pypi.corp.factual.com
```

## Usage

+ Create/find existing construct file with `SnakeRunner` class
+ Add an endpoint with parameters
+ invoke `smaker [endpoint_name]` in the docker container

An example endpoint looks like:
```
import snakerunner
sn = snakerunner.runner.SnakeRunner(default_snakefile='Snakefile.base',
default_config='conf/original')
sn.add_endpoint(name='original_engine_workflow', params={'source':
['engine'])
```

```
sudo docker -E training/smk/docker_run_workflow.sh smaker
original_engine_workflow --dryrun
sudo docker -E training/smk/docker_run_workflow.sh smaker
original_engine_workflow

```

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

