import requests
import argparse
from http_request import Header
from zone_processor import ZoneProcessor
from api import CloudflareAPI
from concurrent.futures import ThreadPoolExecutor, as_completed
import config
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_cloudflare():
    """初始化 Cloudflare API，并处理传入的命令行参数"""
    session = requests.Session()
    args = parse_arguments()
    header = Header(args.headers_profile)

    try:
        if args.while_list:
            # 使用白名单直接处理
            api = CloudflareAPI(header)
            api.add_while(args.while_list, args.ip_list)
        else:
            # 获取区域列表
            zone_list = header.send_request("GET", f"{config.BASE_URL}/zones", "get zone")
            if not zone_list:
                logger.warning("未找到任何区域信息，请检查 Cloudflare API 配置是否正确。")
                return

            # 域名过滤
            if args.domain:
                zone_list = [zone for zone in zone_list.json().get('result') if any(domain in zone['name'] for domain in args.domain)]
                if not zone_list:
                    logger.warning("根据域名过滤条件，未找到匹配的区域。")

            # 处理每个 zone
            processor = ZoneProcessor(args,header)
            with ThreadPoolExecutor(max_workers=config.MAX_WORKS) as executor:
                futures = {executor.submit(processor.process_zone, zone): zone for zone in zone_list}

                for future in as_completed(futures):
                    zone = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"处理区域 {zone.get('name', '未知区域')} 时发生错误: {e}")

    except Exception as e:
        logger.error(f"初始化 Cloudflare 时发生错误: {e}")

    finally:
        session.close()


def parse_arguments():
    parser = argparse.ArgumentParser(description='Cloudflare API 操作')
    parser.add_argument('-H', '--headers-profile', type=str, required=True,
                        choices=['No1', 'No2', 'No3'], help='选择使用的头配置（No1, No2 或 No3）')
    parser.add_argument('-o', '--operation', type=str, nargs='+',
                        choices=['del_dns', 'del_cache', 'add_rule', 'add_dns', 'add_param', 'add_while'],
                        required=True, help='指定操作类型，如 del_dns, add_rule 等。多个操作用空格分隔')
    parser.add_argument('-d', '--domain', type=str, nargs='+', help='过滤的域名，多个用空格分隔。')
    parser.add_argument('-w', '--while_list', type=str, nargs='+', help='添加白名单')
    parser.add_argument('-i', '--ip_list', type=str, nargs='+', help='添加 IP 列表，多个用空格分隔。')
    return parser.parse_args()


if __name__ == '__main__':
    init_cloudflare()
