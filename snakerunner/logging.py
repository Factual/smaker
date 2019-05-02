import re

def scrape_error_logs(log):
    post = ' \(check log file\(s\) for error message'
    regex = 'log: ([^\s]*\.log) \(check log file\(s\) for error message'
    file_regex = '[^\s]*\.log'

    with open(log, 'r+') as log_file:
        for line in log_file:
            for match in re.finditer(regex, line, re.S):
                for f in re.finditer(file_regex, match.group(), re.S):
                    yield f.group()

