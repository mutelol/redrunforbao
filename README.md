# Curly Collection 内容助手

一个零第三方依赖的 Python 工具，用来扫描 `curlycollection.jp` 首页，自动挑选一个适合发的小红书题材，并生成本地内容包、图片素材和静态库存页。

## 功能

- 扫描首页的 `CURLY'S NEWS` 和 `NEW ARRIVALS`
- 自动选出一个主选题
- 用 `SQLite` 记录已生成过的产品，默认自动避重
- 抓取详情页补充标题、正文、图片和基础信息
- 生成中文内容包 `Markdown`
- 输出结构化元数据 `JSON`
- 下载原始图片到本地
- 生成一个可预览的中文封面草稿 `SVG`
- 自动生成一个手机友好的静态库存页
- 生成适合 GitHub Pages 的自包含站点，不再依赖本地 `runs/`
- 详情页会展示已保存到本地的图片，并提供打开原图和下载图片入口

## 运行

```powershell
python .\run_curly_agent.py
```

可选参数：

```powershell
python .\run_curly_agent.py --output-root .\runs
python .\run_curly_agent.py --homepage-url https://curlycollection.jp/
python .\run_curly_agent.py --no-download-images
python .\run_curly_agent.py --allow-seen
python .\run_curly_agent.py --config .\curly-agent.config.json
```

默认情况下，如果首页候选都已经生成过内容，程序会停止，避免重复产出。如果你确实想复用旧题材，可以加 `--allow-seen`。

单独重建静态站点：

```powershell
python .\build_static_site.py
```

## 输出结构

每次运行会在 `runs/` 下生成一个新目录，例如：

```text
runs/
  20260415-011523-arrival-fab1238/
    content-pack.md
    metadata.json
    assets/
      primary.jpg
      detail-2.jpg
      cover.svg
```

同时会刷新 GitHub Pages 友好的静态站点：

```text
site/
  index.html
  styles.css
  app.js
  data.json
  .nojekyll
  items/
    20260415-011523-arrival-fab1238.html
  records/
    20260415-011523-arrival-fab1238/
      content-pack.md
      assets/
        primary.jpg
        detail-2.jpg
        cover.svg
```

## GitHub Pages

这个项目已经带了 GitHub Pages 工作流：

- `.github/workflows/deploy-pages.yml`

只要这个目录已经连到一个 GitHub 仓库，并且推送到 `main` 分支，GitHub Actions 就会把 `site/` 发布成 Pages 站点。

本地辅助脚本：

```powershell
.\publish-github-pages.bat
```

这个 bat 会：

1. 先重建 `site/`
2. 检查当前目录是不是 Git 仓库
3. 检查有没有 `origin`
4. 提交并推送 `site/` 和 Pages 工作流

如果你还没初始化 Git，它会直接提示你下一步该怎么做。

## 腾讯云 CloudBase

如果给国内手机访问，推荐用腾讯云 CloudBase 静态网站托管。CloudBase 官方 CLI 支持扫码登录和静态网站上传，本项目已经准备了两个脚本：

```powershell
.\setup-tencent-cloudbase.bat
.\deploy-tencent-cloudbase.bat
```

第一次使用：

1. 先在腾讯云 CloudBase 控制台创建或打开一个环境，并确认开启“静态网站托管”。
2. 双击 `setup-tencent-cloudbase.bat`，它会安装 `@cloudbase/cli` 并引导你扫码登录。
3. 双击 `deploy-tencent-cloudbase.bat`，第一次会让你输入 CloudBase 环境 ID，之后会保存到本机 `.cloudbase-env`。

以后每次更新：

1. 双击 `run-curly-agent.bat` 生成新内容和本地图片。
2. 双击 `deploy-tencent-cloudbase.bat` 上传最新 `site/`。

`.cloudbase-env` 只保存在本机，已经加入 `.gitignore`，不会提交到 GitHub。

## 测试

```powershell
python -m unittest discover -s tests -v
```

## 说明

- 第一版只做“发现 + 生成 + 归档”，不碰小红书账号动作。
- 图片默认下载原图，并生成一个改图方向明确的 `SVG` 封面草稿，方便你后续手动再处理。
- 本地会创建一个 `curly-agent.sqlite3` 数据库，记录已经生成过内容的产品 URL 和产品编号。
- 静态网页默认生成在 `site/`，现在它是自包含结构，可以直接用于 GitHub Pages。
- 后续如果你有实拍图，可以继续在这个项目上加“实拍图修图 / 替换封面 / 官网图对比实拍”的能力。
