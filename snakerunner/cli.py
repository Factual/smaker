import click
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader
import snakerunner

@click.command()
@click.argument('cmd')
@click.argument('endpoint', required=False)
@click.option('--construct', '-c', default='Smakefile')
@click.option('--dryrun/--no-dryrun', is_flag=True, default=True)
@click.option('--quiet/--no-quiet', is_flag=True, default=False)
def main(cmd, endpoint, construct, dryrun, quiet):

    # this does: "import construct as construct_module"
    spec = spec_from_loader("Smakefile", SourceFileLoader("Smakefile", construct))
    construct_module = module_from_spec(spec)
    spec.loader.exec_module(construct_module)

    runners = []
    for val in dir(construct_module):
        obj = getattr(construct_module, val)
        if isinstance(obj, snakerunner.runner.SnakeRunner):
            runners.append(obj)

    if cmd == 'list':
        for r in runners:
            for e in r.endpoints: print(e)
        return
    elif cmd == 'run':
        matching = [sn for sn in runners if sn.endpoints.get(endpoint, None) != None]
        assert len(matching) != 0, 'Endpoint not found: %s' % endpoint
        assert len(matching) == 1, 'Endpoint found in multiple runners: %s' % endpoint
        matching[0].run(endpoint, dryrun=dryrun, quiet=quiet)
    else:
        print('Command not recognized')

if __name__=='__main__':
    main()

