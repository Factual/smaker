# PA workflow helper / snakemake runner (smaker)

This package (at `training/smk/snakerunner`) makes it easier to write + run workflows:

+ Add an endpoint in the `Smakefile` file
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

## Pip package
Download:
```
pip3 install --extra-index-url http://pypi.corp.factual.com/pypi/ smaker
--trusted-host pypi.corp.factual.com
```

[Upload](https://wiki.corp.factual.com/pages/viewpage.action?spaceKey=ENG&title=Factual+Internal+PyPi+Server):
```
python3 setup.py sdist upload -r factual
```

