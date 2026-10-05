#!/usr/bin/env python3
"""Comprehensive verification script for VibeWise Codex port.

Performs static validation of manifests, assets, and configurations,
followed by a live CLI smoke test with an isolated temporary CODEX_HOME
testing marketplace registration, plugin installation, and app-server
JSON-RPC discovery for skills and hooks.
"""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import yaml


ROOT = Path(__file__).resolve().parents[1]
CODEX_ROOT = ROOT / "codex"


def log(msg):
    print(f"[verify_codex] {msg}")


def verify_static():
    log("Running static validation...")

    # 1. Root marketplace manifest
    marketplace_file = ROOT / ".agents/plugins/marketplace.json"
    assert marketplace_file.is_file(), f"Missing {marketplace_file}"
    marketplace = json.loads(marketplace_file.read_text(encoding="utf-8"))
    assert marketplace.get("name") == "vibe-wise", f"Unexpected name: {marketplace.get('name')}"
    assert marketplace.get("interface", {}).get("displayName") == "VibeWise"
    plugins = marketplace.get("plugins", [])
    assert len(plugins) == 1, f"Expected 1 plugin, got {len(plugins)}"
    assert plugins[0].get("name") == "vibe-wise"
    assert plugins[0].get("source") == {"source": "local", "path": "./codex"}
    assert plugins[0].get("policy") == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}
    assert plugins[0].get("category") == "Productivity"
    log("[OK] Root marketplace.json is valid")

    # 2. Codex plugin manifest
    plugin_file = CODEX_ROOT / ".codex-plugin/plugin.json"
    assert plugin_file.is_file(), f"Missing {plugin_file}"
    plugin = json.loads(plugin_file.read_text(encoding="utf-8"))
    assert plugin.get("name") == "vibe-wise"
    assert plugin.get("version") == "0.1.43-codex.1"
    assert plugin.get("skills") == "./skills/"
    assert plugin.get("hooks") == "./hooks/hooks.json"
    interface = plugin.get("interface", {})
    assert interface.get("displayName") == "VibeWise"
    assert interface.get("shortDescription") == "Mindful pair programming that keeps you in the driver's seat"
    assert interface.get("developerName") == "Noah Kim"
    assert interface.get("category") == "Productivity"
    assert interface.get("composerIcon") == "./assets/vibewise-icon.png"
    assert interface.get("logo") == "./assets/vibewise-icon.png"
    log("[OK] codex/.codex-plugin/plugin.json is valid")

    # 3. Assets and license
    assert (CODEX_ROOT / "LICENSE").is_file(), "Missing codex/LICENSE"
    assert (CODEX_ROOT / "assets/vibewise-icon.png").is_file(), "Missing codex/assets/vibewise-icon.png"
    log("[OK] Bundle LICENSE and icon assets exist")

    # 4. Hooks configuration
    hooks_file = CODEX_ROOT / "hooks/hooks.json"
    assert hooks_file.is_file(), f"Missing {hooks_file}"
    hooks_data = json.loads(hooks_file.read_text(encoding="utf-8"))
    session_start_hooks = hooks_data.get("hooks", {}).get("SessionStart", [])
    assert len(session_start_hooks) >= 1, "Missing SessionStart hook"
    reg = session_start_hooks[0]
    assert reg.get("matcher") == "startup|resume|clear|compact", f"Unexpected matcher: {reg.get('matcher')}"
    hook_entry = reg.get("hooks", [])[0]
    assert hook_entry.get("type") == "command"
    assert hook_entry.get("timeout") == 5
    assert hook_entry.get("statusMessage") == "Loading VibeWise learning context"
    assert "session_start.py" in hook_entry.get("command")
    assert (CODEX_ROOT / "hooks/session_start.py").is_file(), "Missing codex/hooks/session_start.py"
    log("[OK] codex/hooks/hooks.json and session_start.py are valid")

    # 5. Skills and OpenAI policies
    for skill_name in ("learn", "reset"):
        skill_dir = CODEX_ROOT / f"skills/{skill_name}"
        skill_md = skill_dir / "SKILL.md"
        assert skill_md.is_file(), f"Missing {skill_md}"
        content = skill_md.read_text(encoding="utf-8")
        assert content.startswith("---"), f"{skill_md} must have frontmatter"
        fm = yaml.safe_load(content.split("---", 2)[1])
        assert fm.get("name") == skill_name
        assert fm.get("disable-model-invocation") is True

        openai_yaml = skill_dir / "agents/openai.yaml"
        assert openai_yaml.is_file(), f"Missing {openai_yaml}"
        data = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))
        assert data.get("policy", {}).get("allow_implicit_invocation") is False, \
            f"{skill_name} must disallow implicit invocation"
        assert "interface" in data
        assert data["interface"].get("display_name")
        assert data["interface"].get("short_description")
        assert data["interface"].get("default_prompt")
    log("[OK] Skill definitions and openai.yaml policies are valid")

    # 6. Companion documents and scripts
    assert (CODEX_ROOT / "skills/learn/behavior.md").is_file()
    assert (CODEX_ROOT / "skills/learn/onboarding.md").is_file()
    assert (CODEX_ROOT / "skills/learn/state-templates.md").is_file()
    assert (CODEX_ROOT / "skills/reset/reset.py").is_file()
    assert (CODEX_ROOT / "README.md").is_file()
    log("[OK] Companion guides, reset helper, and README exist")


