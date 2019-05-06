# Smaker - Flexible Snakemake workflows

## Install
You'll need:
+ A `python3` environment
+ The dependencies included in the following package:
```
pip3 install --extra-index-url http://pypi.corp.factual.com/pypi/ smaker --trusted-host pypi.corp.factual.com
```

Or if the PyPi package is up:
```
pip3 install smaker
```

Or clone the repo and install:
```
git clone https://github.com/max-hoffman/smaker.git
pip3 install -e smaker
```

## Tutorial
See [tutorial here](examples/tutorial.md) for examples.

## Background
[Snakemake](https://snakemake.readthedocs.io/en/stable/) is a great
workflow tool for data science pipelines that change infrequently.
The workflow DSL language is clear, concise, supports in-line Python,
arbitrary parameter grid-search, and features a robust DAG-builder 
and execution engine that make debugging/running/scaling workflows easy. The docs
are helpful, the source code is clear, the creator actively gives
helpful responses to user questions and bugs.

There are many other features, but the main downside is the "pipelines that change
infrequently" stickler. Most of the time this software is used for
genomics pipelines that championed clarity, debuggability and computational
throughput at the cost of workflow flexibility.

We tried to expand the feature set of Snakemake to support workflows
that change frequently. Our primary use-case is machine learning pipelines
that add steps and parameters often. It was suprisingly painful to
A/B test with the standard Snakemake library due to the amount of copied
code and hard-coded paths: basically a new Snakefile for every change.
Alternate systems lacked the clarity and debuggability that we liked about
Snakemake, however, so we used Python's flexibilty to try and work-around
that limitation.

## Motivation
This library supports Snakemake workflows composed of
rules grouped into generic modules. Small generalizations of
target paths allow modules to be:

1) Flexibly combined and interchanged

2) Without having to manually manage wildcard inconsistencies between
modules

3) While still benefitting from the static snakemake DAG checking

This architecture is intended for large batch-style jobs that 
change often. The overhead likely impedes cron or static work
better suited for standard Snakemake files/Airflow.

Our machine learning modularization:

+ Preprocess: input raw data, output test/train data
+ Train: input train data, output model/model weights/model params
+ Evaluate: input test data and model, output statistics/plots

All of our work fits within those categories, and new
modules with the same input/output pattern can be swapped 
without disrupting/rewriting other steps. For example, new pre-processors with different 
parameter requirements can be added without other modules needing to be
aware of those changes. New modules can be written separately and
 appended without breaking other workflows with overlapping rule sets.

To re-iterate, the inter-module dependencies enforce an organization that 
best-suits quickly iterating workflows. At a
certain level of customization, workflows should just be written 
as standalone Snakefiles.

## Usage

+ Create/find existing construct file with `SnakeRunner` (default is
    `Smakefile` currently in `training/smk`)
+ Add an endpoint with parameters
+ invoke `smaker [endpoint_name]`

An example `Smakefile` looks like:
```python
import snakerunner
sn = snakerunner.runner.SnakeRunner(default_snakefile='Snakefile.base', default_config='conf/original')
sn.add_endpoint(name='original_engine_workflow', params={'source':['engine']})
```

A few sample commands are shown below. Refer to the
[tutorial](examples/tutorial.md) for a more thorough breakdown
```
smaker --help

smaker list

smaker run --quiet [endpoint]
smaker run --no-dryrun [endpoint]

smaker fly --configfile CONFIG --snakefile SNAKEFILE - [options]

```

This library is a wrapper for the [snakemake
API](https://snakemake.readthedocs.io/en/stable/api_reference/snakemake.html). 
Refer to its docs for more context regarding the execution engine.


## Architecture

Overall:

+ Everything is written in Python except for Snakemake rules, which
    still have to adhere to their own Python superset.
+ The construct file (default=`Smakefile`) collects endpoint
    descriptions using instances of the `SnakeRunner` class.
+ The `cli` script scrapes the construct for endpoints, and invokes
    user commands.
+ The `path_gen` script generates wildcards for generically written
    `Snakefiles`.
+ The `runner` class interfaces with the Snakemake API to launch
    executors.

The default `Snakefile` in this repo is required for generalizing
between modules. The custom `include` and `all` directives are how this
library injects workflow flexibility, which the user has to be aware of
when writing rules. Respectively, paths with wildcards have to use
what's currently called `run_wildcards` in place of a general output
path, and "DAG-tip" rules have to be marked with `params.FINAL =
[path]` so the scheduler can generate the DAG tree given whichever
wildcards are required by the collection of modules.

Refer to the [tutorial](examples/tutorial.md) for a walkthrough
for a better description.

## Modules:
The top-level snakefile iteratively includes `modules` specified in the config. 
Each module uses generic path names to specify rules, but are otherwise
just standard collections of snakemake rules. Because the rule paths are
generic, we added some fields to wrangle rules into the proper
Snakemake format at runtime:

+ `output_path` - Top-level directory where results are written
    Individual workflow runs have unqiue directories inside
    this output path.
+ `data_path` - Outputs can be cached in a data directory separate from 
    standard workflow outputs. This is intended for computationally expensive steps whose
    outputs are shared between endpoints.
+ `sources` - ML projects can run pipelines with different
    data sets, and this field can provide a layer of
    caching if certain modules' outputs are used repetitively by
    downstream modules within the same endpoint.

These fields can be ignored; they are just there to help
organize where results are written.

## Improvements

+ Set parameters and modules from the command line. I think the
    `--add-module` flag works, but I have not spent time testing it. Adding
    param setting would follow the same structure as I currently have for
    modules.

+ Chain endpoints into uber-DAGs. So instead of having the executor
    launch with one config, we would separate the run step into: a)
    iteratively creating configs for each endpoint requested, and then
    b) injecting (config, snakefile, workdir) tuples into a new
    snakefile that includes all subworkflows. The backend implementation
    is straightforward and the executor will work all the same;
    figuring out how the user should specify
    endpoints on the front-end is harder. Override `add_endpoint` to
    take a list of previously defined endpoints? Pass multiple endpoint
    arguments to the `run` command via the CLI?

+ Add either unit or integration tests. The example projects are already
    integrations tests sort of - if the DAG-builder succeeds and makes
    the expected dependency graph then smaker has successfully generated wildcards
    and combined modules. Changes to the confiig structure or
    subworkflow support would require updating those examples. Unit tests
    that run `path_gen` and the log/target scrapers would be useful.

+ Support a broader range of
    [Snakemake API options](https://snakemake.readthedocs.io/en/stable/api_reference/snakemake.html).
    The CLI script needs to individually support these to correcly
    type-cast before passing them to the snakemake library.


## Pip package management
[Upload](https://wiki.corp.factual.com/pages/viewpage.action?spaceKey=ENG&title=Factual+Internal+PyPi+Server):
```
python3 setup.py sdist upload -r factual
```
