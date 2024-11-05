import requests


class Header:
    def __init__(self, profile):
        self.session = requests.Session()
        self.headers_map = {
            "No1": {
                'X-Auth-Email': 'x',
                'X-Auth-Key': 'x',
                'Content-Type': 'application/json'
            },
            'No2': {
                'X-Auth-Email': 'xx',
                'X-Auth-Key': 'xx',
                'Content-Type': 'application/json'
            },
            'No3': {
                'X-Auth-Email': 'xx',
                'X-Auth-Key': 'xx',
                'Content-Type': 'application/json'
            }
        }
        self.session.headers.update(self.headers_map.get(profile))

    def send_request(self, method, url, name, data=None, params=None):
        try:
            response = self.session.request(method, url, json=data, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"处理 {name} 错误: {e}")
            return None
        return response

    def get_account_info(self, url):
        items = []
        page = 1
        per_page = 100

        while True:
            params = {'page': page, 'per_page': per_page}
            response = self.send_request('GET', url, "get_info", params=params)
            if response and response.status_code == 200:
                data = response.json()
                result_items = data.get('result', [])
                items.extend(result_items)
                if len(result_items) < per_page:
                    break
                page += 1
            else:
                print("获取区域信息失败。")
                return []
        return items
