# Synapse skills for Claude Code

A Claude Code plugin marketplace with skills for the Synapse Kotlin Multiplatform libraries (`com.ribads.synapse`).

## Install

In Claude Code:

```
/plugin marketplace add ribads/kmp-skills
/plugin install synapse@kmp-skills
```

Skills are namespaced under the plugin, for example `/synapse:ui-element` or `/synapse:build-screen`. Claude also loads a skill on its own when a task matches its description.

The [Claude Code skills guide](https://ribads.com/guides/claude-code/) covers sharing the plugin with a project and what each skill does.

## Update

Auto-update is off by default for third-party marketplaces. Turn it on in `/plugin` under Marketplaces, or update manually:

```sh
claude plugin marketplace update kmp-skills
claude plugin update synapse@kmp-skills
```

Then run `/reload-plugins` in any open session.

## Contributing

This repository is generated from the Synapse source repository on every change to its skills. Edits made here are overwritten by the next sync.
