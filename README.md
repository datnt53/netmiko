# Net_Playbook: Automation config/backup/view for Network Device
Net_Playbook is python script to config/backup/view Network Device. Features:
* It works for Python 3.7
* Supporting list vendors: Following Netmiko Library: `https://pypi.org/project/netmiko/`

## Packages:
* python3.7
* netmiko
* ftplib

## Using Net_Playbook:
USAGE: net_playbook.py [-i] [inventory_file] task_file

* `inventory` with list IPs and information to connect to Devices. By default, Net_playbook get `config.ini` in path of script. You can change path to config with option `-i`.

* `task.yml` with list tasks with template file `test.yaml`:

    `backup` with 2 action `save` and `get` (only support Huawei Device with enabled ftpserver)
    
    `config` with 2 option `command` and `from_file`.
    
    `view` with `command`

## Output:

Output of each task will print to screen.