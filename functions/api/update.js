// Cloudflare Pages Function ——「检查更新」接口
// 路由：GET /api/update?pkg=包名&vc=版本号(可选)&vn=版本名
// 数据来源：构建时由 generate_list.py 自动生成的 /update.json

const FALLBACK_NOTES = "优化与修复，建议更新到最新版本。";

function jsonResp(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*"
    }
  });
}

// "6.10" -> [6,10]；非法格式返回 null
function verKey(v) {
  if (!v || !/^[0-9]+(\.[0-9]+)*$/.test(v)) return null;
  return v.split(".").map(function (x) { return parseInt(x, 10); });
}

// a > b 返回 1；a < b 返回 -1；相等返回 0
function verCmp(a, b) {
  var n = Math.max(a.length, b.length);
  for (var i = 0; i < n; i++) {
    var x = a[i] || 0;
    var y = b[i] || 0;
    if (x > y) return 1;
    if (x < y) return -1;
  }
  return 0;
}

export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const pkg = (url.searchParams.get("pkg") || "").trim();
  const vn = (url.searchParams.get("vn") || "").trim();
  if (!pkg) return jsonResp({ ok: false, msg: "缺少包名参数" }, 400);

  let meta = null;
  try {
    const res = await env.ASSETS.fetch(new URL("/update.json?ts=" + Date.now(), url.origin));
    if (res.ok) meta = await res.json();
  } catch (e) {
    meta = null;
  }
  if (!meta || !meta.apps || !meta.apps[pkg]) {
    return jsonResp({ ok: false, msg: "未收录该应用的更新信息" }, 404);
  }
  const app = meta.apps[pkg];
  if (!app.versionName || !app.file) {
    return jsonResp({ ok: false, msg: "更新信息不完整" }, 500);
  }

  const server = verKey(app.versionName);
  const client = verKey(vn);
  if (server && client && verCmp(client, server) >= 0) {
    return jsonResp({ ok: true, latest: true, serverVersionName: app.versionName });
  }

  const dl = new URL("/" + encodeURIComponent(app.file), url.origin).toString();
  return jsonResp({
    ok: true,
    latest: false,
    serverVersionName: app.versionName,
    url: dl,
    file: app.file,
    size: app.size || 0,
    md5: app.md5 || "",
    notes: app.notes || FALLBACK_NOTES
  });
}
