# API.CC SMS Monitor

监控 [API.CC](https://api.cc) 接码平台指定项目的号码库存，有货时通过 [Bark](https://github.com/Finb/Bark) 推送到手机。

## 快速开始

### 1. 安装依赖

无需额外依赖，仅使用 Python 标准库（Python 3.8+）。

### 2. 配置

复制配置模板并填入你的信息：

```bash
cp cfg.json.example cfg.json
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `token` | API.CC 的 API Token | `F5C676E54248...` |
| `bark_api` | Bark 推送地址 | `https://api.day.app` |
| `bark_key` | Bark 设备 Key | `ByebX7ipTrdAc...` |
| `cate_id` | 项目分类 ID（启动时会显示所有分类） | `5`（美国实卡） |
| `type` | 卡类型：1=首次卡，2=重启卡，3=续费卡 | `1` |
| `project_name` | 项目名称关键词（模糊匹配） | `chatgpt` |
| `interval` | 轮询间隔（秒） | `60` |

### 3. 运行

```bash
python monitor.py
```

按 `Ctrl+C` 停止。

### 4. Docker 部署

```bash
docker build -t api-cc-sms-monitor .
docker run -d --restart=always --name api-cc-sms-monitor api-cc-sms-monitor
```

## 推送逻辑

- **仅在库存从 0 变为 >0 时**触发 Bark 推送，连续有货不重复通知

## License

MIT
