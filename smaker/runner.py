from backports import tempfile
import functools
import json
import os
import snakemake
from smaker import path_gen

def pretty_dump(blob):
    return json.dumps(blob, indent=4, sort_keys=True)

class SnakeRunner:
    def __init__(self, default_config, default_snakefile, cores=4):
        self.endpoints = {}
        self.default_snakefile = default_snakefile
        self.cores = cores
        self.configfile = default_config
        with open(default_config, 'r') as cf:
            self.default_config = json.load(cf)

    def _merge_configs(self, base, overrides, nested_fields=['params', 'modules', 'sources']):
        for field in nested_fields:
            if overrides.get(field, None) != None:
                collection = overrides[field]
                if isinstance(collection, dict):
                    if base.get(field, None) == None: base[field] == {}
                    base[field].update(overrides[field])
                    del overrides[field]
                elif isinstance(collection, (tuple, list, set)):
                    if base.get(field, None) == None: base[field] == []
                    base[field] += list(collection)
                    del overrides[field]
        base.update(overrides)
        return base

    def run(self, endpoint, api_opts):
        base_config = self.default_config.copy()
        overrides = self.endpoints.get(endpoint, None)
        assert overrides != None, 'Endpoint %s not defined' % endpoint

        workflow_config = self._merge_configs(base_config, overrides)
        workflow_config['final_paths'], workflow_config['run_wildcards'] = path_gen.config_to_targets([''], workflow_config)

        print('API options set:\n%s' % pretty_dump(api_opts))
        dryrun = api_opts.pop('dryrun', True)
        cwd = os.getcwd()

        if not api_opts.get('quiet', True):
            print('Workflow opts:\n%s' % pretty_dump(workflow_config))

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config = os.path.join(temp_dir, 'config.json')
            with open(temp_config, 'w+') as f: json.dump(workflow_config, f)
            api_opts['configfile'] = temp_config

            res = snakemake.snakemake(self.default_snakefile, dryrun=True, **api_opts)
            assert res, 'Dry run failed'
            os.chdir(cwd)

            if not dryrun:
                res = snakemake.snakemake(self.default_snakefile, dryrun=False, **api_opts)
                assert res, 'Workflow failed'
                os.chdir(cwd)

    def add_endpoint(self, name, params):
        assert self.endpoints.get(name, None) == None, 'Tried to duplicate endpoint: %s' % name
        self.endpoints[name] = params

    @classmethod
    def run_undefined_endpoint(cls, configfile, snakefile, workflow_opts={}, api_opts={'cores': 2}):
        print('Running with dynamic workflow opts:\n%s' % pretty_dump(workflow_opts))
        sn = cls(configfile, snakefile)
        sn.add_endpoint('_undefined', workflow_opts)
        sn.run('_undefined', api_opts)

