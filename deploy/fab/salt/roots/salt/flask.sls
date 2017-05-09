flask-running:
  supervisord.running:
    - name: flask
    - restart: True
    - user: ubuntu
    - conf_file: /home/ubuntu/deploy/fab/supervisord.conf
    - bin_env: /home/ubuntu/miniconda2/envs/aei_dropq/bin/supervisorctl
    - require:
        - sls: conda-environment
        - sls: redis-server
        - sls: supervisor

