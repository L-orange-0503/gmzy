# Hero 区域设计 QA

## Source visual truth

- Source: `/Users/lishijiedemac/Desktop/1.jpg`
- Source dimensions: 1920 × 920 px
- State: 首页首屏，桌面端，页面顶部

## Implementation evidence

- Desktop capture: `/tmp/成都工贸-hero-implementation-desktop.png`
- Mobile capture: `/tmp/成都工贸-hero-implementation-mobile.png`
- Requested desktop viewport: 1920 × 920 CSS px
- Effective desktop capture: 1651 × 913 px（浏览器可用视口限制）
- Effective mobile capture: 375 × 812 px
- Density normalization: screenshots are 1× captures; no scaling applied

## Comparison

- Full-view evidence: hero background、导航、首屏标题、渐变标语色块和快捷入口的整体层级与参考图一致。
- Focused hero evidence: `厚德致远、精技兴业` 使用提供的 SVG 色块，桌面端为 28px/700；说明文案已替换为用户指定内容并保持左对齐换行。
- Responsive evidence: 移动端色块宽度随容器收缩，标语和说明文案无横向溢出，快捷入口仍正常显示。
- Interaction evidence: 控制台无 error/warning；已有导航和快捷入口交互未改变。

## Findings

无 P0/P1/P2 问题。桌面截图实际像素受浏览器视口上限影响，但首屏结构和目标区域可正常对照；该差异不属于页面布局问题。

## Implementation checklist

- [x] 更新 hero 说明文案
- [x] 使用提供的 SVG 渐变色块
- [x] 叠加 28px/700 标语
- [x] 校验桌面端首屏
- [x] 校验移动端响应式布局
- [x] 校验控制台日志

## Follow-up polish

无必要的 P3 调整。

final result: passed
