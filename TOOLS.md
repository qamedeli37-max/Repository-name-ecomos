# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Environment

- OS: Windows 10.0.19044 (x64)
- Shell: PowerShell
- Channel: openclaw-weixin (WeChat)
- Timezone: Asia/Shanghai

## Available CLIs

| Tool | Path |
|------|------|
| node | C:\Program Files\nodejs\node.exe |
| curl | C:\Windows\system32\curl.exe |
| python3 | WindowsApps |
| dotnet | C:\Program Files\dotnet\ |
| winget | WindowsApps (package manager) |
| cloudflared | C:\Program Files (x86)\cloudflared\ |
| wsl | WSL available |
| ssh | OpenSSH in system32 |

## Proxy (Clash Verge)

- Core: verge-mihomo
- Mixed port: 7897
- HTTP port: 7899
- SOCKS port: 7898
- Config dir: %APPDATA%\io.github.clash-verge-rev.clash-verge-rev
- Profiles: %APPDATA%\io.github.clash-verge-rev.clash-verge-rev\profiles\
- Logs: %APPDATA%\io.github.clash-verge-rev.clash-verge-rev\logs\

## User (桐希)

- Creative tools: 3ds Max, After Effects, Premiere, Blender, Photoshop
- Apps: WPS, 夸克, 豆包, 小红书, Steam, 和平精英模拟器
- Proxy provider: 淘气兔 (TQT) - subscription API at 47.97.81.77:88

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)
