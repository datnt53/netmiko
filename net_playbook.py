#!/usr/bin/env python3.7

from netmiko import ConnectHandler
import datetime
import yaml
import sys
import configparser
from optparse import OptionParser
from ftplib import FTP
from termcolor import colored


usage = "usage: %prog [-i] [inventory_file] task_file"
parser = OptionParser(usage=usage)
parser.add_option("-i", "--inventory",
                  dest="g",
                  default="inventory",
                  help="Path to file inventory",
                  metavar="FILE")
#yaml_file = 'backup.yaml'
yaml_file = sys.argv[1:][2]
(options, args) = parser.parse_args()


def read_inventory(file):
    config_parser = configparser.RawConfigParser(allow_no_value=True)
    config_parser.read(file)
    global ip_result
    global vars_result
    list_sec = config_parser.sections()
    ip_result = {}
    vars_result = {}
    list_ip = []
    # Parse list IPs follow device
    for i in list_sec:
        if 'var' not in i:
            for j in range(0, len(config_parser.items(i))):
                ip = list(config_parser.items(i))[j][0]
                list_ip.append(str(ip))
            ip_result[i] = list_ip
        else:
            for k in range(0, len(config_parser.items(i))):
                vars_result[i] = {
                    'username': config_parser.get(i, 'username'),
                    'password': config_parser.get(i, 'password'),
                    'port': config_parser.get(i, 'port'),
                    'verbose': config_parser.get(i, 'verbose')}


def get_fpt(host, user, passwd, source, dest, file, verbose):
    ftp_server = FTP(host=host)
    ftp_server.login(user=user, passwd=passwd)
    local_path = '{dest}/{file}'.format(dest=dest, file=file)
    local = open(local_path, 'wb')
    if source is not None:
        ftp_server.cwd(source)
    output = ftp_server.retrbinary('RETR {file}'.format(file=file), local.write)
    if verbose == 'False':
        if 'Transfer complete' in output:
            print(colored('{ip} --> Get file {file} succeed!'.format(ip=host,
                                                                     file=file), 'magenta'))
        else:
            print(colored('{ip} --> Get file {file} failed!'.format(ip=host,
                                                                    file=file), 'magenta'))
    else:
        print(output)


def save_config(net_connect, time_template, ip, verbose):
    time_template = datetime.datetime.now().strftime(time_template)
    filename = 'config_{ip}_{time}.cfg'.format(ip=ip,
                                               time=time_template)
    bk_cmd = 'save {file}'.format(file=filename)
    output = colored('>>>>>>>>> {ip} --> Save config:\n'.format(ip=ip), 'yellow', attrs=['bold'])
    output += net_connect.send_command_timing(bk_cmd, strip_command=False, strip_prompt=False)
    while '[Y/N]' in output.split('\n')[-1]:
        output += net_connect.send_command_timing('Y',
                                                  strip_command=False,
                                                  strip_prompt=False)
    if verbose == 'False':
        if 'successfully' in output:
            print(colored('{ip} --> Saving config to {file} suceeded!'.format(ip=ip,
                                                                              file=filename), 'yellow', attrs=['bold']))
        else:
            print(colored('{ip} --> Saving config failed!'.format(ip=ip), 'yellow', attrs=['bold']))
    else:
        print(output)
    return filename


def backup_config(list_ip, type_b, username, password, port, verbose, **kwargs):
    a = {'False': False, 'True': True}
    for i in list_ip:
        device = {'device_type': type_b,
                  'ip': i,
                  'username': username,
                  'password': password,
                  'port': port,
                  'verbose': a[verbose]}
        connect = ConnectHandler(**device)
        filename = save_config(connect, kwargs['time_template'], i, verbose)
        if kwargs['getfile'] == 'Yes':
            get_fpt(i, kwargs['ftp_user'], kwargs['ftp_pass'], kwargs['source'], kwargs['dest'], filename, verbose)


