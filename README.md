# 代理服务

(开发中)

## ROADMAP
在openai格式的API的基础上，开发了一个代理服务

这个代理服务的目标是
- 增加token管理
    - 生成token
    - 对于用户请求进行token认证
- 增加日志功能
    - 在生成新的token时记录日志。
    - 在请求缺少token或token无效时记录警告日志。
    - 在处理请求和响应时记录详细信息。
    - 捕获所有的请求异常并记录错误日志。


## 启动服务
```python
# 服务端
python proxy.py
```

```python
# 客户端
python client.py
```

