import requests
import argparse
from api import CloudflareAPI
from zone_processor import ZoneProcessor
from concurrent.futures import ThreadPoolExecutor


def init_cloudflare(operations, headers_profile, domain_filter):
    session = requests.Session()
    # 创建 CloudflareAPI 实例并传入 session、操作类型和头配置
    api = CloudflareAPI(session, headers_profile)

    # 获取区域列表
    zone_list = api.get_zones()

    # 如果有传入域名过滤条件，则根据条件筛选区域
    if domain_filter:
        zone_list = [zone for zone in zone_list if any(domain in zone['name'] for domain in domain_filter)]

    processor = ZoneProcessor(api, operations)  # 传递 API 实例给 ZoneProcessor

    with ThreadPoolExecutor(max_workers=10) as executor:
        # 使用并发处理每个区域
        futures = {executor.submit(processor.process_zone, zone, operations): zone for zone in zone_list}

        for future in futures:
            try:
                # 获取结果，如果有异常会在这里抛出
                future.result()
            except Exception as e:
                zone_name = futures[future].get('name', '未知区域')  # 获取区域的名称
                print(f"处理区域 {zone_name} 时发生错误: {e}")

    session.close()


def parse_arguments():
    parser = argparse.ArgumentParser(description='Cloudflare API 操作')
    parser.add_argument('-H', '--headers-profile', type=str, required=True,
                        choices=['No1', 'No2', 'No3'], help='选择使用的头配置（office、No1 或 No2）')
    parser.add_argument('-o', '--operation', type=str, nargs='+',
                        choices=['del_dns', 'del_cache', 'add_rule', 'add_dns', 'add_param'],
                        required=True,
                        help='指定操作类型，如 delete_dns（删除DNS）、delete_rule（删除规则）、add_rule（添加规则）、add_dns（添加DNS）等。多个操作用空格分隔')
    parser.add_argument('-d', '--domain', type=str, nargs='+', required=True, help='正则处理的域名，多个使用空格分隔。')

    return parser.parse_args()


if __name__ == '__main__':
    # 获取传参
    args = parse_arguments()

    # 调用 Cloudflare API 初始化，传入操作类型、头配置和可选的域名
    init_cloudflare(args.operation, args.headers_profile, domain_filter=args.domain)
