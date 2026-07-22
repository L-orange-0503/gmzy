const fs = require('fs');
const os = require('os');
const path = require('path');
const { chromium } = require('/Users/lishijiedemac/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright@1.61.1/node_modules/playwright');

const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const outputDir = path.resolve(process.cwd(), 'analysis/site-style-extraction');
const keepScreenshots = process.env.KEEP_ANALYSIS_SCREENSHOTS === '1';
const screenshotDir = keepScreenshots
  ? path.join(outputDir, 'screenshots')
  : fs.mkdtempSync(path.join(os.tmpdir(), 'site-style-screenshots-'));

const urls = [
  'https://52uzx4tv.mh.chaoxing.com/?wfwfid=67395&pageId=2614724&websiteId=967576&uid=146333006&mhType=2&publicId=371087a1-9e3c147121b674-96e9db480225&mhEnc=0dab8a23ea16450462840e4fdfb75c9f',
  'https://sptc.mh.chaoxing.com/?wfwfid=67395&pageId=2614724&websiteId=967576&uid=146333006&mhType=2&publicId=371087a1-9e3c147121b674-96e9db480225&mhEnc=0dab8a23ea16450462840e4fdfb75c9f',
  'https://5wvwmocx.mh.chaoxing.com/?wfwfid=67395&pageId=2614724&websiteId=967576&uid=146333006&mhType=2&publicId=371087a1-9e3c147121b674-96e9db480225&mhEnc=0dab8a23ea16450462840e4fdfb75c9f',
  'https://5tm7jcox.mh.chaoxing.com/?wfwfid=67395&pageId=2614724&websiteId=967576&uid=146333006&mhType=2&publicId=371087a1-9e3c147121b674-96e9db480225&mhEnc=0dab8a23ea16450462840e4fdfb75c9f',
  'https://5uuvezml.mh.chaoxing.com/?wfwfid=67395&pageId=2614724&websiteId=967576&uid=146333006&mhType=2&publicId=371087a1-9e3c147121b674-96e9db480225&mhEnc=0dab8a23ea16450462840e4fdfb75c9f',
  'https://53i91uz6.mh.chaoxing.com/?wfwfid=67395&pageId=2614724&websiteId=967576&uid=146333006&mhType=2&publicId=371087a1-9e3c147121b674-96e9db480225&mhEnc=0dab8a23ea16450462840e4fdfb75c9f',
  'https://seuwlxxzx.mh.chaoxing.com/?wfwfid=67395&pageId=2614724&websiteId=967576&uid=146333006&mhType=2&publicId=371087a1-9e3c147121b674-96e9db480225&mhEnc=0dab8a23ea16450462840e4fdfb75c9f',
  'https://52u5blwj.mh.chaoxing.com/?wfwfid=67395&pageId=2614724&websiteId=967576&uid=146333006&mhType=2&publicId=371087a1-9e3c147121b674-96e9db480225&mhEnc=0dab8a23ea16450462840e4fdfb75c9f',
  'https://52us7rzt.mh.chaoxing.com/?wfwfid=67395&pageId=2614724&websiteId=967576&uid=146333006&mhType=2&publicId=371087a1-9e3c147121b674-96e9db480225&mhEnc=0dab8a23ea16450462840e4fdfb75c9f',
  'https://aicenter.whu.edu.cn/?wfwfid=67395&pageId=2614724&websiteId=967576&uid=146333006&mhType=2&publicId=371087a1-9e3c147121b674-96e9db480225&mhEnc=0dab8a23ea16450462840e4fdfb75c9f'
];

function countValues(values) {
  const map = new Map();
  for (const value of values.filter(Boolean)) {
    map.set(value, (map.get(value) || 0) + 1);
  }
  return [...map.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 24)
    .map(([value, count]) => ({ value, count }));
}

