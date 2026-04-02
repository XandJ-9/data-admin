"""Generate Nginx config for local production simulation."""
import sys

nginx_dir = sys.argv[1] if len(sys.argv) > 1 else "/Users/xujia/nginx"
dist_dir = sys.argv[2] if len(sys.argv) > 2 else "/Users/xujia/MyCode/data-admin/frontend/dist"
port = sys.argv[3] if len(sys.argv) > 3 else "9090"

conf = f"""worker_processes  1;

error_log  logs/error.log;
pid        logs/nginx.pid;

events {{
    worker_connections  1024;
}}

http {{
    include       mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  logs/access.log  main;

    sendfile        on;
    keepalive_timeout  65;

    gzip  on;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    upstream dataadmin_backend {{
        server 127.0.0.1:8000;
        keepalive 32;
    }}

    server {{
        listen       {port};
        server_name  localhost;

        client_max_body_size 100M;

        # frontend static files
        location /data-admin/ {{
            alias {dist_dir}/;
            try_files $uri $uri/ /data-admin/index.html;
            expires 1d;
            add_header Cache-Control "public, immutable";
        }}

        # backend API
        location /data-api/ {{
            proxy_pass http://dataadmin_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            proxy_read_timeout 30s;
        }}

        # WebSocket support (Web Terminal)
        location /ws/ {{
            proxy_pass http://dataadmin_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 3600s;
        }}

        error_page   500 502 503 504  /50x.html;
        location = /50x.html {{
            root   html;
        }}
    }}
}}
"""

output_path = f"{nginx_dir}/conf/nginx.conf"
with open(output_path, 'w') as f:
    f.write(conf)
print(f"Nginx config written to {output_path}")
