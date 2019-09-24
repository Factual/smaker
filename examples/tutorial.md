# Smaker Tutorial

## Table of Contents
1. [Setup](#setup)
2. [Background](#background)
3. [Hello World Pt1](#hello1)
4. [Hello World Pt2 (Wildcards)](#hello2)
5. [Hello World Pt3 (CLI parameters)](#hello3)
6. [Single-module example](#single-module)
7. [Multi-module example](#multi-module)
8. [Takeaways](#takeaways)

## Setup

+ Install `smaker`
+ Clone this repo

Cd into the `examples/` directory (should have `Snakefile`,
`Smakefile`, `simple/`, `hello_world`).

## Background

Smaker is setup to run "endpoints" statically defined in a "construct"
file (default=`Smakefile`). 1 endpoint = 1 workflow = 1 snakemake DAG. 
Endpoints have four components:

1) The default `snakefile`

2) The default `configfile`

3) Config overrides (`params`) encoded as a python dictionary

4) Endpoint names (used to reference workflows via CLI)

Default `snakefile` and `configfile` are shared among endpoints
in a `SnakeRunner` class, which collect similarly structured endpoints
through `Snakerunner.add_endpoint(name, params={})`.

Constructs can hold several `SnakeRunner` class instances
with different defaults as long as endpoints aren't shared (currently).

Smaker can also run undefined workflows (no endpoint) by passing parameters at
run-time (`fly` command show in [part 3](#hello3).

Smaker can re-use generic collections of rules
(modules) as long as the required params are provided for each
module (each module is unaware of what `wildcard` parameters
are defined globally).

That design choice necessetates two variable (nested) config fields:

1) Modules: a dictionary of paths to snakefiles (name:path)

2) Parameters (params): a dictionary of key/value pairs of
type `string: list` or `string: bool`.

Endpoints can override values in the default `params` dictionary.
Undedfined workflows can only override top-level config key/value pairs
outside of the `params` dict (currently).

## Hello World Pt 1 <a name="hello1"></a>

Check if `smaker` was installed:
```
smaker list
```
This should output a list of pre-defined endpoints. If not, you are
either missing dependencies, in the wrong directory, or haven't
downloaded the full repo.

The list of endpoints output from `list` are defined in the `Smakefile`
by default. If you look in the smakefile you'll see the list of
endpoints, what `snakefile` and `configfile` values were used to create those
endpoints, and any override parameters.

Run one of the following:
```
smaker run -e hello
smaker run --no-dryrun -e hello
smaker run --quiet --no-dryrun -e hello
```

You should see descriptive output and a printed `Hello World!`.

A second `--no-dryrun` should indicate that the rule was already ran.

## Hello World Pt2 - Add Wildcards <a name="hello2"></a>

If you take a look at `hello_world/Snakefile`, you should
notice two rules - one of which was not executed by the "hello" endpoint.

+ The first rule has an explicit output path (i.e. no wildcards), so
    snakemake identifies the rule on its own.
+ The second rule has a generic wildcard output that snakemake
	excluded from the DAG due to lack of informatiion

The "hello_world" endpoint back in the `Smakefile` uses the top-level
`Snakefile` as its default, while the "hello" endpoint did not.
That unique snakefile dynamicaly loads modules
with an `include` directive, and populates its `all` directive with
absolute paths needed for snakemake to generalize the DAG to include
wildcard-dependent rules. That generalization requires:

+ We must create a generic "wildcard specification" (labeled
	`run_wildcards` in config) specific to the given
    endpoint/workflow. This is generated based on the
	parameters passed by the user, and looks something
	like this (refer to snakemake docs for more information about
    wildcards):
```
{source}/name{name}_{say_hello}
```

+ Me must use the wildcard specification properly in rules 
    so that modules can be unaware of global wildcards.

+ We must tag certain outputs as `FINAL` to help the snakemake 
	DAG builder generate the full list of rule dependencies for every
    combination of input parameters (i.e. which rule(s) are
    the tip of our desired dependency trees)

If you take a look at `examples/hello_world/Snakefile` again, you will
notice the usage of the second two points above in the second
"hello_world" rule.

+ The rule uses the wildcard spec in its `output` directive.
+ The rule uses the params directive to specifiy a file that the 
    DAG builder will use to build a dependency tree (after smaker
    expands it with wildcards).

Creating the wildcard spec requires the user to provide
the necessary parameters for the modules used in an endpoint. The 
`snakerunner/path_gen.py` file contains the logic for spec generation,
and the `snakerunner/runner.py` class invokes that logic given the
user-provided parameters. The "final" files are added in the top-level 
`Snakefile` class's `all` rule (at which point we can access all sub-`rules`
of the workflow).

All of that information is printed to the console when dry-running an 
endpoint, so you can see what the snakemake API is running. If you
forget to set a parameter, snakemake should throw a wildcard not found
exception.

To see that process in-action, run one of the following:
```
smaker run -e hello-world
smaker run -e hello-world --no-dryrun
smaker run -e hello-world --no-dryrun --quiet
```

Re-running those endpoint should be prevented by the output files 
created in the first run.

As a final step, you can change the configs (or add additional
endpoints) to tweak the outputs. In the next step we'll run a dynamic
endpoint to change the `name` value via the command line.

## Hello World Pt3 - Set parameters via CLI <a name="hello3"></a>

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
smaker run -e say_hello_noone
smaker run -e say_hello_noone --no-dryrun
smaker run -e say_hello_world
smaker run -e say_hello_world --no-dryrun
```

You can always check if these ran by looking for the output files in
`/outputs`. The pathnames should help distinguish which have run.

You can also change the `name` (not the `params`) via the command line:
```
smaker fly --snakefile Snakefile --configfile hello_world/config.json --name "World!"
smaker fly --snakefile Snakefile --configfile hello_world/config.json --no-dryrun --name "World!"
```

Because the endpoints aren't named, you have to supply the default
config and snakefile. Also note the "-" to separate snakemake's API
parameters from the user workflow parameters.

Dynamically overwriting parameters requires capturing unnamed cli
options, which comes with some drawbacks.

1) Smaker prevents unnamed cli values when using the `run` command.
Disparities between recorded endpoint configs and run-time configs
is undesirable.

2) `--[option] [value]` pairs are expected to be space-separeted (right
now). An error message should log if you pass un-parseable configs.

3) If you did not change the `source` value above, the `fly` target
outputs could already exist, and the workflow won't re-run.

## Single-module Example <a name="single-module"></a>

The `simple` folder contains a more complicated example of a
single-module workflow. The `simple_workflow` endpoint 
makes a dataframe -> transform it with a python script ->
filters it with a bash command:
```
smaker run -e run_simple
smaker run -e run_simple --no-dryrun
smaker run -e run_simple --no-dryrun --quiet
```

A couple additional features in that `Snakefile`:

+ I used a `data_path` to cache the inital dataframe in case we change
	the parameters and want to re-run with the same data source.

+ We have several wildcard rules, but only one has the `params.FINAL`
	tag (as long as we can work backward from the final rule to the
	inputs, snakemake can generate the full DAG).

+ The dryrun output is more verbose, because we specified
	several values for the `multiply` parameter. That can be muted with
    `--quiet`.

+ We inlined Python to make the dataframe, which works because the
	Snakefile is a superset of Python. We had to cast the `output`
	directive to a string to extract a Python primitive,
	but otherwise the looks like normal Python. On the other hand, in the
	`hello_world` example we accessed `wildcards.say_hello` as a
	string directly because the `shell` directive allows it.
    So there are some snakemake syntax peculiarities to be aware of.

+ We exec'd a Python script in a shell command, and visually organized the
	call by splitting it into multiple lines. Refer to
	the snakemake docs for more ways to run scripts.

That `Snakefile` is populated with comments to help explain more
details regarding that example.

## Multi-module Example <a name="multi-module"></a>

We made smaker to avoid rewriting rules everytime we swap or
A/B test components of our system. For example, if we use the same ML-trainer
with several pre-processers, we want to use the same training code each
time.

The previous examples could have been written with explicit rules and ran
with the standard Snakemake file. This example shows how we can combine
several modules to take advantage of smaker's generalization. 

We replicated the ML example's structure in the `complex` folder. There
are three pre-processors, one trainer, and one evaluator module. The
modules don't actually do anything useful here, they just take unique
parameters to showcase module flexibility.

We use three endpoints to run each preprocessor with the trainer +
evaluator. (In this example we can't run
`fly`, because the `modules` and `params` config keys are nested, 
and can't be set by the cli. The config did not have to be empty here,
but we left it like that anyways.)

The endpoints are defined in
`Smakefile`: "complex_prepA", "complex_prepB", complex_prepC". The
paremeter organization is all in Python.

If you run the endpoints, you will see see each uses a
different set of parameters unique to the preprocessor being run.
The content of rules can be customized, as is shown in the other example
workflows.

If we had not used smaker with this example, we would have needed to write three train and three
evalute snakefiles to pair with each preprocessor. A normal workflow
could include dozens of rules per module, several different training
styles, and last-minute add-on modules for glue-code, monitoring or 
post-processing. Every tweak introduces a
mutliplier of complexity and an increasing number of
files to be copied and maintatined. Smaker lets you generalize and
to avoid code-duplication.

## Takeaways

Hopefully the `complex` folder shows how smaker can help
avoid code-duplication at the cost of some organizational overhead. The
`hello_world` and `simple` examples try to show the differences
between standard snakefiles and our additions, albeit for trivial
workflows.

In our use-case, "static data, variable workflow", modules can include
dozens of rules. We want to be able to test new preprocessor, 
models, evaluators, and even unforeseen special cases. 
So for us, the feature-richness of Snakemake combined
with the flexibility of smaker satisfies our workflow needs.

Other use-cases might benefit from different
modularizations, or plain Snakefiles if the main use-cases is "variable data,
static processing." It all comes down to a trade-off of immediate
clarity at the cost of flexibility vs. generalization with upfront
organizational overheads.

