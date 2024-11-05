# 全局变量
BASE_URL = 'https://api.cloudflare.com/client/v4/zones'
DNS_HOST = ["@", "www"]
DNS_VALUE = "xxx"
DNS_TYPE = "xxx"
# 清除缓存和删除dns是用
#MATCH_CLEAN_HOST = "xxx"
# init param
INIT_PARAM = [
    'http2', 'http3', 'tls_1_3', 'always_use_https', 'automatic_https_rewrites', 'early_hints',
    'websockets', 'browser_check', 'ipv6', 'security_header', 'min_tls_version', "rocket_loader"
]
# 规则映射 添加规则集是用
RULE_DATA_MAPPING = {
    "http_request_cache_settings": {
        "rule_name": "static cdn",
        "data": {
            "action": "set_cache_settings",
            "action_parameters": {
                "cache": True,
                "edge_ttl": {"mode": "override_origin", "default": 2592000},
                "browser_ttl": {"mode": "override_origin", "default": 2592000}
            },
            "expression": "(starts_with(http.request.uri.path, \"/static\")) or "
                          "(starts_with(http.request.uri.path, \"/assets\")) or "
                          "(starts_with(http.request.uri.path, \"/upload\"))",
            "description": "static cache",
            "enabled": True
        },
        "exists": False
    },
    "http_request_firewall_custom": {
        "rule_name": "block cn",
        "data": {
            "action": "block",
            "expression": "(ip.geoip.country eq \"CN\")",
            "description": "block cn"
        },
        "exists": False
    },
    "http_response_compression": {
        "rule_name": "compress_zstd",
        "data": {
            'action': 'compress_response',
            'action_parameters': {
                'algorithms': [{'name': 'zstd'}, {'name': 'brotli'}, {'name': 'gzip'}]
            },
            'description': 'compress_zstd',
            'enabled': True,
            'expression': '(http.response.content_type.media_type in {"text/html" "text/richtext" "text/plain" "text/css" "text/x-script" "text/x-component" "text/x-java-source" "text/x-markdown" "application/javascript" "application/x-javascript" "text/javascript" "text/js" "image/x-icon" "image/vnd.microsoft.icon" "application/x-perl" "application/x-httpd-cgi" "text/xml" "application/xml" "application/rss+xml" "application/vnd.api+json" "application/x-protobuf" "application/json" "multipart/bag" "multipart/mixed" "application/xhtml+xml" "font/ttf" "font/otf" "font/x-woff" "image/svg+xml" "application/vnd.ms-fontobject" "application/ttf" "application/x-ttf" "application/otf" "application/x-otf" "application/truetype" "application/opentype" "application/x-opentype" "application/font-woff" "application/eot" "application/font" "application/font-sfnt" "application/wasm" "application/javascript-binast" "application/manifest+json" "application/ld+json" "application/graphql+json" "application/geo+json" "image/png" "image/webp"})',
        },
        "exists": False
    }
}
