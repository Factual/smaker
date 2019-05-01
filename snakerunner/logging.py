import re

def scrape_error_logs(log):
    post = ' \(check log file\(s\) for error message'
    error_regex = 'log: ([^\s]*\.log) \(check log file\(s\) for error message'
    log_regex = '[^\s]*\.log'

    print(''.join(['=']*100))
    with open(log, 'r+') as log_file:
        for line in log_file:
            for match in re.finditer(error_regex, line, re.S):
                for f in re.finditer(log_regex, match.group(), re.S):
                    error_log = f.group()
                    print('Printing failure log %s:\n' % error_log)
                    shell('cat %s' % error_log)
                    print('\nEnd of failure log')
    print(''.join(['=']*100))

