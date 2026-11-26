# CLI documentation maintenance

## Required dual synchronization

For any user-visible CLI capability change (commands, flags, defaults, installation,
authorization, billing behavior, status, error handling, recovery or downloads),
update both:

1. `README.zh-CN.md`, the canonical Chinese CLI usage guide in this repository.
2. The user's Feishu tutorial:
   https://my.feishu.cn/wiki/P7e4wqY1uie5kAklYlncbxckn8b

Keep chapter coverage, command examples, applicable CLI version, document revision
and update date consistent. Render the canonical Markdown as Feishu headings,
tables and code blocks; do not independently invent a second set of instructions.
Update affected installation instructions and English usage statements as needed.

Before reporting completion:

- Verify flags against the actual parser and current service contracts.
- Distinguish parser checks, live reads, real generation, software release and
  production deployment. Do not claim one proves another.
- Reopen the Feishu document after cloud save and check the changed sections.
- If Feishu access or writing is unavailable, report **Feishu not synchronized**
  and retain the complete Markdown and the pending sync status. Updating GitHub
  alone does not satisfy this requirement.
- Capability documentation is not authorization to run paid generation or publish
  CLI software. Keep any release prerequisite visible until it is verified.

Do not include API keys, device codes, private workflow content or internal service
credentials in documentation, screenshots, Git commits or PR descriptions.
