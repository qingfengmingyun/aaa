# 软件下载站（极简版）

一个只有「下载」功能的软件网站：把文件放进本项目目录，网页自动列出，点击即可下载。

部署链路：**本目录 → 上传到 GitHub → Cloudflare Pages 自动构建发布**，全程免费，自带 HTTPS。

## 目录说明

| 文件 | 作用 |
| --- | --- |
| `index.html` | 网页本体（文件列表 + 搜索 + 下载按钮） |
| `files.json` | 文件清单，由脚本自动生成，**不需要手动修改** |
| `generate_list.py` | 生成清单的脚本 |
| `.github/workflows/update-files.yml` | 可选：推送到 GitHub 后自动更新清单 |
| `README.md` | 本说明 |

---

## 第 1 步：把文件放进目录

把要分享的软件（apk / exe / zip / 任意后缀）**直接复制到本项目目录**（和 `index.html` 同一层，不要放进子文件夹）。

注意：

- 单个文件不能超过 **25 MiB（约 26 MB）**，这是 Cloudflare Pages 的硬性限制，超了会导致部署失败；大文件建议分卷压缩或改用网盘。
- GitHub 网页上传也有限制：单个文件最大 100 MB。

## 第 2 步：生成文件清单 `files.json`

三种方式任选一种，**推荐方式 A**：

**方式 A（推荐）：交给 Cloudflare 自动生成**

在第 4 步部署时，把 Cloudflare 的「构建命令」填成 `python3 generate_list.py`。以后每次部署都会自动生成清单，你什么都不用管。

**方式 B：本地运行脚本**

装了 Python 的电脑，在本目录打开终端运行：

```bash
python3 generate_list.py     # Windows 下一般为 python generate_list.py
```

运行后把 `files.json` 的变化一起上传到 GitHub 即可。

**方式 C：GitHub Actions 自动生成（本项目已内置）**

仓库启用后，每次推送都会自动重新生成清单并提交。需要先开启写权限：

> GitHub 仓库 → **Settings → Actions → General → Workflow permissions** → 选 **Read and write permissions** → Save。

不想折腾可以跳过方式 C（`.github` 文件夹甚至不用上传）。

## 第 3 步：上传到 GitHub

### 网页上传（最简单）

1. 打开 <https://github.com/new> 新建仓库；仓库名随意（如 `my-apps`），选择 **Public**，点 **Create repository**。
2. 在新仓库页面点 **uploading an existing file**。
3. 把本目录里的**所有文件**拖进上传区（想用方式 C 的话，记得连 `.github` 隐藏文件夹一起拖；如果还看到 `.backup` 之类的其他隐藏文件夹，跳过即可，不用上传）。
4. 点 **Commit changes** 完成。

### 命令行

```bash
# 在本项目目录里执行（如果提示缺少身份配置，先 git config --global user.name/user.email）
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

## 第 4 步：部署到 Cloudflare Pages

1. 打开 <https://dash.cloudflare.com> 登录（没有账号就免费注册一个）。
2. 左侧菜单 **Workers & Pages** → **Create application（创建应用）** → 切到 **Pages** 标签 → **Import an existing Git repository（导入现有 Git 仓库）**。
   - 首次使用需要授权：按提示安装 Cloudflare 的 GitHub App，允许它访问刚建的仓库。
3. 选中刚上传的仓库 → **Begin setup**。
4. 在 **Set up builds and deployments** 里按下表填写：

   | 配置项 | 填写内容 |
   | --- | --- |
   | Production branch（生产分支） | `main` |
   | Framework preset（框架预设） | `None` |
   | Build command（构建命令） | `python3 generate_list.py` |
   | Build output directory（构建输出目录） | `/` |

5. 点 **Save and Deploy**，等约 1 分钟。
6. 完成后会得到一个形如 `https://xxxx.pages.dev` 的网址 —— 打开就是你的下载站。

以后每次把新文件传到 GitHub，Cloudflare 都会自动重新构建并发布；打开网站刷新即可看到新文件。

## 本地预览（可选）

想在部署前先看看效果，可以在本目录运行：

```bash
python3 -m http.server 8000
```

然后浏览器打开 <http://localhost:8000>。
（直接双击打开 `index.html` 可能因浏览器安全限制看不到列表，属正常现象。）

## 常见问题

**Q：页面显示「暂无可下载的文件」？**
目录里没放文件，或 `files.json` 还没生成。放好文件后按第 2 步生成清单即可。

**Q：传了新文件，页面没有更新？**
部署需要 1~2 分钟；完成后强制刷新页面（电脑 Ctrl+F5，手机下拉刷新）。

**Q：想改网站名字和文案？**
编辑 `index.html` 中的这几处：

- `<title>软件下载</title>` → 浏览器标签页标题
- `<h1><span>软件下载</span></h1>` → 页面大标题
- `<p class="sub">…</p>` → 副标题
- 底部 `<footer>…</footer>` → 页脚文字

**Q：文件名是中文或带空格，可以吗？**
可以，脚本和网页均已处理。

**Q：文件超过 25 MiB 怎么办？**
Cloudflare Pages 单文件上限 25 MiB（约 26 MB），超过会导致构建失败。可以压缩成多个小于 25 MiB 的分卷包，或把大文件放到网盘后单独分享链接。

**Q：要花钱吗？需要备案吗？**
不需要。Cloudflare Pages 免费套餐即可：每月 500 次构建、站点最多 20000 个文件、自带 HTTPS 和全球 CDN。

## 许可

仅供学习交流，请勿用于分发侵权或盗版内容。
