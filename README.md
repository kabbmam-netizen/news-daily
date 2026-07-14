# 每日世界新闻摘要 (Daily News Digest)

每天自动抓取世界主要一手新闻源，按 **财经 / 政治 / 国际** 分类归档，生成 Markdown 摘要并归档，可选推送到企业微信群机器人、钉钉群机器人，或个人微信（经 Server酱 / PushPlus 中转）。

**数据源选型原则**：一手、客观、原始发布方（非聚合转载）。Reuters 为国际通讯社源头；NPR 为独立非营利公共媒体；CNBC/MarketWatch 为财经一手发布方；Politico/The Hill 为美国政治专业媒体。

- **调度**：GitHub Actions 每天 UTC 22:00（北京时间次日 06:00）自动运行
- **输出**：`digests/YYYY-MM-DD.md`，提交回仓库，本地 `git pull` 即可查看
- **推送**：通过 webhook 推送到企业微信 / 钉钉 / 个人微信（按 URL 域名自动识别）
- **依赖**：纯 RSS 抓取，无 AI、无数据库、无第三方付费 API

## 本地运行

```bash
pip install -r requirements.txt
python -m src.main
```

生成的摘要存放在 `digests/` 目录。若设置了 `WEBHOOK_URL` 环境变量，会同时推送通知：

```bash
# Linux / macOS
export WEBHOOK_URL="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
python -m src.main

# Windows PowerShell
$env:WEBHOOK_URL="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
python -m src.main
```

## 配置新闻源

编辑 `feeds.yml`，按格式自由增删：

```yaml
feeds:
  - name: 我的来源
    url: https://example.com/rss.xml
    category: 科技
```

- `max_entries_per_feed`：每个源最多保留多少条（默认 10）
- `max_total_entries`：摘要最多收录多少条（默认 50）

## 部署到 GitHub Actions

1. 在 GitHub 新建仓库，把本项目推上去：

   ```bash
   cd news-daily
   git init
   git add .
   git commit -m "init: daily news digest"
   git branch -M main
   git remote add origin git@github.com:<你的用户名>/news-daily.git
   git push -u origin main
   ```

2. 配置 webhook secret（不配也能跑，只是不会推送通知）：
   - 仓库 **Settings -> Secrets and variables -> Actions -> New repository secret**
   - Name 填 `WEBHOOK_URL`，Value 填你的企业微信 / 钉钉 / Server酱 / PushPlus 地址

3. 手动触发一次验证：
   - 仓库 **Actions** 标签页 -> 左侧选 `Daily News Digest` -> `Run workflow`
   - 检查 `digests/` 下是否生成当日摘要、推送渠道是否收到消息

4. 之后每天北京时间早上 6 点自动运行。

## 获取 Webhook 地址

### 企业微信群机器人
群右上角 `...` -> 群机器人 -> 添加机器人 -> 起名 -> 复制 webhook 地址。

### 钉钉自定义机器人
群设置 -> 智能群助手 -> 添加机器人 -> 自定义 ->
安全设置选「自定义关键词」，填 `新闻`（匹配摘要标题）-> 复制 webhook 地址。

### Server酱（推送到个人微信）
普通个人微信群不支持 webhook，可用 Server酱 中转：微信扫码登录 https://sct.ftqq.com/ 拿到 SendKey，拼成 `https://sctapi.ftqq.com/{你的SendKey}.send` 作为 `WEBHOOK_URL`。消息会通过 Server酱 小程序/公众号推到你的微信，免费版每天 5 条。

### PushPlus（推送到个人微信）
同上，另一个常用中转：微信扫码登录 https://www.pushplus.plus/ 并关注公众号，拿到 token，拼成 `https://www.pushplus.plus/send?token={你的token}` 作为 `WEBHOOK_URL`。免费额度较宽松。

> 推送渠道按 `WEBHOOK_URL` 的域名自动识别，企业微信 / 钉钉 / Server酱 / PushPlus 四选一即可，不用改代码。

## 项目结构

```
news-daily/
├── .github/workflows/daily-news.yml   # GitHub Actions 定时任务
├── digests/                           # 生成的每日摘要（自动提交）
├── src/
│   ├── main.py                        # 入口：抓取 -> 生成 -> 推送
│   ├── config.py                      # 读取 feeds.yml
│   ├── feeds.py                       # 并发抓取 RSS + 去重
│   ├── digest.py                      # Markdown 生成
│   └── notifiers.py                   # 企业微信 / 钉钉 / Server酱 / PushPlus 推送
├── feeds.yml                          # 新闻源配置（可自由增删）
├── requirements.txt
└── README.md
```

## 工作原理

1. `feeds.yml` 定义新闻源列表
2. `src/feeds.py` 并发抓取所有 RSS，按 URL 去重，按时间倒序
3. `src/digest.py` 按分类生成 Markdown 摘要
4. `src/main.py` 写入 `digests/YYYY-MM-DD.md`（按北京时间标注日期）并推送 webhook
5. GitHub Actions 把摘要提交回仓库

失败的源会被跳过并记录到日志，不影响其他源。

## License

MIT — 可自由使用、修改、分发。详见 [LICENSE](LICENSE)。