def verify_live():
    codex_bin = shutil.which("codex")
    if not codex_bin:
        log("codex binary not found in PATH; skipping live smoke test")
        return

    log(f"Running live CLI smoke verification using {codex_bin}...")
    with tempfile.TemporaryDirectory(prefix="codex-smoke-", ignore_cleanup_errors=True) as temp_dir:
        env = dict(os.environ)
        env["CODEX_HOME"] = temp_dir

        # 1. codex plugin marketplace add <repo-worktree-path>
        log("Adding local marketplace...")
        res = subprocess.run([codex_bin, "plugin", "marketplace", "add", str(ROOT)],
                             capture_output=True, text=True, env=env, shell=(os.name == "nt"))
        assert res.returncode == 0, f"marketplace add failed: {res.stderr}"

        # 2. codex plugin marketplace list
        log("Listing marketplaces...")
        res = subprocess.run([codex_bin, "plugin", "marketplace", "list"],
                             capture_output=True, text=True, env=env, shell=(os.name == "nt"))
        assert res.returncode == 0, f"marketplace list failed: {res.stderr}"
        assert "vibe-wise" in res.stdout, f"vibe-wise not listed: {res.stdout}"

        # 3. codex plugin add vibe-wise@vibe-wise
        log("Installing vibe-wise plugin...")
        res = subprocess.run([codex_bin, "plugin", "add", "vibe-wise@vibe-wise"],
                             capture_output=True, text=True, env=env, shell=(os.name == "nt"))
        assert res.returncode == 0, f"plugin add failed: {res.stderr}"

        # 4. codex plugin list
        log("Checking plugin list...")
        res = subprocess.run([codex_bin, "plugin", "list"],
                             capture_output=True, text=True, env=env, shell=(os.name == "nt"))
        assert res.returncode == 0, f"plugin list failed: {res.stderr}"
        assert "vibe-wise@vibe-wise" in res.stdout, f"Plugin not installed: {res.stdout}"

        # 5. codex app-server --stdio JSON-RPC inspection
        log("Testing app-server stdio JSON-RPC (skills/list & hooks/list)...")
        proc = subprocess.Popen(
            [codex_bin, "app-server", "--stdio"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", env=env, shell=(os.name == "nt"),
        )
        try:
            def send(obj):
                proc.stdin.write(json.dumps(obj) + "\n")
                proc.stdin.flush()

            send({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"clientInfo": {"name": "verify", "version": "1.0"}}})
            init_line = proc.stdout.readline()
            init_data = json.loads(init_line)
            assert init_data.get("id") == 0, f"Unexpected init response: {init_line}"

            # skills/list
            send({"jsonrpc": "2.0", "id": 1, "method": "skills/list", "params": {"cwds": [str(ROOT)], "forceReload": True}})
            skills_found = set()
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                data = json.loads(line)
                if data.get("id") == 1:
                    result = data.get("result", {})
                    for entry in result.get("data", []):
                        for s in entry.get("skills", []):
                            name = s.get("name")
                            if name in ("vibe-wise:learn", "vibe-wise:reset"):
                                skills_found.add(name)
                    break
            assert "vibe-wise:learn" in skills_found, f"vibe-wise:learn not discovered: {skills_found}"
            assert "vibe-wise:reset" in skills_found, f"vibe-wise:reset not discovered: {skills_found}"
            log("[OK] Discovered skills via JSON-RPC: " + ", ".join(sorted(skills_found)))

            # hooks/list
            send({"jsonrpc": "2.0", "id": 2, "method": "hooks/list", "params": {}})
            hook_found = False
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                data = json.loads(line)
                if data.get("id") == 2:
                    result = data.get("result", {})
                    for entry in result.get("data", []):
                        for h in entry.get("hooks", []):
                            if "vibe-wise" in h.get("pluginId", "") and h.get("eventName") == "sessionStart":
                                hook_found = True
                                assert h.get("trustStatus") == "untrusted", \
                                    f"Hook should remain untrusted until user review, got: {h.get('trustStatus')}"
                                assert h.get("matcher") == "startup|resume|clear|compact"
                    break
            assert hook_found, "VibeWise sessionStart hook was not reported by hooks/list"
            log("[OK] Verified sessionStart hook reported with untrusted status until user review")

        finally:
            try:
                proc.stdin.close()
            except Exception:
                pass
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                               capture_output=True, check=False)
            else:
                proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                pass

    log("[OK] Live smoke verification completed cleanly and temporary directory removed.")


def main():
    log("Beginning VibeWise Codex verification...")
    verify_static()
    verify_live()
    log("All checks passed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
