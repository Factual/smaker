import functools
from backports import tempfile
import snakemake
from snakerunner import path_gen
import os
import json

class SnakeRunner:
    def __init__(self, default_config, default_snakefile, cores=4):
        self.endpoints = {}
        self.default_snakefile = default_snakefile
        self.cores = cores
        self.configfile = default_config
        with open(default_config, 'r') as cf:
            self.default_config = json.load(cf)

    def generate_config(self, endpoint):
        globdict = globals()
        globdict['rule_targets'] = []
        globdict['data_targets'] = []
        globdict['required_params'] = []
        all_rule_targets = []
        all_data_targets = []
        all_req_params = set()

        global config
        config = self.default_config.copy()
        config_overrides = self.endpoints.get(endpoint, None)
        assert config_overrides != None, 'Endpoint %s not defined' % endpoint
 
        # must manually manage nested config dicts (this could be changed)
        nested_fields = ['params', 'modules']
        for field in nested_fields:
            if config_overrides.get(field, None) != None:
                config[field].update(config_overrides[field])
                del config_overrides[field]

        config.update(config_overrides)
        print(config)
        modules = config['modules']
        flat_config = config.copy()
        del flat_config['modules']
        assert config.get('sources', None) != None, 'Must provide data source namespace (sources field)'

        global workflow
        workflow = snakemake.workflow.Workflow(snakefile=self.default_snakefile, overwrite_config=flat_config)

        for name, snakefile in modules.items():
            code, linemap, rulecount = snakemake.parser.parse(snakefile)
            exec(compile(code, snakefile, "exec"), globdict)
            all_rule_targets += rule_targets
            all_data_targets += data_targets
            all_req_params |= set(required_params)

        path_gen.verify_config(config, required_params=list(all_req_params))
        rtargs, run_wildcards = path_gen.config_to_targets(all_rule_targets, config)
        dtargs, _ = path_gen.path_gen(data_targets, data_path, sources=config['sources'])

        config['run_wildcards'] = run_wildcards
        config['targets'] = rtargs + dtargs
        return config

    def run(self, endpoint, **kwargs):
        config = self.generate_config(endpoint).copy()
        config.update(kwargs)
        print(config)
        quiet = config.get('quiet', True)
        dryrun = config.get('dryrun', True)
        cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config = os.path.join(temp_dir, 'config.json')
            with open(temp_config, 'w+') as f:
                json.dump(config, f)
            if not quiet:
                print(json.dumps(config, indent=4, sort_keys=True))

            res = snakemake.snakemake(
                self.default_snakefile,
                configfile=temp_config,
                cores=self.cores,
                dryrun=True,
                quiet=quiet
            )
            assert res, 'Dry run failed'
            os.chdir(cwd)

            if not dryrun:
                res = snakemake.snakemake(
                    self.default_snakefile,
                    configfile=temp_config,
                    cores=self.cores,
                    dryrun=False
                )
                assert res, 'Workflow failed'
                os.chdir(cwd)

    def add_endpoint(self, name, params):
        assert self.endpoints.get(name, None) == None, 'Tried to duplicate endpoint: %s' % name
        self.endpoints[name] = params

    @classmethod
    def run_undefined_endpoint(cls, configfile, snakefile, workflow_opts, api_opts={'cores': 2}):
        sn = cls(configfile, snakefile)
        sn.add_endpoint('_undefined', workflow_opts)
        sn.run('_undefined', **api_opts)

