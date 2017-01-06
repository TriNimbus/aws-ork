python-pip:
  pkg.installed

aws_ork:
  pip.installed:
    - require:
      - pkg: python-pip

aws_ork.conf:
  file.managed:
    - name: /etc/aws_ork.conf
    - user: root
    - group: root
    - mode: 644
    - source: salt://files/aws_ork.conf
    - template: jinja

# SysV
aws-ork.init:
  file.symlink:
    - name: /etc/init.d/aws-ork
    - target: /usr/local/lib/python2.7/dist-packages/aws_ork/data/sys_init/aws_ork
    - force: true
    - user: root
    - group: root
    - mode: 755
    - require:
      - pip: aws_ork

# SystemD
/etc/init/aws-ork.conf:
  file.symlink:
    - user: root
    - group: root
    - mode: 644
    - target: /usr/local/lib/python2.7/dist-packages/aws_ork/data/systemd/aws_ork.conf
    - force: true
    - require:
      - pip: aws_ork

/etc/systemd/system/aws-ork.service:
  file.symlink:
    - target: /usr/local/lib/python2.7/dist-packages/aws_ork/data/systemd/aws_ork.service
    - force: true
    - user: root
    - group: root
    - mode: 644
    - require:
      - pip: aws_ork

aws-ork:
  service.running:
    - watch:
      - file: /etc/aws_ork.conf
    - require:
      - pip: aws_ork
      - file: aws_ork.conf
