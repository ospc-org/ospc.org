run-supervisord:
  cmd.run:
    - name: |
        source activate aei_dropq &&
        /home/ubuntu/miniconda2/envs/aei_dropq/bin/python /home/ubuntu/miniconda2/envs/aei_dropq/bin/supervisord -c /home/ubuntu/deploy/fab/supervisord.conf
    - user: ubuntu
    - cwd: /home/ubuntu
    - env:
       - PATH: "/home/ubuntu/deploy:/home/ubuntu/miniconda2/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games"
    - require:
      - sls: conda-environment
      - sls: redis-server
    - unless: test -e /home/ubuntu/supervisor.sock

reload-supervisord:
  cmd.run:
    - name: |
        source activate aei_dropq &&
        /home/ubuntu/miniconda2/envs/aei_dropq/bin/python /home/ubuntu/miniconda2/envs/aei_dropq/bin/supervisorctl -c /home/ubuntu/deploy/fab/supervisord.conf reload
    - user: ubuntu
    - cwd: /home/ubuntu
    - env:
       - PATH: "/home/ubuntu/deploy:/home/ubuntu/miniconda2/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games"
    - require:
      - sls: conda-environment
      - sls: redis-server
