### cloudflare自动化工具
1、通过map映射支持多header头  
2、支持添加dns、通过规则集添加(缓存、防火墙、压缩规则)、删除dns、清除缓存

### 参数解释  均为必填
-H 传入header map key  
-o 传入要执行的操作 多个通过空格分割  
-d 传入执行的域名,通过re.match和zone["name"]的值进行匹配

### 案例
python -H No1 -o del_cache -d xxx