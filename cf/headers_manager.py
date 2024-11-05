class HeadersManager:
    def __init__(self):
        self.headers_map = {
            "No1": {
                'X-Auth-Email': 'xx',
                'X-Auth-Key': 'xx',
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
                # 可以根据需要添加更多的配置
            }

        }

    def get_headers(self, profile):
        return self.headers_map.get(profile, None)
