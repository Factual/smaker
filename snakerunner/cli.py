import click
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader
import snakerunner

@click.command()
@click.argument('endpoint')
@click.option('--construct', '-c', default='Smakefile')
@click.option('--dryrun/--no-dryrun', is_flag=True, default=True)
@click.option('--quiet/--no-quiet', is_flag=True, default=False)
def main(endpoint, construct, dryrun, quiet):
    spec = spec_from_loader("Smakefile", SourceFileLoader("Smakefile", construct))
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)

    runners = []
    for val in dir(mod):
        obj = getattr(mod, val)
        if isinstance(obj, snakerunner.runner.SnakeRunner):
            runners.append(obj)

    matching = [sn for sn in runners if sn.endpoints.get(endpoint, None) != None]
    if len(matching) < 0: return 'Endpoint not found'
    if len(matching) > 1: return 'Duplicate endpoints found; ambiguous command'
    matching[0].run(endpoint, dryrun=dryrun, quiet=quiet)

if __name__=='__main__':
    main()

