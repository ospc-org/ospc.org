create-environment:
  cmd.run:
    - name: |
        conda env remove --name aei_dropq --yes ;
        conda create --name aei_dropq python=2.7 --yes
    - user: ubuntu
    - cwd: /home/ubuntu
    - env:
       - PATH: "/home/ubuntu/miniconda2/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games"
    - require:
      - sls: miniconda


install-into-environment:
  cmd.run:
    - name: |
        source activate aei_dropq &&
        conda install --channel ospc pytest mock taxcalc btax ogusa pandas xlrd bokeh flask requests greenlet --yes &&
        pip install celery retrying eventlet redis supervisor plotly requests-mock requests
    - user: ubuntu
    - cwd: /home/ubuntu
    - env:
       - PATH: "/home/ubuntu/miniconda2/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games"
    - require:
      - cmd: create-environment
