import click
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader
import json
import os
from snakerunner.runner import SnakeRunner

def list_endpoints(runners):
    return [ print(e) for r in runners for e in r.endpoints ]

def run_endpoint(endpoint, runners, api_opts):
    matching = [sn for sn in runners if sn.endpoints.get(endpoint, None) != None]
    assert len(matching) != 0, 'Endpoint not found: %s' % endpoint
    assert len(matching) == 1, 'Endpoint found in multiple runners: %s' % endpoint
    matching[0].run(endpoint, api_opts)

def run_on_the_fly(snakefile, configfile, extra_modules, workflow_opts, api_opts):
    workflow_opts['modules'] = { os.path.dirname(os.path.basename(mod)): mod for mod in extra_modules if os.path.isfile(mod) }
    SnakeRunner.run_undefined_endpoint(configfile, snakefile, workflow_opts, api_opts)

@click.command(name='smaker', context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.argument('cmd')
@click.argument('endpoint', required=False)
@click.option('--construct', '-c', default='Smakefile')
@click.option('--add-module', '-m', required=[], multiple=True)
@click.option('--snakefile', type=str, required=False)
@click.option('--configfile', type=str, required=False)
@click.option('--dryrun', type=bool, default=False)
@click.option('--quiet', type=bool, default=True)
@click.option('--cores', type=int, default=2)
@click.pass_context
def main(context, cmd, endpoint, construct, add_module, snakefile, configfile, dryrun, quiet, cores):

    # "import construct as construct_module"
    spec = spec_from_loader("Smakefile", SourceFileLoader("Smakefile", construct))
    cmodule = module_from_spec(spec)
    spec.loader.exec_module(cmodule)

    # generic workflow options (`--[option] [value]` format)
    if cmd == 'fly': context.args = [endpoint] + context.args
    workflow_opts = { context.args[i][2:]: context.args[i+1] for i in range(0, len(context.args), 2) }
    api_opts = { 'cores': cores, 'quiet': quiet, 'dryrun': dryrun }

    runners = [ getattr(cmodule, val) for val in dir(cmodule) if isinstance(getattr(cmodule, val), SnakeRunner) ]

    if cmd == 'list': list_endpoints(runners)
    elif cmd == 'run': run_endpoint(endpoint, runners, api_opts)
    elif cmd == 'fly': run_on_the_fly(snakefile, configfile, add_module, workflow_opts, api_opts)
    else: print('Command not recognized')

if __name__=='__main__':
    main()

