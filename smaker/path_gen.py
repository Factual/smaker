import numpy as np
import os

def config_to_targets(targets, config):
    return path_gen(targets, config['output_path'], parameters=config.get('params', {}),
                    sources=config.get('sources', []))

def path_gen(targets, output_path, parameters={}, sources=[]):
    assert(parameters != None)
    assert(sources != None)

    partials = ['']
    template = ''
    flags = []
    opts = []
    for k, vals in parameters.items():
        assert '_' not in k, "Cannot put hyphens or underscores in parameter namei: %s" % k
        assert '-' not in k, "Cannot put hyphens or underscores in parameter namei: %s" % k
        if isinstance(vals, bool):
            flags.append((k,vals))
            continue
        opts.append((k,vals))

    if len(opts) > 0:
        for k,vals in sorted(opts):
            partials = [subl for l in [[t+'%s%s_'%(k,v) for v in vals] for t in partials] for subl in l]
            template += '%s{%s}_'%(k,k)

    if len(flags) > 0:
        flags = sorted(flags)
        fpartials = '_'.join(['%s'%f if v else 'no-%s'%f for f,v in flags])
        partials = [p + fpartials for p in partials]
        template += '_'.join(['{%s}'%f for f,v in flags])
    else:
        partials = [t[:-1] for t in partials]
        template = template[:-1]

    if len(sources)>0:
        full_paths = [os.path.join(output_path, s, p, t) for t in targets for p in partials for s in sources]
        template = os.path.join('{source}', template)
    else:
        # full_paths = [os.path.join(output_path, p, t) for t in targets for p in partials]
        print('Source must be defined. Path-collapsing intentionally not supported at this time')
        raise

    return full_paths, os.path.normpath(template)

def verify_config(config, required_params=[]):
    valid = np.all([p in config['params'].keys() for p in required_params])
    assert valid, 'Missing required params :\nparams: %s\nconfig params: %s' % (required_params, config['params'])
    assert len(config['modules'].items()) > 0, 'Config does not specify any modules to run'

