# Smaker Tutorial

## Table of Contents
1. [Setup](#setup)
2. [Background](#background)
3. [Hello World Pt1](#hello1)
4. [Hello World Pt2](#hello2)
5. [Hello World Pt3](#hello3)
6. [Single module data transform](#single-module)
7. [Multi-module example](#multi-module)


## Setup

+ Install `smaker`
+ Install `singularity`
+ Install `pandas`, `pyarrow`

Make sure your environment has `snakemake` and `smaker` loaded,
and the working directory contains the
`examples/` directory from this repo (should have `Snakefile`,
`Smakefile`, `simple/`, `hello_world`).

## Background

Smaker is setup to run "endpoints" statically defined in a "construct"
file (default=`Smakefile`). Those endpoints have four components:

1) The default `snakefile`

2) The default `configfile`

3) Config overrides (`params`) encoded as a python dictionary

4) Endpoints names (used to reference in cli)

Default `snakefile` and `configfile` are shared among endpoints
in a `SnakeRunner` class, which after instantiation collects endpoints
with a `Snakerunner.add_endpoint(name, params={})` method.

Constructs can hold several `SnakeRunner` class instances
with different defaults as long as endpoints aren't shared (currently).

Smaker can also run undefined endpoints by passing parameters at
run-time, which requires a separation of concerns for static and dynamic
config values.

We setup smaker to re-use generic collections of rules
(modules) as long as the minimal set of params are provided for each
module. So workflows are essentially ran with a variable number of
parameters, with each module unaware of what `wildcard` parameters
are defined (other than the ones it invokes).

That means two config fields are variable (nested):

1) Modules: a dictionary of paths to snakefiles (name:path)

2) Parameters (params): a dictionary of key/value pairs of
type `string: list` or `string: bool`.

Endpoints can override values in the default `params` dictionary.
Undedfined workflows can only override top-level config key/value pairs
outside of the `params` dict (currently).

## Hello World Pt 1

Check is your `smaker` and `snakerunner` deps are installed:
```
smaker list
```
This should output a list of pre-defined endpoints. If not, you are
either missing dependencies, in the wrong directory, or haven't
downloaded the full repo.

The list of endpoints output from `list` are defined in the `Smakefile`
by default. If you look in the smakefile you'll see the list of
endpoints, what `snakefile` and `configfile`s were used to create those
endpoints, and any override parameters.

Run one of the following:
```
smaker run hello
smaker run --no-dryrun hello
smaker run --quiet --no-dryrun hello
```

You should see descriptive output and a printed `Hello World!`.

A second `--no-dryrun` should indicate that the rule was already ran.

## Hello World Pt2

If you take a look at `examples/hello_world/Snakefile`, you should
notice two rules - one of which wasn't executed by the "hello" endpoint.

+ The first rule has an explicit output path.
+ We used that direct `Snakefile` as the default, preventing module
	generalization.
+ The second rule has a generic wildcard output that snakemake
	excluded from the DAG due to lack of informatiion.

The "hello_world" endpoint back in the `Smakefile` uses the top-level
`Snakefile` as its default. That `snakefile` dynamicaly loads modules
with an `include` directive, and populates its `all` directive with
absolute paths needed for snakemake to generalize the DAG and include
all of the rules that use wildcards. That generalization requires:

+ Creating a generic "wildcard specification" (labeled
	`run_wildcards` in config). This is generated based on the
	parameters passed by the user to an endpoint, and looks something
	like (refer to snakemake docs for expl):
```
{source}/distance{distance}_time{time}_{filter}_{skip_step_b}
```

+ Using that wildcard specification properly in rules so that we can
	combine modules that are unaware of each other's dependencies.

+ Tagging certain outputs with `FINAL` so that we can tell the snakemake
	DAG builder which rule(s) are the tip of our desired dependency
	tree.

If you take a look at `examples/hello_world/Snakefile` again, you will
notice the usage of the second two points above. The second rule uses a 
wildcard output with the spec injected with `run_wildcards`, and
specifies a file that the DAG builder should consider "final".

Creating the proper wildcard spec just requires the user to  provide
the necessary parameters for the wilcards they use. The 
`snakerunner/path_gen.py` file contains the logic for spec generation,
and the `snakerunner/runner.py` class invokes that logic given the
user-provided parameters. The "final" files are added in the top-level 
`Snakefile` class's `all` rule (at which point we can access all sub-`rules`
of the workflow).

To see that process in-action, run one of the following:
```
smaker run hello-world
smaker run hello-world --no-dryrun
smaker run hello-world --no-dryrun --quiet
```

As before, re-running the endpoint should be blocked by the output file 
existence.

As a final step, you can change the configs (or add additional
endpoints) to tweak the output. In the next step we'll run a dynamic
endpoint to change the `name` value via the command line.

