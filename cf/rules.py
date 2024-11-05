from config import RULE_DATA_MAPPING
import config


class RuleManager:
    def __init__(self, api):
        self.api = api

    def add_rulesets(self, zone):
        rulesets_url = f"{config.BASE_URL}/{zone['id']}/rulesets"
        ruleset_result = self.api.send_request("GET", rulesets_url, zone["name"])

        for rule in ruleset_result.get("result", []):
            phase = rule["phase"]
            if phase in RULE_DATA_MAPPING:
                rule_info = RULE_DATA_MAPPING[phase]
                if rule["name"] == rule_info["rule_name"]:
                    rule_info["exists"] = True
                    continue
                rules_url = f"{rulesets_url}/{rule['id']}/rules"
                self.api.send_request("POST", rules_url, zone["name"], data=rule_info["data"])

        # 检查是否需要创建新的规则集
        for phase, rule_info in RULE_DATA_MAPPING.items():
            if not rule_info["exists"]:
                self.api.send_request("POST", rulesets_url, zone["name"], data={"rules": [rule_info["data"]]})

    def purge_cache(self, zone):
        url = f"{config.BASE_URL}/{zone['id']}/purge_cache"
        data = {"purge_everything": True}
        response = self.api.send_request("POST", url, zone["name"], data=data)
        if response:
            print(f'Cache purged for {zone["name"]}')
        else:
            print(f'Failed to purge cache for {zone["name"]}')

    def delete_dns(self, zone):
        list_dns_url = f"{config.BASE_URL}/{zone['id']}/dns_records"
        dns_resp = self.api.send_request("GET", list_dns_url, zone["name"])
        if dns_resp is None:
            return

        dns_records = dns_resp.json()
        for record in dns_records['result']:
            delete_dns_url = f"{config.BASE_URL}/{zone['id']}/dns_records/{record['id']}"
            resp = self.api.send_request("DELETE", delete_dns_url, zone["name"])
            if resp and resp.status_code == 200:
                print(f"{record['name']} deleted")

    def add_dns(self, zone):
        dns_url = f'{config.BASE_URL}/{zone["id"]}/dns_records'
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
            self.api.send_request("POST", dns_url, zone["name"], data=dns_data)

    def add_init_param(self, zone):
        for param in config.INIT_PARAM:
            url = f'{config.BASE_URL}/{zone["id"]}/settings/{param}'
            result = self.api.send_request("GET", url, zone["name"])

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
                    self.api.send_request("PATCH", url, zone["name"], data={'value': updates[param_key]['value']})

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
        hsts_url = f'{config.BASE_URL}/{zone["id"]}/settings/security_header'
        self.api.send_request("PATCH", hsts_url, zone["name"], data=hsts_data)
