import numpy as np
import os

def config_to_targets(targets, config):
    return path_gen(targets, config['output_path'], parameters=config.get('params', {}),
                    flags=config.get('flags', {}), sources=config.get('sources', []))

def path_gen(targets, output_path, parameters={}, flags={}, sources=[]):
    assert(parameters != None)
    assert(flags != None)
    assert(sources != None)

    partials = ['']
    template = ''
    for k, vals in parameters.items():
        partials = [subl for l in [[t+'%s%s_'%(k,v) for v in vals] for t in partials] for subl in l]
        template += '%s{%s}_'%(k,k)

    for f in flags:
        partials = [subl for l in [[t+'%s_'%v for v in flags[f]] for t in partials] for subl in l]
        template += '{%s}_'%f

    partials = [t[:-1] for t in partials]
    template = template[:-1]

    if len(sources)>0:
        full_paths = [os.path.join(output_path, s, p, t) for t in targets for p in partials for s in sources]
        template = os.path.join('{source}', template)
    else:
        full_paths = [os.path.join(output_path, p, t) for t in targets for p in partials]

    return full_paths, template

def verify_config(config, required_params=[], required_flags=[]):
    valid = np.all([p in config['params'].keys() for p in required_params] + [f in config['flags'].keys() for f in required_flags])
    assert valid, 'Missing required params or flags:\nparams: %s\nflags: %s\nconfig params: %s\nconfig flags: %s' % (required_params, required_flags, config['params'],  config['flags'])
    assert len(config['modules'].items()) > 0, 'Config does not specify any modules to run'