## Hello World Pt3

If you added an endpoint to change the `say_hello` parameter in the last
step, it would look something like this:
```python
hello_noone_params = {
	'params': {
		'say_hello': True
	}
}
hello_world.add_endpoint('say_hello_noone', params=hello_noone_params)
```

Changing the name is also pretty easy:
```python
hello_world_params = {
	'params': {
		'say_hello': True
	},
	'name': 'World!'
}
hello_world.add_endpoint('say_hello_world', params=hello_world_params)
```

Invoking these two endpoints looks like:
```
smaker run say_hello_noone
smaker run say_hello_noone --no-dryrun
smaker run say_hello_world
smaker run say_hello_world --no-dryrun
```

You can always check if these ran by looking for the output files in
`/outputs`. The pathnames should help distinguish which have run.

You can also change the `name` (not the `params`) via the command line:
```
smaker fly --snakefile Snakefile --configfile hello_world/config.json - --name "World!"
smaker fly --snakefile Snakefile --configfile hello_world/config.json --no-dryrun - --name "World!"
```

Because the endpoints aren't named, you have to supply the default
config and snakefile. Also note the "-" to separate snakemake's API
parameters from the user workflow parameters.

Dynamically overwriting parameters requires capturing unnamed cli
options, which comes with some drawbacks.

1) Smaker prevents unnamed cli values with the `run` command.
Disparities between the recorded endpoint configs and run-time configs
is undesirable.

2) `--[option] [value]` pairs are expected to be space-separeted (right
now). An error message should log if you pass un-parseable configs.

3) If you didn't change the `source` value above, the `fly` target
outputs probably already exist, and the workflow won't re-run.

## Single module data transform

The `simple` folder contains a more complicated example of a
single-module workflow. The `simple_workflow` endpoint uses files in that 
folder to make a dataframe -> transform it with a python script ->
filter it with a bash command:
```
smaker run simple_workflow
smaker run simple_workflow --no-dryrun
smaker run simple_workflow --no-dryrun --quiet
```

A couple additional features in that `Snakefile`:

+ I used a `data_path` to cache the inital dataframe in case we change
	the parameters and want to re-run with the same data source.

+ We have several wildcard rules, but only one has the `params.FINAL`
	tag (as long as we can work backward from the final rule to the
	inputs, snakemake can generate the full DAG).

+ The dryrun output is considerably more verbose, because we specified
	several values for the `multiply` parameter.

+ We use Python inline to make the dataframe, which works because the
	Snakefile is a superset of Python. We had to cast the `output`
	directive to a string to extract the value into a Python primitive,
	but otherwise the code changes little from normal Python. In the
	`hello_world` example we could access `wildcards.say_hello` as a
	string directly, so there are some syntax inconsistencies to be
	aware of.

+ We exec'd a Python script in a shell command, and visually organized the
	call by splitting it into multiple lines. Refer to
	the snakemake docs for more ways to run scripts.

That `Snakefile` is populated with comments to help explain more
details regarding that example.

## Multi-module example

We made smaker to avoid rewriting rules everytime we swap or
A/B test components of our system. For example, if we use the same ML-trainer
with several pre-processers, we want to use the same training code each
time.

The previous examples could have been written with explicit rules and ran
with the standard Snakemake file. This example shows how we can combine
several modules to take advantage of that generalization.

We replicate the ML example's structure in the `complex` folder. There
are three pre-processors, one trainer, and one evaluator module. The
modules don't actually do anything useful here, they just take unique
parameters to showcase module flexibility.

We use three endpoints to run each preprocessor with the trainer +
evaluator. (In this example we can't run
`fly`, because the `modules` and `params` config keys are nested, 
and can't be set by the cli). The config doesn't have to be empty here,
but we leave it like that anyways. The endpoints are defined in
`Smakefile`: "complex_prepA", "complex_prepB", complex_prepC".

The executed code is trivial, but the setup is kind of complex even with
one rule per file. If you run the endpoints you'll see that each uses a
different set of parameters unique to the modules being run. The
organization for those parameters is in the `Smakefile` in Python. The
content of the rules can be customized, as is shown in the other example
workflows.

## Takeaways

Hopefully the `complex` folder shows how our helper functions can help
avoid code-duplication at the cost of some organizational overhead. The
`hello_world` and `simple` examples try to work upwards to bridge the gap
between standard snakefiles and our additions.

In our use-case, "static data, variable workflow", modules can include
dozens of rules. We often need to add new parameters for testing
new processing types, models, evaluators, and even unexpected in-between
or add-on modules. So for us, the feature-richness of Snakemake combined
with the flexibility of smaker satisfies our workflow needs.

Other use-cases might benefit from different
modularizations, or plain Snakefiles if the use-cases is "variable data,
static processing."