def config_device(list_ip, type_d, username, password, port, verbose, **kwargs):
    a = {'False': False, 'True': True}
    for i in list_ip:
        device = {'device_type': type_d,
                  'ip': i,
                  'username': username,
                  'password': password,
                  'port': port,
                  'verbose': a[verbose]}
        connect = ConnectHandler(**device)
        output_cmd = ''
        output_file = ''
        err_cmd = ''
        err_file = ''
        for k in kwargs.keys():
            if k == 'command':
                cfg_cmd = kwargs['command'].split('||')
                output_cmd = connect.send_config_set(cfg_cmd, strip_command=False, strip_prompt=False)
                while 'Are you sure to commit' in output_cmd:
                    if 'Are you sure to commit' in output_cmd:
                        output_cmd += connect.send_command_timing('Y',
                                                                  strip_command=False,
                                                                  strip_prompt=False)
            if k == 'file':
                file = kwargs['file']
                output_file = connect.send_config_from_file(file, strip_command=False, strip_prompt=False)
                while 'Are you sure to commit' in output_file:
                    if 'Are you sure to commit' in output_file:
                        output_file += connect.send_command_timing('Y',
                                                                   strip_command=False,
                                                                   strip_prompt=False)
        if verbose == 'False':
            if output_cmd != '':
                if 'Error' in output_cmd:
                    for line in output_cmd.splitlines():
                        if 'Error' in line:
                            err_cmd += line + '; '
            if output_file != '':
                if 'Error' in output_file:
                    for line in output_file.splitlines():
                        if 'Error' in line:
                            err_file += line + '; '
            if 'command' in kwargs.keys():
                if err_cmd != '':
                    print(colored('{ip} --> [Command] Configuration failed ({error})'.format(ip=i,
                                                                                             error=err_cmd[:-2]), 'cyan', attrs=['bold']))
                else:
                    print(colored('{ip} --> [Command] Configuration succeed'.format(ip=i), 'cyan', attrs=['bold']))
            if 'file' in kwargs.keys():
                if err_file != '':
                    print(colored('{ip} --> [File] Configuration failed ({error})'.format(ip=i,
                                                                                          error=err_file[:-2]), 'cyan', attrs=['bold']))
                else:
                    print(colored('{ip} --> [File] Configuration succeed'.format(ip=i), 'cyan', attrs=['bold']))
        else:
            print(colored('{ip} --> [Config with command]\n{mess}'.format(ip=i,
                                                                          mess=output_cmd), 'cyan', attrs=['bold']))
            print(colored('{ip} --> [Config with file]\n{mess}'.format(ip=i,
                                                                       mess=output_file), 'cyan', attrs=['bold']))


def view_device(list_ip, type_d, username, password, port, verbose, **kwargs):
    a = {'False': False, 'True': True}
    for i in list_ip:
        device = {'device_type': type_d,
                  'ip': i,
                  'username': username,
                  'password': password,
                  'port': port,
                  'verbose': a[verbose]}
        connect = ConnectHandler(**device)
        view_cmd = kwargs['command'].split('||')
        output = ''
        for j in view_cmd:
            output += colored('>>>>>>>>> {cmd}\n'.format(cmd=j), 'magenta')
            output_tmp = connect.send_command(j)
            output += colored(output_tmp, 'green') + '\n'
        print(colored('{ip} --> Result of view command:'.format(ip=i), 'yellow', attrs=['bold']))
        print('{mes}'.format(mes=output))


if __name__ == '__main__':
    task = yaml.load(open(yaml_file))
    read_inventory(options.g)
    for e in range(0, len(task)):
        ip_service = ip_result[task[e]['hosts']]
        vars_service = vars_result['{sec}:vars'.format(sec=task[e]['hosts'])]
        device_type = task[e]['device_type']
        for f in range(0, len(task[e]['task'])):
            if 'backup' in task[e]['task'][f].keys():
                print(colored('TASK [{name}]'.format(name=task[e]['task'][f]['name']), 'red'))
                backup_config(ip_service,
                              device_type,
                              vars_service['username'],
                              vars_service['password'],
                              vars_service['port'],
                              vars_service['verbose'],
                              **task[e]['task'][f]['backup'])
            elif 'config' in task[e]['task'][f].keys():
                print(colored('TASK [{name}]'.format(name=task[e]['task'][f]['name']), 'red'))
                config_device(ip_service,
                              device_type,
                              vars_service['username'],
                              vars_service['password'],
                              vars_service['port'],
                              vars_service['verbose'],
                              **task[e]['task'][f]['config'])
            elif 'view' in task[e]['task'][f].keys():
                print(colored('TASK [{name}]'.format(name=task[e]['task'][f]['name']), 'red'))
                view_device(ip_service,
                            device_type,
                            vars_service['username'],
                            vars_service['password'],
                            vars_service['port'],
                            vars_service['verbose'],
                            **task[e]['task'][f]['view'])

