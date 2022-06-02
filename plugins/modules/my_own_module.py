#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
import os.path
import json

__metaclass__ = type

DOCUMENTATION = r'''
---
module: my_test

short_description: This is my test module

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This is my longer description explaining my test module.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        zone=dict(type='str', required=True),
        subnet_name=dict(type='str', required=True),
        image_family=dict(type='str', required=True),
        path_ssh=dict(type='str', required=True),
        memory=dict(type='str', required=False),
        count_cores=dict(type='str', required=False),
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

    command_disk_size = ' '
    command_core_count = ' '
    command_mem_size = ' '
    if module.params['disk_size']:
        command_disk_size = ' --create-disk size=' + module.params['disk_size'] + 'GB'
    if module.params['count_cores']:
        command_core_count = ' --cores ' + module.params['count_cores']
    if module.params['memory']:
        command_mem_size = ' --memory ' + module.params['memory'] + 'GB'

    command = 'yc compute instance create \
                    --name ' + module.params['name'] + ' \
                    --zone ' + module.params['zone'] + ' \
                    --network-interface subnet-name=' + module.params['subnet_name'] + ',nat-ip-version=ipv4 \
                    --create-boot-disk image-folder-id=standard-images,image-family=' + module.params['image_family'] + ' \
                    --metadata-from-file ssh-keys=' + module.params['path_ssh'] + command_mem_size + command_core_count + command_disk_size

    search_name_instance = ' | ' + module.params['name']
    os.system('yc compute instance list | grep ' + module.params['name'] + ' > list_instance.txt')
    with open("list_instance.txt", "r") as f:
        if search_name_instance in f.read():
            result['changed'] = False
            result['message'] = module.params['name'] + ' is already set'
            module.exit_json(**result)
        else:
            file_log_json = 'log_'+module.params['name']+'.json'
            os.system(command + ' --format json > ' + file_log_json)
    os.system('rm list_instance.txt')
    file_instance_list = 'list_' + module.params['name'] + '.txt'
    os.system("yc compute instance list | sed -n '1p;2p;3p' > "+file_instance_list)
    os.system('yc compute instance list | grep ' + module.params['name'] + ' >> '+file_instance_list)
    os.system("yc compute instance list | sed  -e  '1{$q;}' -e '$!{h;d;}' -e x >> "+file_instance_list)
    with open(file_instance_list, "r") as f:
        result['message'] = f.read()

    data = json.loads(open(file_log_json).read())
    external_ip = data["network_interfaces"][0]["primary_v4_address"]["one_to_one_nat"]["address"]

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

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