function analyzeElementsInPage() {
  const countLocalValues = (values) => {
    const map = new Map();
    for (const value of values.filter(Boolean)) {
      map.set(value, (map.get(value) || 0) + 1);
    }
    return [...map.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 24)
      .map(([value, count]) => ({ value, count }));
  };

  const isVisible = (el) => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return (
      rect.width > 2 &&
      rect.height > 2 &&
      style.visibility !== 'hidden' &&
      style.display !== 'none' &&
      Number(style.opacity) > 0.01
    );
  };

  const elements = [...document.querySelectorAll('body *')]
    .filter(isVisible)
    .slice(0, 1600)
    .map((el) => {
      const rect = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      const text = (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80);
      return {
        tag: el.tagName.toLowerCase(),
        className: String(el.className || '').slice(0, 160),
        id: String(el.id || '').slice(0, 80),
        text,
        rect: {
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          width: Math.round(rect.width),
          height: Math.round(rect.height)
        },
        style: {
          color: style.color,
          backgroundColor: style.backgroundColor,
          backgroundImage: style.backgroundImage && style.backgroundImage !== 'none' ? style.backgroundImage.slice(0, 240) : '',
          fontFamily: style.fontFamily,
          fontSize: style.fontSize,
          fontWeight: style.fontWeight,
          lineHeight: style.lineHeight,
          letterSpacing: style.letterSpacing,
          borderRadius: style.borderRadius,
          boxShadow: style.boxShadow,
          borderTop: style.borderTop,
          padding: `${style.paddingTop} ${style.paddingRight} ${style.paddingBottom} ${style.paddingLeft}`,
          margin: `${style.marginTop} ${style.marginRight} ${style.marginBottom} ${style.marginLeft}`
        }
      };
    });

  const links = [...document.querySelectorAll('link[rel~="stylesheet"]')]
    .map((el) => el.href)
    .filter(Boolean);
  const images = [...document.images]
    .map((img) => ({
      src: img.currentSrc || img.src,
      alt: img.alt || '',
      width: img.naturalWidth || img.width,
      height: img.naturalHeight || img.height
    }))
    .filter((img) => img.src)
    .slice(0, 80);

  const bodyStyle = getComputedStyle(document.body);
  return {
    title: document.title,
    url: location.href,
    bodyTextSample: document.body.innerText.replace(/\s+/g, ' ').trim().slice(0, 1000),
    bodyStyle: {
      color: bodyStyle.color,
      backgroundColor: bodyStyle.backgroundColor,
      backgroundImage: bodyStyle.backgroundImage && bodyStyle.backgroundImage !== 'none' ? bodyStyle.backgroundImage.slice(0, 240) : '',
      fontFamily: bodyStyle.fontFamily,
      fontSize: bodyStyle.fontSize,
      lineHeight: bodyStyle.lineHeight
    },
    stylesheets: links,
    images,
    counts: {
      tags: countLocalValues(elements.map((el) => el.tag)),
      fontFamilies: countLocalValues(elements.map((el) => el.style.fontFamily)),
      fontSizes: countLocalValues(elements.map((el) => el.style.fontSize)),
      fontWeights: countLocalValues(elements.map((el) => el.style.fontWeight)),
      colors: countLocalValues(elements.map((el) => el.style.color)),
      backgrounds: countLocalValues(elements.map((el) => el.style.backgroundColor).filter((v) => v !== 'rgba(0, 0, 0, 0)')),
      radii: countLocalValues(elements.map((el) => el.style.borderRadius).filter((v) => v !== '0px')),
      shadows: countLocalValues(elements.map((el) => el.style.boxShadow).filter((v) => v !== 'none')),
      borders: countLocalValues(elements.map((el) => el.style.borderTop).filter((v) => !v.startsWith('0px none')))
    },
    notableElements: elements
      .filter((el) => {
        const width = el.rect.width;
        const height = el.rect.height;
        const hasText = el.text.length > 0;
        const hasVisual = el.style.backgroundColor !== 'rgba(0, 0, 0, 0)' || el.style.boxShadow !== 'none' || el.style.backgroundImage;
        return hasText || (width > 120 && height > 80 && hasVisual);
      })
      .slice(0, 160)
  };
}

