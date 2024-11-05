from api import CloudflareAPI


class ZoneProcessor:
    def __init__(self, args, header):
        self.operations = args.operation  # 将 operations 存储在类中
        self.rule_manager = CloudflareAPI(header)  # 这里创建 RuleManager 的实例
        self.while_list = args.while_list
        self.ip_list = args.ip_list
        # 操作映射字典
        self.operation_map = {
            'del_dns': self.del_dns,
            'del_cache': self.del_cache,
            'add_rule': self.add_rule,
            'add_dns': self.add_dns,
            'add_parm': self.add_parm,
        }

    def process_zone(self, zone):
        # 针对每个操作执行相应的处理
        for operation in self.operations:
            operation_func = self.operation_map.get(operation)
            if operation_func:
                operation_func(zone)
            else:
                print(f"不支持的操作类型: {operation}")

    def del_dns(self, zone):
        self.rule_manager.delete_dns(zone)

    def del_cache(self, zone):
        self.rule_manager.purge_cache(zone)

    def add_dns(self, zone):
        self.rule_manager.add_dns(zone)

    def add_rule(self, zone):
        self.rule_manager.add_rulesets(zone)

    def add_parm(self, zone):
        self.rule_manager.add_init_param(zone)

    def add_while(self, while_list, ip_list):
        self.rule_manager.add_while(while_list, ip_list)
