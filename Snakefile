import os
from snakerunner.utils import scrape_error_logs, scrape_final_targets

workdir: config['workdir']

for module_path in config['modules'].values():
    include: module_path

print([ os.path.join(o,targ) for o in config['final_paths'] for targ in scrape_final_targets(rules) ])
rule all:
    input: [ os.path.join(o,targ) for o in config['final_paths'] for targ in scrape_final_targets(rules) ]

onerror:
    start = '%s\nPrinting error log:' % ''.join(['=']*100)
    end = '\nEnd of error log\n%s' % ''.join(['=']*100)
    for error_log in scrape_error_logs(log):
        shell('echo "%s" && echo "%s\n" && cat %s && echo "%s"' % (start, error_log, error_log, end))