async function safeAnalyzeFrame(frame) {
  try {
    return await frame.evaluate(analyzeElementsInPage);
  } catch (error) {
    return {
      url: frame.url(),
      error: error.message
    };
  }
}

async function captureVariant(context, url, siteId, variant, viewport, isMobile) {
  const page = await context.newPage();
  await page.setViewportSize(viewport);
  const result = {
    siteId,
    variant,
    requestedUrl: url,
    status: null,
    finalUrl: null,
    title: null,
    error: null,
    screenshots: {},
    frames: []
  };

  try {
    const response = await page.goto(url, {
      waitUntil: 'domcontentloaded',
      timeout: 45000
    });
    result.status = response ? response.status() : null;
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    await page.waitForTimeout(3000);
    result.finalUrl = page.url();
    result.title = await page.title();

    const baseName = `${siteId}-${variant}`;
    const viewportPath = path.join(screenshotDir, `${baseName}-viewport.png`);
    await page.screenshot({ path: viewportPath, fullPage: false });
    result.screenshots.viewport = keepScreenshots ? viewportPath : '';

    if (!isMobile) {
      const fullPagePath = path.join(screenshotDir, `${baseName}-fullpage.png`);
      await page.screenshot({ path: fullPagePath, fullPage: true });
      result.screenshots.fullPage = keepScreenshots ? fullPagePath : '';
    }

    for (const frame of page.frames()) {
      result.frames.push(await safeAnalyzeFrame(frame));
    }
  } catch (error) {
    result.error = error.message;
  } finally {
    await page.close().catch(() => {});
  }

  return result;
}

async function main() {
  fs.mkdirSync(screenshotDir, { recursive: true });

  const browser = await chromium.launch({
    headless: true,
    executablePath: chromePath
  });

  const desktopContext = await browser.newContext({
    viewport: { width: 1440, height: 1100 },
    deviceScaleFactor: 1,
    userAgent:
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    locale: 'zh-CN'
  });

  const mobileContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true,
    userAgent:
      'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
    locale: 'zh-CN'
  });

  const allResults = [];
  for (let i = 0; i < urls.length; i += 1) {
    const siteId = `site${String(i + 1).padStart(2, '0')}`;
    console.log(`Capturing ${siteId}`);
    allResults.push(await captureVariant(desktopContext, urls[i], siteId, 'desktop', { width: 1440, height: 1100 }, false));
    allResults.push(await captureVariant(mobileContext, urls[i], siteId, 'mobile', { width: 390, height: 844 }, true));
  }

  await desktopContext.close();
  await mobileContext.close();
  await browser.close();

  const summaryPath = path.join(outputDir, 'summary.json');
  fs.writeFileSync(summaryPath, JSON.stringify({
    capturedAt: new Date().toISOString(),
    urls,
    results: allResults
  }, null, 2));

  const lines = [
    '# Site Style Extraction Precheck',
    '',
    `Captured at: ${new Date().toISOString()}`,
    '',
    '| Site | Variant | Status | Title | Error | Screenshot |',
    '|---|---:|---:|---|---|---|'
  ];
  for (const item of allResults) {
    const shot = item.screenshots.viewport ? path.relative(outputDir, item.screenshots.viewport) : '';
    lines.push(`| ${item.siteId} | ${item.variant} | ${item.status ?? ''} | ${(item.title || '').replace(/\|/g, '/')} | ${(item.error || '').replace(/\|/g, '/')} | ${shot} |`);
  }
  fs.writeFileSync(path.join(outputDir, 'precheck.md'), `${lines.join('\n')}\n`);

  if (!keepScreenshots) {
    fs.rmSync(screenshotDir, { recursive: true, force: true });
  }

  console.log(`Wrote ${summaryPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
