# 成都工贸学院未来学习中心

这是一个无需构建的静态 HTML/CSS/JavaScript 网站，已整理为可直接部署到 GitHub Pages 的项目。

## GitHub Pages 部署

本项目使用仓库根目录作为发布目录：

1. 将项目提交并推送到 GitHub 仓库的 main 分支。
2. 打开仓库 Settings → Pages。
3. 在 Build and deployment 中选择 Deploy from a branch。
4. 分支选择 main，目录选择 /(root)，保存。
5. 等待 GitHub Pages 完成部署，项目站点地址通常为：
   https://<用户名>.github.io/<仓库名>/

这是一个无需构建的静态站点：Pages 发布源应选择 **`main` 分支的 `/(root)`**，而非 `/docs`。`docs/` 仅存放项目说明；发布时应保留仓库根目录下的 6 个 HTML 页面、`assets/` 与 `.nojekyll`。

根目录至少须保持以下结构：

~~~text
index.html
.nojekyll
assets/
~~~

index.html 中的本地资源均使用相对路径，适用于仓库项目站点路径；页面不依赖外部动画脚本。

## 本地预览

在项目根目录运行：

~~~bash
python3 -m http.server 4173
~~~

然后访问 http://127.0.0.1:4173/。

## 图片无损压缩

整理项目时可运行以下命令审计并压缩全部图片：

~~~bash
python3 tools/optimize-images-lossless.py --root . --apply
~~~

脚本会对 PNG 进行无损重打包，并验证压缩前后的解码数据完全一致；JPEG、GIF 和 WebP 不进行重新编码，避免画质损伤。当前环境没有安全的 JPEG/GIF 无损编码器，因此这些格式会被扫描并明确标记为保留。

## 项目说明

- 类型：静态站点，无需 npm install 或生产构建。
- 发布范围：整个仓库根目录。
- 本地资源：assets/ 下的图片与 GIF。
- 外部内容：页面中的 Figma 原型嵌入需要浏览器联网访问。
- 动效：模块会直接呈现，不使用滚动淡入淡出或页签切换淡入淡出。

## 项目文档

- [项目文件审计（2026-07-28）](docs/项目文件审计-2026-07-28.md)：发布页面的资源引用、清理候选和链接完整性检查结果。

如果部署后页面仍显示旧版本，请等待 Pages 构建完成后执行强制刷新，或使用无痕窗口打开站点。
