### cloudflare自动化工具
1、通过map映射支持多header头  
2、支持添加dns、通过规则集添加(缓存、防火墙、压缩规则)、删除dns、清除缓存

### 参数解释
-H 传入header map key 必填  
-o 传入要执行的操作 多个通过空格分割 必填  
-d 传入执行的域名,通过re.match和zone["name"]的值进行匹配  
-w 传入自定义白名单列表名称
-i 传入ip和备注使用,分割 格式为ip,remark ip2,remark2

### 案例
删除缓存  
python -H No1 -o del_cache -d xxx
添加白名单  
python -H No1 -o add_while -w server -i 127.0.0.1,test