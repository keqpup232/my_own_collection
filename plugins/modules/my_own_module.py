#!/usr/bin/python

# Copyright: (c) 2022, Ivan Gavryushin <keqpup232@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
'''

EXAMPLES = r'''
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
import os.path
from subprocess import PIPE, Popen
import json

def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        zone=dict(type='str', required=True),
        subnet_name=dict(type='str', required=True),
        image_family=dict(type='str', required=True),
        path_ssh=dict(type='str', required=True),
        memory=dict(type='str', required=False),
        cpu_count=dict(type='str', required=False),
        disk_size=dict(type='str', required=False)
    )

    result = dict(
        changed=True,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    if (module.params['zone'] == 'ru-central1-a') or (module.params['zone'] == 'ru-central1-b') or (module.params['zone'] == 'ru-central1-c'):
        pass
    else:
        result['changed'] = False
        result['message'] = module.params['zone'] + ' zone is incorrect'
        module.exit_json(**result)

    if module.params['memory'].isnumeric():
        pass
    else:
        result['changed'] = False
        result['message'] = module.params['memory'] + ' memory is incorrect'
        module.exit_json(**result)

    if module.params['cpu_count'].isnumeric():
        pass
    else:
        result['changed'] = False
        result['message'] = module.params['cpu_count'] + ' cpu_count is incorrect'
        module.exit_json(**result)

    if module.params['disk_size'].isnumeric():
        pass
    else:
        result['changed'] = False
        result['message'] = module.params['disk_size'] + ' disk_size is incorrect'
        module.exit_json(**result)

    command_disk_size = ' '
    command_core_count = ' '
    command_mem_size = ' '
    if module.params['disk_size']:
        command_disk_size = ' --create-disk size=' + module.params['disk_size'] + 'GB'
    if module.params['cpu_count']:
        command_core_count = ' --cores ' + module.params['cpu_count']
    if module.params['memory']:
        command_mem_size = ' --memory ' + module.params['memory'] + 'GB'

    command = 'yc compute instance create \
                    --name ' + module.params['name'] + ' \
                    --zone ' + module.params['zone'] + ' \
                    --network-interface subnet-name=' + module.params['subnet_name'] + ',nat-ip-version=ipv4 \
                    --create-boot-disk image-folder-id=standard-images,image-family=' + module.params['image_family'] + ' \
                    --metadata-from-file ssh-keys=' + module.params['path_ssh'] + command_mem_size + command_core_count + command_disk_size


    res_cmd_instances = Popen('yc compute instance list --format json'.split(), stdout=PIPE).stdout.read().strip().decode('utf-8')
    list_instances = json.loads(res_cmd_instances)
    for instance in list_instances:
        if instance['name'].strip() == module.params['name'].strip():
            result['changed'] = False
            result['message'] = module.params['name'] + ' is already set'
            module.exit_json(**result)

    with open("list_instances.json", "a") as f:
        f.write(str(list_instances))

    file_log_json = 'log_'+module.params['name']+'.json'
    os.system(command + ' --format json > ' + file_log_json)
    data = json.loads(open(file_log_json).read())
    external_ip = data["network_interfaces"][0]["primary_v4_address"]["one_to_one_nat"]["address"]

    # FEEDBACK: С инвентори задумка забавная, жалко только, что файлик формируется не на стандартном месте.
    # - Про какое стандартное место идет речь?

    # Но можно пойти ещё дальше, сгенерировать json с готовым динамическим инвентори,
    # который можно получить в ansible через register, тогда с файликами можно не возиться вообще
    # - Не очень понял идею, вместо файлов формировать json или dict, который по итогу выплюнет один файл инвентори?
    # - Или модуль как то будет передать данные в ansible через register.
    # - Можно питоном запросить у яндекса списки всех машин через $ yc compute instance list --format json что впринципе есть в переменной res_cmd_instances
    # - А потом что? Создавать inventory и дополнять его? Модуль вызывается по сути столько раз, сколько виртуалок создается.
    # - Идея по сути таже получилась

    if module.params['name']=='node-clickhouse':
        with open("inventory.yml", "a") as f:
            f.write('---\nclickhouse:\n  hosts:\n    ' + module.params['name'] + ':\n      '+'ansible_host: ' + external_ip + '\n')
        with open("vector.toml", "a") as f:
            f.write('[sources.my_source_id]\ntype = "syslog"\naddress = "0.0.0.0:514"\nmode = "tcp"\npath = "/usr/lib/systemd/system/syslog.socket"\n\n'
                    '[sinks.my_sink_id]\ntype = "clickhouse"\ninputs = [ "my_source_id" ]\nendpoint = "http://'+ external_ip +':8123"\ndatabase = "logs"\n'
                    'table = "access_logs"\nskip_unknown_fields = true')
    elif module.params['name']=='node-vector':
        with open("inventory.yml", "a") as f:
            f.write('vector:\n  hosts:\n    ' + module.params['name'] + ':\n      '+'ansible_host: ' + external_ip + '\n')
    elif module.params['name']=='node-lighthouse':
        with open("inventory.yml", "a") as f:
            f.write('lighthouse:\n  hosts:\n    ' + module.params['name'] + ':\n      '+'ansible_host: ' + external_ip + '\n')


    result['message'] = 'vm is created successful'
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
