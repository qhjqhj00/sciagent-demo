# Scripts

## start_frontend.sh

启动前端应用的脚本。它会：
1. 启动后端 API 服务器（如果未运行）
2. 启动前端 Web 服务器
3. 在端口 12312 提供服务

### 使用方法

```bash
cd /root/dw/research/sciagent-demo/scripts
./start_frontend.sh
```

然后访问：http://localhost:12312/index.html

### API 端点

- `GET /api/config` - 获取配置
- `GET /api/test_data` - 获取测试数据
- `GET /api/stats` - 获取数据统计

### 新功能

#### Data Status Bar
在搜索框上方显示数据状态：
- **Total Papers**: 总论文数量（带千分位格式化）
- **Latest Update**: 最新更新时间

状态栏使用半透明白色背景，具有毛玻璃效果，与整体设计协调。

