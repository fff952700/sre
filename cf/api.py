import config
import threading
import copy

# 创建锁
data_lock = threading.Lock()


class CloudflareAPI:
    def __init__(self, header):
        self.header = header

    def add_rulesets(self, zone):
        with data_lock:
            # 为每个域名创建独立的规则配置副本（关键修复）
            current_rule_mapping = copy.deepcopy(config.RULE_DATA_MAPPING)

            # 获取规则集
            rulesets_url = f"{config.BASE_URL}/zones/{zone['id']}/rulesets"
            ruleset_result = self.header.send_request("GET", rulesets_url, zone["name"])

            ruleset_data = ruleset_result.json().get("result", [])

            for rulesets in ruleset_data:
                phase = rulesets["phase"]
                print(f"domain {zone['name']} phase {phase}")

                # 使用当前域名的独立配置副本
                if phase in current_rule_mapping:
                    print(f"Processing phase: {phase}")
                    ruleset_id_url = f"{config.BASE_URL}/zones/{zone['id']}/rulesets/{rulesets['id']}"
                    ruleset_info = self.header.send_request("GET", ruleset_id_url, zone["name"])
                    # 获取规则集详细信息
                    ruleset_info_data = ruleset_info.json().get("result", {})
                    rule_descriptions = ruleset_info_data.get("rules", [])
                    # 获取期望的规则描述
                    expected_desc = current_rule_mapping[phase]["data"]["rules"][0].get("description")

                    rule_found = False
                    for rule_desc in rule_descriptions:
                        # 如果规则已经存在，跳过
                        if rule_desc.get("description") == expected_desc:
                            print(f"Rule '{expected_desc}' already exists in phase '{phase}'")
                            rule_found = True
                            # 找到后跳出内层循环
                            break

                    if not rule_found:
                        print(f"Adding new rule '{expected_desc}'")
                        rules_url = f"{config.BASE_URL}/zones/{zone['id']}/rulesets/{rulesets['id']}/rules"
                        self.header.send_request("POST", rules_url, zone["name"],
                                                 data=current_rule_mapping[phase]["data"]["rules"][0])

                    # 仅修改当前域名的配置副本
                    current_rule_mapping[phase].pop("exists", None)

            # 检查并创建新规则集（使用当前域名的配置副本）
            for phase, rule_info in current_rule_mapping.items():
                if "exists" in rule_info:
                    print(f"Creating new ruleset for {zone['name']}: {rule_info.get('rule_name')}")
                    self.header.send_request("POST", rulesets_url, zone["name"], data=rule_info["data"])

    def purge_cache(self, zone):
        url = f"{config.BASE_URL}/zones/{zone['id']}/purge_cache"
        data = {"purge_everything": True}
        response = self.header.send_request("POST", url, zone["name"], data=data)
        if response:
            print(f'Cache purged for {zone["name"]}')
        else:
            print(f'Failed to purge cache for {zone["name"]}')

    def delete_dns(self, zone):
        list_dns_url = f"{config.BASE_URL}/zones/{zone['id']}/dns_records"
        dns_resp = self.header.send_request("GET", list_dns_url, zone["name"])
        if dns_resp is None:
            return

        for record in dns_resp.json().get('result'):
            delete_dns_url = f"{config.BASE_URL}/zones/{zone['id']}/dns_records/{record['id']}"
            resp = self.header.send_request("DELETE", delete_dns_url, zone["name"])
            if resp.status_code == 200:
                print(f"{record['name']} deleted")

    def add_dns(self, zone):
        dns_url = f'{config.BASE_URL}/zones/{zone["id"]}/dns_records'
        for name in config.DNS_HOST:
            dns_data = {
                "comment": "Domain verification record",
                "name": name,
                "proxied": True,
                "settings": {},
                "tags": [],
                "ttl": 3600,
                "content": config.DNS_VALUE,
                "type": config.DNS_TYPE
            }
            self.header.send_request("POST", dns_url, zone["name"], data=dns_data)

    def add_init_param(self, zone):
        for param in config.INIT_PARAM:
            url = f'{config.BASE_URL}/zones/{zone["id"]}/settings/{param}'
            result = self.header.send_request("GET", url, zone["name"]).json().get('result')
            if result:
                param_key = result.get('id')
                param_value = result.get('value')

                # 使用映射来处理一些简单的设置
                updates = {
                    "tls_1_3": {'value': 'zrt', 'check': param_value != "zrt"},
                    "ipv6": {'value': 'off', 'check': param_value != 'off'},
                    "rocket_loader": {'value': 'on', 'check': param_value != 'on'},
                    "min_tls_version": {'value': '1.1', 'check': param_value != '1.1'},
                }

                if param_key in updates and updates[param_key]['check']:
                    self.header.send_request("PATCH", url, zone["name"], data={'value': updates[param_key]['value']})

                elif param_key == "security_header":
                    self.set_security_header(zone)

    def set_security_header(self, zone):
        hsts_data = {
            'value': {
                'strict_transport_security': {
                    'enabled': True,
                    'max_age': 15552000,
                    'include_subdomains': True,
                    'preload': True,
                    'nosniff': True,
                }
            }
        }
        hsts_url = f'{config.BASE_URL}/zones/{zone["id"]}/settings/security_header'
        self.header.send_request("PATCH", hsts_url, zone["name"], data=hsts_data)

    def add_while(self, while_list, ip_list):
        account_id = self.get_account_id().json().get('result')[0].get('id')
        if not account_id:
            return
        target_list = self.get_target_list(account_id, while_list)
        if not target_list:
            return
        existing_ips = self.header.get_account_items(
            f"{config.BASE_URL}/accounts/{account_id}/rules/lists/{target_list['id']}/items")
        if existing_ips is None:
            return
        add_item = self.prepare_ips_to_add(ip_list, existing_ips)
        if not add_item:
            print("没有新的IP需要添加")
            return
        self.add_ips_to_list(account_id, target_list['id'], add_item)

    def get_account_id(self):
        account_url = f"{config.BASE_URL}/accounts"
        account_id = self.header.send_request("GET", account_url, "accountId")
        if not account_id:
            print("未能获取账号ID")
        return account_id

    def get_target_list(self, account_id, while_list):
        lists_url = f'{config.BASE_URL}/accounts/{account_id}/rules/lists'
        list_resp = self.header.send_request("GET", lists_url, "lists_id")
        if list_resp.status_code != 200:
            print(f"获取列表失败: {list_resp.status_code}")
            return None
        return next((item for item in list_resp.json().get('result') if item['name'] == while_list[0]), None)

    def prepare_ips_to_add(self, ip_list, existing_ips):
        # 创建一个集合，用于去重 IP 地址
        unique_ips_to_add = set()
        add_item = []
        # 从 existing_ips 中提取出已经存在的 IP 地址
        existing_ip_set = set(ip['ip'] for ip in existing_ips)
        for ip_info in ip_list:
            # 拆分 IP 和备注
            ip, remark = ip_info.split(",", 1)
            # 检查 IP 是否已经在 existing_ips 中，或者已经在 unique_ips_to_add 中
            if ip not in existing_ip_set and ip not in unique_ips_to_add:
                # 如果 IP 没有重复，则加入待添加列表
                add_item.append({"ip": ip, "comment": remark})
                unique_ips_to_add.add(ip)

        return add_item

    def add_ips_to_list(self, account_id, list_id, add_item):
        item_url = f"{config.BASE_URL}/accounts/{account_id}/rules/lists/{list_id}/items"
        add_response = self.header.send_request("POST", item_url, "add ip", data=add_item)
        if add_response.status_code == 200:
            print(f"成功将 {len(add_item)} 个IP添加到列表")
        else:
            print(f"添加IP失败: {add_response.status_code} - {add_response.text}")
