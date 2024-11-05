import requests
from config import BASE_URL
from headers_manager import HeadersManager


class CloudflareAPI:
    def __init__(self, session, headers_profile):
        self.session = session
        self.headers_manager = HeadersManager()
        headers = self.headers_manager.get_headers(headers_profile)

        if headers is None:
            raise ValueError(f"未找到配置为 '{headers_profile}' 的请求头")
        else:
            self.session.headers.update(headers)  # 将 headers 添加到 session

    def send_request(self, method, url, name, data=None, params=None):
        try:
            response = self.session.request(method, url, json=data, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"处理{name} 错误: {e}")
            return None
        return response

    def get_zones(self):
        url = f"{BASE_URL}"
        items = []
        page = 1
        per_page = 50

        while True:
            params = {'page': page, 'per_page': per_page}
            response = self.send_request('GET', url, "get_zones", params=params)

            if response and response.status_code == 200:
                data = response.json()
                result_items = data.get('result', [])
                items.extend(result_items)
                if len(result_items) < per_page:
                    break
                page += 1
            else:
                print("Failed to fetch zones.")
                return []
        return items
