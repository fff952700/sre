from rules import RuleManager


class ZoneProcessor:
    def __init__(self, api, operations):
        self.api = api
        self.operations = operations  # 将 operations 存储在类中
        self.rule_manager = RuleManager(self.api)

        # 操作映射字典
        self.operation_map = {
            'del_dns': self.del_dns,
            'del_cache': self.del_cache,
            'add_rule': self.add_rule,
            'add_dns': self.add_dns,
            'add_parm': self.add_parm,
        }

    def process_zone(self, zone, operations=None):
        # 针对每个操作执行相应的处理
        operations = operations or self.operations  # 如果没有传递 operations，则使用类中的 operations
        for operation in operations:
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
