/etc/nginx/sites-enabled/default:
  file.copy:
    - force: True
    - makedirs: True
    - source: /home/ubuntu/deploy/fab/dropq.conf

nginx:
  pkg:
    - installed
  service:
    - running
    - watch:
        - pkg: nginx
        - file: /etc/nginx/sites-enabled/default
