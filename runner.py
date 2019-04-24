import functools
import snakemake
from . import path_gen
import os
import json

class SnakeRunner:
    def __init__(self, default_config, default_snakefile):
        self.endpoints = {}
        self.default_snakefile = default_snakefile
        self.cores = 4
        self.configfile = default_config
        with open(default_config, 'r') as cf:
            self.default_config = json.load(cf)

    def run(self, endpoint):
        globdict = globals()
        globdict['rule_targets'] = []
        globdict['data_targets'] = []
        all_rule_targets = []
        all_data_targets = []

        global config
        config = self.default_config.copy()
        config_overrides = self.endpoints.get(endpoint, None)
        assert config_overrides != None, 'Endpoint %s not defined' % endpoint
        config.update(config_overrides)
        modules = config['modules']
        flat_config = config.copy()
        del flat_config['modules']

        global workflow
        workflow = snakemake.workflow.Workflow(snakefile=self.default_snakefile, overwrite_config=flat_config)

        for name, snakefile in modules.items():
            code, linemap, rulecount = snakemake.parser.parse(snakefile)
            exec(compile(code, snakefile, "exec"), globdict)
            all_rule_targets += rule_targets
            all_data_targets += data_targets

        path_gen.verify_config(config, required_params=[], required_flags=[])
        rtargs, run_wildcards = path_gen.config_to_targets(all_rule_targets, config)
        dtargs, _ = path_gen.path_gen(data_targets, data_path, sources=config['sources'])

        config_overrides['run_wildcards'] = run_wildcards
        config_overrides['targets'] = rtargs + dtargs

        cwd = os.getcwd()
        res = snakemake.snakemake(
            self.default_snakefile,
            configfile=self.configfile,
            config=config_overrides,
            cores=self.cores,
            dryrun=True
        )
        assert res, 'Dry run failed'
        os.chdir(cwd)

#        res = snakemake.snakemake(
            #self.default_snakefile,
            #configfile=self.default_config,
            #config=config_overrides,
            #cores=self.cores,
            #dryrun=False
        #)
#        assert res, 'Workflow failed'
        #os.chdir(cwd)

    def add_endpoint(self, name, params):
        self.endpoints[name] = params

#sn = SnakeRunner()

#@sn.endpoint
#def job1(conf):
    #conf.params = {}
    #conf.name = 'job1_name'

#@click.command()
#@click.argument(endpoint)
#def main(endpoint):
   #sn.run(endpoint)

#if __name__=='__main__':
    #main()

