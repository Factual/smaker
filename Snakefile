workdir: config['workdir']

for module_path in config['modules'].values():
    include: module_path

rule all:
    input: config['targets']

