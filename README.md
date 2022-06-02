# Ansible Collection - my_own_namespace.yandex_cloud_elk
### Prepare to launch ansible
1) You need install yc and create ssh 
   - [manual](https://cloud.yandex.com/en/docs/cli/operations/install-cli) cli 
   - [manual](https://cloud.yandex.ru/docs/managed-kubernetes/operations/node-connect-ssh) ssh
2) Set your properties VM in role single_task_role/tasks or defaults
   ```yml
   - name: create node-clickhouse
     my_own_module:
       name: "node-clickhouse"
       zone: "{{ zone }}"
       subnet_name: "{{ subnet_name }}"
       image_family: "{{ image_family }}"
       path_ssh: "{{ path_ssh }}"
       memory: 8
       count_cores: 4
   ```
3) If you need download roles in playbook folder
    ```bash
    ansible-galaxy install -r requirements.yml -p ./roles/ -f
    ```
4) Change default var in clickhouse role
   ```yaml
   clickhouse_listen_host:
     - "::"

   clickhouse_networks_default:
     - "::/0"
   ```
5) Install module 
   ```bash
   ansible-galaxy collection build --force
   ansible-galaxy collection install my_own_namespace-yandex_cloud_elk-2.0.0.tar.gz --force
   ```
6) Start playbook
   ```bash
   ansible-playbook site.yml ; ansible-playbook site.yml -i inventory.yml
   ```
7) After install check works 
 - http://<external_ip_lighthouse>/#http://<external_ip_clickhouse>:8123/
 - DATABASE logs TABLE access_log COLUMN message "My Test Message"