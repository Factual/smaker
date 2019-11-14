from backports import tempfile
import functools
import json
import os
import snakemake
import smaker
from tqdm import tqdm
import copy
from omegaconf import OmegaConf
import omegaconf

class TqdmExtraFormat(tqdm):
    "Style change copied from tqdm documentation"
    @property
    def format_dict(self):
        d = super(TqdmExtraFormat, self).format_dict
        total_time = d["elapsed"] * (d["total"] or 0) / max(d["n"], 1)
        d.update(total_time=self.format_interval(total_time) + " in total")
        return d

all_template = """\
import os
from smaker.utils import scrape_error_logs, scrape_final_targets

rule all:
    input: [ os.path.join(o,targ) for o in config['final_paths'] for targ in scrape_final_targets(rules) ]

onerror:
    start = '%s\\nPrinting error log:' % ''.join(['=']*100)
    end = '\\nEnd of error log\\n%s' % ''.join(['=']*100)
    for error_log in scrape_error_logs(log):
        shell('echo "%s" && echo "%s\\n" && cat %s && echo "%s"' % (start, error_log, error_log, end))
"""

class SnakeRunner:
    def __init__(self, default_config, default_snakefile, cores=4):
        self.endpoints = {}
        self.cores = cores
        self.configfile = default_config
        self.default_snakefile = os.path.abspath(default_snakefile)
        self.default_config = OmegaConf.load(default_config)

    def run(self, endpoint, api_opts):
        dryrun = api_opts.pop('dryrun', True)
        cwd = os.getcwd()

        config_overrides = self.endpoints.get(endpoint, None)
        assert config_overrides !=  None, 'Endpoint %s not defined' % endpoint
        if isinstance(config_overrides, dict): config_overrides = [config_overrides]
        assert len(config_overrides) > 0, "No configs found: %s" % endpoint

        config_overrides = [c if isinstance(c, omegaconf.dictconfig.DictConfig) else OmegaConf.create(c) for c in config_overrides]
        subworkflow_configs = [OmegaConf.merge(self.default_config, c) for c in config_overrides]

        with tempfile.TemporaryDirectory() as temp_dir:
            config_paths = [os.path.abspath(os.path.join(temp_dir, 'config%s.json' % idx)) for idx in range(len(subworkflow_configs))]
            for config, path in zip(subworkflow_configs, config_paths):
                if config.get('params') != None:
                    config['final_paths'], config['run_wildcards'] = smaker.config_to_targets([''], config)
                config.save(path)

            pbar = TqdmExtraFormat(config_paths, ascii=True , bar_format="{total_time}: {percentage:.0f}%|{bar}{r_bar}")
            for i, cpath in enumerate(pbar):
                res = snakemake.snakemake(self.default_snakefile, configfile=cpath, dryrun=dryrun, **api_opts)
                assert res, 'Workflow failed'
                os.chdir(cwd)

    def add_endpoint(self, name, params):
        assert self.endpoints.get(name, None) == None, 'Tried to duplicate endpoint: %s' % name
        self.endpoints[name] = params

    @classmethod
    def run_undefined_endpoint(cls, configfile, snakefile, workflow_opts={}, api_opts={'cores': 2}):
        sn = cls(configfile, snakefile)
        sn.add_endpoint('_undefined', workflow_opts)
        sn.run('_undefined', api_opts)

