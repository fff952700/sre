from config import RULE_DATA_MAPPING
import config


class CloudflareAPI:
    def __init__(self, header):
        self.header = header

    def add_rulesets(self, zone):
        rulesets_url = f"{config.BASE_URL}/zones/{zone['id']}/rulesets"
        ruleset_result = self.header.send_request("GET", rulesets_url, zone["name"])

        # 检查是否存在需要的规则集，并更新对应状态
        for rule in ruleset_result.get("result", []):
            phase = rule["phase"]
            if phase in RULE_DATA_MAPPING:
                rule_info = RULE_DATA_MAPPING[phase]
                if rule["name"] == rule_info["rule_name"]:
                    rule_info["exists"] = True
                    continue
                rules_url = f"{rulesets_url}/{rule['id']}/rules"
                self.header.send_request("POST", rules_url, zone["name"], data=rule_info["data"])

        # 创建新的规则集
        for phase, rule_info in RULE_DATA_MAPPING.items():
            if not rule_info["exists"]:
                self.header.send_request("POST", rulesets_url, zone["name"], data={"rules": [rule_info["data"]]})

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

        dns_records = dns_resp.json()
        for record in dns_records['result']:
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
            result = self.header.send_request("GET", url, zone["name"])

            if result:
                param_key = result["result"]["id"]
                param_value = result["result"]["value"]

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

        existing_ips = self.header.get_account_info(
            f"{config.BASE_URL}/accounts/{account_id}/rules/lists/{target_list['id']}/items")
        if existing_ips is None:
            return
        print("c")
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
        unique_ips_to_add = set()
        add_item = []
        for ip_info in ip_list:
            ip, remark = ip_info.split(",", 1)
            if ip not in existing_ips and ip not in unique_ips_to_add:
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
