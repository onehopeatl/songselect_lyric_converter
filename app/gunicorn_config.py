bind = '0.0.0.0:8080'

accesslog = '-'
# access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

workers = 5
threads = 3

max_requests = 1000
max_requests_jitter = 100

timeout = 120
