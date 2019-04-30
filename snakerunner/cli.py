from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader
import click
import os
import snakerunner

def list_endpoints(runners):
        for r in runners:
            for e in r.endpoints: print(e)

def run_endpoint(endpoint, runners, **kwargs):
    matching = [sn for sn in runners if sn.endpoints.get(endpoint, None) != None]
    assert len(matching) != 0, 'Endpoint not found: %s' % endpoint
    assert len(matching) == 1, 'Endpoint found in multiple runners: %s' % endpoint
    matching[0].run(endpoint, **kwargs)

def run_on_the_fly(extra_modules, **kwargs):
    workflow_opts, api_opts = filter_api_options(**kwargs)
    if len(extra_modules) > 0:
        workflow_opts['modules'].update({{os.path.dirname(os.path.basename(mod)): mod} for mod in extra_modules if os.path.isfile(mod)})

    configfile = api_opts.pop('configfile', None)
    snakefile = api_opts.pop('snakefile', None)
    assert configfile != None, 'Must pass default config to run non-endpoint workflows'
    assert snakefile != None, 'Must pass snakefile to run non-endpoint workflows'
    snakerunner.runner.SnakeRunner.run_undefined_endpoint(configfile, snakefile, workflow_opts, api_opts)

def filter_api_options(**kwargs):
    smk_opts = set(['report','listrules','list_target_rules','cores','nodes','local_cores','resources','cluster_sync','drmaa','drmaa_log_dir','jobname','immediate_submit',
      'config','configfile','config_args','workdir','targets','dryrun','touch','forcetargets','forceall','forcerun','until','omit_from','prioritytargets',
      'stats','printreason','printshellcmds','debug_dag','printdag','printrulegraph','printd3dag','nocolor','quiet','keepgoing','cluster','cluster_config',
      'standalone','ignore_ambiguity','snakemakepath','lock','unlock','cleanup_metadata','cleanup_conda','cleanup_shadow','force_incomplete',
      'ignore_incomplete','list_version_changes','list_code_changes','list_input_changes','list_params_changes','list_untracked','list_resources','summary',
      'archive','delete_all_output','delete_temp_output','detailed_summary','latency_wait','wait_for_files','print_compilation','debug','notemp',
      'keep_remote_local','nodeps','keep_target_files','allowed_rules','jobscript','greediness','no_hooks','overwrite_shellcmd','updated_files','log_handler','keep_logger',
      'max_jobs_per_second','max_status_checks_per_second','restart_times','attempt','verbose','force_use_threads','use_conda',
      'use_singularity','singularity_args','conda_prefix','list_conda_envs','singularity_prefix','shadow_prefix','create_envs_only','mode',
      'wrapper_prefix','kubernetes','kubernetes_envvars','container_image','default_remote_provider','default_remote_prefix','assume_shared_fs',
      'cluster_status', 'export_cwl', 'snakefile'])
    kwarg_keys = set(kwargs.keys())
    api_opts = { opt: kwargs.pop(opt) for opt in (smk_opts & kwarg_keys) }
    return kwargs, api_opts

@click.command(name='smaker', context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
))
@click.argument('cmd')
@click.argument('endpoint', required=False)
@click.option('--construct', '-c', default='Smakefile')
@click.option('--add-module', '-m', required=[], multiple=True)
@click.pass_context
def main(context, cmd, endpoint, construct, add_module):

    # this does: "import construct as construct_module"
    spec = spec_from_loader("Smakefile", SourceFileLoader("Smakefile", construct))
    construct_module = module_from_spec(spec)
    spec.loader.exec_module(construct_module)

    # collect generic parameters passed at run-time (in `--opt val` format)
    if cmd == 'fly': context.args = [endpoint] + context.args
    kwarg_overrides = { context.args[i][2:]: context.args[i+1] for i in range(0, len(context.args), 2) }
    print(kwarg_overrides)

    # scrape snakefile for runner class instances
    runners = []
    for val in dir(construct_module):
        obj = getattr(construct_module, val)
        if isinstance(obj, snakerunner.runner.SnakeRunner):
            runners.append(obj)

    if cmd == 'list': list_endpoints(runners)
    elif cmd == 'run': run_endpoint(endpoint, runners, **kwarg_overrides)
    elif cmd == 'fly': run_on_the_fly(add_module, **kwarg_overrides)
    else:
        print('Command not recognized')

if __name__=='__main__':
    main()

