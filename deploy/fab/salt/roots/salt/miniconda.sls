miniconda-download:
  cmd.run:
    - name: |
        wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh#auto
    - unless: "test -e /home/ubuntu/Miniconda-latest-Linux-x86_64.sh"
    - user: ubuntu
    - cwd: /home/ubuntu

miniconda-install:
  cmd.run:
    - name: |
        chmod +x ./Miniconda-latest-Linux-x86_64.sh
        ./Miniconda-latest-Linux-x86_64.sh -b -f
    - unless: "test -e /home/ubuntu/miniconda2"
    - user: ubuntu
    - cwd: /home/ubuntu

conda-path-bashrc:
  file.append:
    - name: /home/ubuntu/.bashrc
    - text: 'export PATH="/home/ubuntu/miniconda2/bin:$PATH"'

conda-path:
  environ.setenv:
    - name: PATH
    - value: "/home/ubuntu/miniconda2/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games"
    - update_minion: True

echo-path:
  cmd.run:
    - name: "echo $PATH"

