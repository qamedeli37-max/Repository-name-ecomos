const fs = require('fs');
const path = require('path');
const cfgPath = path.join(require('os').homedir(), '.openclaw', 'openclaw.json');

let raw = fs.readFileSync(cfgPath, 'utf-8');
if (raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);

const cfg = JSON.parse(raw);

// Add reload mode
if (!cfg.gateway) cfg.gateway = {};
cfg.gateway.reload = { mode: 'hot', debounceMs: 300 };

// Write with pretty formatting
fs.writeFileSync(cfgPath, JSON.stringify(cfg, null, 2) + '\n', 'utf-8');
console.log('✅ 已设置 reload.mode = hot');
console.log('现在改配置不会自动重启网关，只会记警告');
