bind = '0.0.0.0:8080'

accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

workers = 5
threads = 3

max_requests = 1000
max_requests_jitter = 100

timeout = 120

# Bound request headers and retain Gunicorn's strict HTTP parsing defaults.
limit_request_line = 4094
limit_request_fields = 50
limit_request_field_size = 8190

# This app does not use Gunicorn's control socket; avoid writing in the home
# directory when running with a read-only root filesystem.
control_socket_disable = True
