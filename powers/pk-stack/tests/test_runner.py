from __future__ import annotations

import json
import shutil
import sys
import threading
from pathlib import Path

import pytest

from pk_stack.models import CommandSpec
from pk_stack.runner import (
    CommandRejected,
    enforce_verification_policy,
    parse_command,
    run_command,
)


def test_parse_command_uses_argv_not_a_shell() -> None:
    assert parse_command('python -m pytest "tests/a file.py"') == (
        "python",
        "-m",
        "pytest",
        "tests/a file.py",
    )


def test_command_spec_argv_is_revalidated_before_execution(tmp_path: Path) -> None:
    contract = CommandSpec(
        argv=("bad\x00executable",),
        display="bad executable",
        source="explicit",
    )

    with pytest.raises(CommandRejected, match="NUL"):
        run_command(contract, root=tmp_path)


@pytest.mark.parametrize(
    "timeout_seconds",
    [float("inf"), float("-inf"), float("nan"), threading.TIMEOUT_MAX + 1],
)
def test_timeout_must_be_finite(tmp_path: Path, timeout_seconds: float) -> None:
    with pytest.raises(ValueError, match="positive, finite"):
        run_command(["pytest"], root=tmp_path, timeout_seconds=timeout_seconds)


def test_overlong_path_operand_is_structurally_rejected(tmp_path: Path) -> None:
    with pytest.raises(CommandRejected, match="inspect"):
        enforce_verification_policy(["pytest", "a" * 10_000], root=tmp_path)


@pytest.mark.parametrize(
    "command",
    [
        ["rm", "-rf", "build"],
        ["bash", "-c", "pytest"],
        ["bash", "-lc", "pytest"],
        ["bash", "verify.sh"],
        ["sh", "-cexit 0"],
        ["fish", "-C", "printf inline"],
        ["fish", "--init-command=printf inline"],
        ["ksh", "-c", "exit 0"],
        ["csh", "-c", "exit 0"],
        ["tcsh", "-c", "exit 0"],
        ["terraform", "destroy"],
        ["aws", "ec2", "terminate-instances"],
        ["env", "rm", "-rf", "build"],
        [sys.executable, "-c", "print('inline')"],
        [sys.executable, "-cprint('inline')"],
        [sys.executable, "-qm", "pk_stack", "version"],
        ["uv", "run", sys.executable, "-qm", "pk_stack", "version"],
        ["node", "-eprocess.exit(0)"],
        ["node", "--eval=process.exit(0)"],
        ["node", "-p", "process.exit(0)"],
        ["node", "--print=process.exit(0)"],
        ["perl", "-Eprint qq(inline)"],
        ["perl", "-we", "print qq(inline)"],
        ["ruby", "-we", "puts :inline"],
        ["ruby", "-W0e", "puts :inline"],
        ["ruby", "-W0eputs :inline"],
        ["ruby", "-I", "lib", "-e", "exit 0"],
        ["ruby", "-C", ".", "-e", "exit 0"],
        ["perl", "-I", "lib", "-e", "exit 0"],
        ["php", "-c", "php.ini", "-r", "exit(0);"],
        ["osascript", "-e", "return 0"],
        ["osascript", "-l", "JavaScript", "-e", "0"],
        ["uv", "run", "python", "-cprint('inline')"],
        ["uv", "run", "node", "--eval=process.exit(0)"],
        ["uv", "run", "node", "--print", "process.exit(0)"],
        ["uv", "run", "perl", "-we", "print qq(inline)"],
        ["uv", "run", "bash", "-lc", "pytest"],
        ["uv", "run", "sh", "-cexit 0"],
        ["uv", "run", "fish", "-Cprintf inline"],
        ["uv", "run", "fish", "--init-command", "printf inline"],
        ["uv", "run", "ksh", "-c", "exit 0"],
        ["uv", "run", "osascript", "-e", "return 0"],
        ["git", "clean", "-fdx"],
        ["gh", "api", "repos/example/project", "-X", "DELETE"],
        ["../outside/verifier"],
        [sys.executable, "../outside.py"],
        [sys.executable, "/tmp/outside.py"],
        ["uv", "run", "python", "../outside.py"],
        ["pytest", "--config=../outside.toml"],
        ["true"],
        ["echo", "proof"],
        ["printf", "proof"],
        ["projectctl", "version"],
        [".pk-stack/bin/projectctl", "version"],
        [sys.executable, "-m", "pk_stack"],
        [sys.executable, "--check-hash-based-pycs", "default", "-m", "pk_stack.cli"],
        ["uv", "run", "true"],
        ["uv", "run", "--quiet", "echo", "proof"],
        ["uv", "run", "-m", "pk_stack"],
        ["uv", "run", "-m", "-q", "pk_stack", "version"],
        ["uv", "run", "-qm", "pk_stack", "version"],
        ["uv", "run", "-mq", "pk_stack", "version"],
        ["uv", "run", "-vm", "pk_stack", "version"],
        ["uv", "run", "-s", "--help", "verify.py"],
        ["uv", "run", "--help"],
        ["uv", "run", "-h"],
        ["uv", "--version", "run", "pytest"],
        ["uv", "--help", "run", "pytest"],
        ["uv", "run", "--help", "pytest"],
        ["uv", "run", "-h", "pytest"],
        ["uv", "run", "-qh", "pytest"],
        ["uv", "run", "-hq", "pytest"],
        ["uv", "-qV"],
        ["sh", ".pk-stack/bin/projectctl", "version"],
        ["ksh", ".pk-stack/bin/projectctl", "version"],
        ["csh", ".pk-stack/bin/projectctl", "version"],
        ["tcsh", ".pk-stack/bin/projectctl", "version"],
        ["bash", "--debug", ".pk-stack/bin/projectctl", "version"],
        ["bash", "+O", "extglob", ".pk-stack/bin/projectctl", "version"],
        ["bash", "+o", "errexit", ".pk-stack/bin/projectctl", "version"],
        ["uv", "run", "sh", ".pk-stack/bin/projectctl", "version"],
        ["time", "pytest"],
        ["caffeinate", "pytest"],
        ["stdbuf", "pytest"],
        ["script", "pytest"],
        ["busybox", "sh", "verify.sh"],
        ["taskpolicy", "-b", "true"],
        ["sandbox-exec", "-p", "(version 1)(allow default)", "true"],
        ["uv", "run", "taskpolicy", "-b", "true"],
        ["uv", "run", "sandbox-exec", "-p", "(version 1)(allow default)", "true"],
        ["xcrun", "--run", "true"],
        ["arch", "-arm64", "/usr/bin/true"],
        ["uv", "run", "xcrun", "--run", "true"],
        ["uv", "run", "arch", "-arm64", "/usr/bin/true"],
        ["sh"],
        [sys.executable],
        [sys.executable, "-B"],
        [sys.executable, "--version"],
        [sys.executable, "-qV", "tests/test_runner.py"],
        [sys.executable, "-BV", "tests/test_runner.py"],
        [sys.executable, "-qh", "tests/test_runner.py"],
        ["node", "--version"],
        ["node", "--version", "verify.js"],
        ["node", "--no-warnings", "--version"],
        ["node", "--conditions", "development", "-e", "process.exit(0)"],
        ["node", "--input-type", "commonjs", "-e", "process.exit(0)"],
        ["ruby", "--encoding", "UTF-8", "-e", "exit 0"],
        ["node"],
        ["ruby"],
        ["perl"],
        ["php"],
        ["osascript"],
        ["uv", "run", "node"],
        ["git", "--version"],
        ["git", "--version", "status"],
        ["git", "-c", "color.ui=false", "--version"],
        ["git", "checkout", "--", "README.md"],
        ["git", "switch", "main"],
        ["git", "branch", "-D", "topic"],
        ["git", "tag", "-d", "v1"],
        ["git", "worktree", "remove", "tmp"],
        ["uv", "run", "git", "checkout", "--", "README.md"],
        ["pytest", "--version", "tests"],
        ["pytest", "-q", "--version"],
        ["python", "-m", "pytest", "--version"],
        ["uv", "run", "pytest", "-q", "--version"],
        ["make", "-C../outside", "verify"],
        ["cc", "verify.c", "-o../outside.bin"],
        ["uv", "run", "cc", "verify.c", "-o../outside.bin"],
        ["pytest", "-c../outside/pytest.ini"],
        ["git", "-C../outside", "status"],
        ["uv", "run", "-w../outside", "pytest"],
        ["uv", "run", "pytest", "-c../outside/pytest.ini"],
        ["python", "-X", "pycache_prefix=..", "verify.py"],
        ["python", "-Xpycache_prefix=../outside", "verify.py"],
        ["pytest", "--config=.."],
        ["find", "."],
        ["find", ".", "-name", "definitely-absent"],
        ["npm", "-v"],
        ["go", "version"],
        ["go", "--", "version"],
        ["go", "-C", ".", "version"],
        ["uv", "run", "go", "--", "version"],
        ["cargo", "-q", "-V"],
        ["uv", "run", "rustc", "-vV"],
        ["cargo", "-V", "ignored"],
        ["rustc", "-V", "ignored"],
        ["npm", "--silent", "-v"],
        ["pip3", "-V", "ignored"],
        ["swift", "-version", "ignored"],
        ["python", "-m", "pip", "-V", "ignored"],
        ["gcc", "-v"],
        ["coverage", "--version"],
        ["swift", "--version"],
        ["tox", "--version"],
        ["ruff", "-h"],
        ["ty", "-h"],
        ["cargo", "-h"],
        ["python", "-m", "unittest", "-h"],
        ["git", "config", "user.name", "example"],
        ["git", "remote", "add", "origin", "example.invalid/repo"],
        ["git", "update-index", "--refresh"],
        ["git", "update-ref", "refs/heads/example", "HEAD"],
        ["git", "-c", "alias.proof=!exit 0", "proof"],
        ["uv", "run", "git", "-c", "alias.proof=!exit 0", "proof"],
        ["git", "grep", "--open-files-in-pager=sh -c 'exit 0'", "needle"],
        ["uv", "run", "git", "grep", "-Osh", "needle"],
        ["git", "ls-remote", "--upload-pack=sh -c 'exit 0'", "example.invalid/repo"],
        ["git", "diff", "--ext-diff"],
        ["git", "grep", "--open-files-in-pag=sh -c 'exit 0'", "needle"],
        ["uv", "run", "git", "ls-remote", "--upload-p=sh", "."],
        ["git", "diff", "--output=escape"],
        ["uv", "run", "git", "log", "--out=escape"],
        ["git", "status", "--help"],
        ["uv", "run", "git", "diff", "--help"],
        ["cargo", "help"],
        ["uv", "run", "go", "help"],
        ["npm", "help"],
        ["pip3", "help"],
        ["ruff", "help"],
        ["pnpm", "help"],
        ["npm", "exec", "--", "projectctl", "version"],
        ["npx", "--no-install", "projectctl", "version"],
        ["pnpm", "exec", "sh", "-c", "exit 0"],
        ["pnpm", "dlx", "projectctl", "version"],
        ["uv", "run", "yarn", "exec", "projectctl", "version"],
        ["uvx", "--from", "pk-stack", "projectctl", "version"],
        ["uv", "run", "uvx", "pytest", "--version"],
        ["pytest", "-o", "addopts=--version"],
        ["uv", "run", "pytest", "--override-ini=addopts=--version"],
        ["python", "-m", "pytest", "-oaddopts=-h"],
        ["python", "-m", "runpy", "pk_stack"],
        ["uv", "run", "python", "-m", "runpy", "pk_stack.__main__"],
        ["python", "src/pk_stack/__main__.py", "version"],
        ["uv", "run", "python", "src/pk_stack/__main__.py", "version"],
        ["uv", "run", "src/pk_stack/__main__.py", "version"],
        ["python", ".pk-stack/projectctl/src/pk_stack/__main__.py", "version"],
        ["python", "src/pk_stack", "version"],
        ["uv", "run", "python", "src/pk_stack", "version"],
        ["python", ".pk-stack/projectctl/src/pk_stack", "version"],
        ["python", "src/pk_stack/__pycache__/__main__.pyc", "version"],
        ["pytest", "@../outside/args.txt"],
        ["pytest", "@args.txt"],
        ["uv", "run", "pytest", "@../outside/args.txt"],
        ["cc", "@args.txt"],
        ["python", "-m", "pytest", "@args.txt"],
        ["coverage", "run", "-m", "pk_stack", "version"],
        ["coverage", "run", "src/pk_stack/__main__.py", "version"],
        ["python", "-m", "coverage", "run", "-m", "pk_stack", "version"],
        ["python", "-m", "pip", "-V"],
        ["uv", "run", "python", "-m", "pip", "-V"],
        ["id"],
        ["hostname"],
        ["uname"],
        ["stat", "."],
        ["test", "-n", "fixed", "-o", "-f", "missing"],
        ["test", "fixed", "=", "fixed", "-o", "-f", "missing"],
        ["test", "-f", "missing", "-o", "fixed", "=", "fixed"],
        ["[", "fixed", "=", "fixed", "-o", "-f", "missing", "]"],
    ],
)
def test_verification_policy_rejects_destructive_or_escaping_commands(
    tmp_path: Path, command: list[str]
) -> None:
    with pytest.raises(CommandRejected):
        run_command(command, root=tmp_path)


@pytest.mark.parametrize(
    "command",
    [
        ["python3", "-Werror::DeprecationWarning", "verify.py"],
        ["perl", "verify.pl", "-MEncode"],
        ["ruby", "verify.rb", "-EUTF-8"],
        ["python", "verify.py", "-c", "config"],
        ["python", "-m", "pytest", "-c", "pyproject.toml"],
        ["uv", "run", "python", "-m", "pytest", "-c", "pyproject.toml"],
        ["node", "verify.js", "--eval", "config"],
        ["osascript", "verify.scpt", "-e", "config"],
        ["python", "verify.py", "--version"],
        ["grep", "-h", "needle", "README.md"],
        ["sort", "-V", "versions.txt"],
        ["git", "status", "--porcelain"],
        ["git", "diff", "--exit-code"],
        ["git", "-C", ".", "status"],
        ["git", "diff", "--", "README.md"],
        ["git", "diff", "--", "--help"],
        ["uv", "run", "git", "status", "--", "README.md"],
        ["coverage", "report", "--fail-under=80"],
        ["grep", "--", "--version", "README.md"],
        ["./verify", "--version"],
        ["grep", "-q", "@example.com", "README.md"],
        ["python", "verify.py", "@scope"],
        ["pytest", "--", "--basetemp=escape.tmp"],
        ["python", "-m", "pytest", "--", "--rootdir=escape.tmp"],
        ["uv", "run", "pytest", "--", "--confcutdir=escape.tmp"],
        ["cargo", "test", "--", "--manifest-path=escape.tmp"],
        ["npm", "test", "--", "--prefix=escape.tmp"],
    ],
)
def test_policy_does_not_scan_option_values_as_eval_clusters(
    tmp_path: Path,
    command: list[str],
) -> None:
    enforce_verification_policy(command, root=tmp_path)


def test_file_predicate_and_ls_human_flag_are_not_mistaken_for_help(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_text("proof\n", encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(target)

    enforce_verification_policy(["test", "-h", "link"], root=tmp_path)
    enforce_verification_policy(["[", "-h", "link", "]"], root=tmp_path)
    enforce_verification_policy(["ls", "-h", "target"], root=tmp_path)
    enforce_verification_policy(["test", "target", "-nt", "missing"], root=tmp_path)
    enforce_verification_policy(
        ["test", "-f", "target", "-a", "!", "-f", "missing"],
        root=tmp_path,
    )


@pytest.mark.parametrize(
    "command",
    [
        ["uv", "--directory", "run", "run", "true"],
        ["uv", "--project", "run", "run", "projectctl", "version"],
        ["uv", "--directory=run", "run", "--quiet", "echo", "proof"],
    ],
)
def test_uv_global_option_values_cannot_hide_denied_run_targets(
    tmp_path: Path,
    command: list[str],
) -> None:
    (tmp_path / "run").mkdir()

    with pytest.raises(CommandRejected):
        run_command(command, root=tmp_path)


def test_uv_nested_policy_does_not_treat_test_selectors_as_executables(tmp_path: Path) -> None:
    enforce_verification_policy(["uv", "run", "pytest", "-k", "time"], root=tmp_path)
    enforce_verification_policy(["uv", "run", "pytest", "-k", "script"], root=tmp_path)
    enforce_verification_policy(
        ["uv", "run", "python", "verify.py", "--directory=fixtures"],
        root=tmp_path,
    )


@pytest.mark.parametrize(
    "command",
    [
        ["./verify"],
        ["uv", "run", "./verify"],
    ],
)
def test_symlink_alias_cannot_turn_controller_into_evidence(
    tmp_path: Path,
    command: list[str],
) -> None:
    controller = tmp_path / ".pk-stack" / "bin" / "projectctl"
    controller.parent.mkdir(parents=True)
    controller.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    controller.chmod(0o755)
    (tmp_path / "verify").symlink_to(controller)

    with pytest.raises(CommandRejected, match="own verification"):
        run_command(command, root=tmp_path)


def test_explicit_relative_executable_symlink_cannot_use_path_identity_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside-verifier"
    project.mkdir()
    outside.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    outside.chmod(0o755)
    (project / "verify").symlink_to(outside)
    monkeypatch.setenv("PATH", str(project))

    with pytest.raises(CommandRejected, match="path operands"):
        run_command(["./verify"], root=project)


def test_project_named_pk_stack_can_run_an_unrelated_local_verifier(tmp_path: Path) -> None:
    project = tmp_path / "pk_stack"
    project.mkdir()
    verifier = project / "verify"
    verifier.write_text("#!/bin/sh\ntest -f proof.txt\n", encoding="utf-8")
    verifier.chmod(0o755)
    (project / "proof.txt").write_text("present\n", encoding="utf-8")

    assert run_command(["./verify"], root=project).passed is True


def test_git_external_pager_option_is_rejected_before_side_effect(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    marker = project / "git-pager-marker"

    with pytest.raises(CommandRejected, match="execute helpers"):
        run_command(
            [
                "git",
                "grep",
                f"--open-files-in-pager=sh -c 'touch {marker}'",
                "needle",
            ],
            root=project,
        )

    assert not marker.exists()


@pytest.mark.parametrize(
    ("scheme", "requirement_prefix"),
    [
        ("file", ""),
        ("git+file", ""),
        ("file", "sample @ "),
        ("git+file", "sample @ "),
    ],
)
def test_local_file_urls_cannot_escape_project_root(
    tmp_path: Path,
    scheme: str,
    requirement_prefix: str,
) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside package"
    project.mkdir()
    outside.mkdir()
    outside_url = requirement_prefix + outside.as_uri().replace("file:", f"{scheme}:", 1)

    with pytest.raises(CommandRejected, match="path operands"):
        enforce_verification_policy(
            ["uv", "run", "--with", outside_url, "python", "verify.py"],
            root=project,
        )


def test_nonlocal_file_url_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(CommandRejected, match="nonlocal file URL"):
        enforce_verification_policy(
            ["uv", "run", "--with", "file://example.invalid/package", "pytest"],
            root=tmp_path,
        )


def test_malformed_file_url_is_structurally_rejected(tmp_path: Path) -> None:
    with pytest.raises(CommandRejected, match="invalid URL"):
        enforce_verification_policy(
            ["uv", "run", "--with", "file://[invalid", "pytest"],
            root=tmp_path,
        )


def test_symlink_loop_path_is_structurally_rejected(tmp_path: Path) -> None:
    (tmp_path / "loop").symlink_to("loop")

    with pytest.raises(CommandRejected, match="unable to resolve"):
        enforce_verification_policy(["python", "loop"], root=tmp_path)


def test_project_local_file_url_remains_available(tmp_path: Path) -> None:
    local_package = tmp_path / "local package"
    local_package.mkdir()

    enforce_verification_policy(
        ["uv", "run", "--with", local_package.as_uri(), "python", "verify.py"],
        root=tmp_path,
    )


@pytest.mark.parametrize(
    "command",
    [
        ["uv", "run", "--env-file=escape.env", "python", "verify.py"],
        ["cargo", "--manifest-path=escape.toml", "test"],
        ["py.test", "--basetemp=escape.tmp"],
        ["python", "-m", "pytest", "--basetemp=escape.tmp"],
        ["uv", "run", "python", "-m", "py.test", "--rootdir=escape.tmp"],
        ["python", "-m", "unittest", "discover", "-sescape.tmp"],
        [
            "uv",
            "run",
            "python",
            "-m",
            "unittest",
            "discover",
            "--start-directory=escape.tmp",
        ],
        ["make", "--directory=escape.tmp", "test"],
        ["gmake", "--makefile=escape.tmp", "test"],
        ["pnpm", "--dir=escape.tmp", "test"],
        ["uv", "run", "make", "--file=escape.tmp", "test"],
        ["git", "--git-dir=escape.tmp", "status"],
        ["uv", "run", "git", "--work-tree=escape.tmp", "status"],
    ],
)
def test_known_long_option_paths_cannot_follow_outside_symlinks(
    tmp_path: Path,
    command: list[str],
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    option = next(token for token in command if "escape." in token)
    value = option.split("=", 1)[1] if "=" in option else option[option.index("escape.") :]
    suffix = Path(value).suffix
    outside = tmp_path / f"outside{suffix}"
    outside.write_text("outside\n", encoding="utf-8")
    (project / f"escape{suffix}").symlink_to(outside)

    with pytest.raises(CommandRejected, match="path operands"):
        enforce_verification_policy(command, root=project)


@pytest.mark.parametrize(
    "command",
    [
        ["uv", "--directory", "nested", "run", "python", "verify.py"],
        ["uv", "run", "--directory", "nested", "python", "verify.py"],
    ],
)
def test_uv_directory_cannot_change_path_resolution_root(
    tmp_path: Path, command: list[str]
) -> None:
    project = tmp_path / "project"
    nested = project / "nested"
    outside = tmp_path / "outside"
    nested.mkdir(parents=True)
    outside.mkdir()
    (outside / "verify.py").write_text("print('outside executed')\n", encoding="utf-8")
    (nested / "verify.py").symlink_to(outside / "verify.py")

    with pytest.raises(CommandRejected, match="uv --directory"):
        run_command(command, root=project)


@pytest.mark.parametrize("explicit_override", [False, True])
def test_uv_working_dir_environment_cannot_change_execution_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    explicit_override: bool,
) -> None:
    project = tmp_path / "project"
    nested = project / "nested"
    project.mkdir()
    nested.mkdir()
    (project / "verify.py").write_text("print('project proof')\n", encoding="utf-8")
    (nested / "verify.py").write_text("raise SystemExit('wrong cwd')\n", encoding="utf-8")
    monkeypatch.setenv("UV_WORKING_DIR", "nested")

    result = run_command(
        ["uv", "run", "python", "verify.py"],
        root=project,
        env={"UV_WORKING_DIR": "nested"} if explicit_override else None,
    )

    assert result.passed is True
    assert result.stdout == "project proof\n"


@pytest.mark.parametrize(
    "name",
    ["UV_CONFIG_FILE", "UV_ENV_FILE", "UV_PROJECT", "UV_WORKING_DIR"],
)
def test_uv_context_environment_is_not_inherited(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    probe = tmp_path / "probe.py"
    probe.write_text(
        f"import os\nprint(os.environ.get({name!r}, 'absent'))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(name, "../outside")

    result = run_command(
        ["uv", "run", "--no-project", sys.executable, "probe.py"],
        root=tmp_path,
        env={name: "../explicit-outside"},
    )

    assert result.passed is True
    assert result.stdout == "absent\n"


@pytest.mark.parametrize(
    "command",
    [
        ["test", "."],
        ["test", "-d", "."],
        ["[", "-e", ".", "]"],
        ["ls"],
        ["ls", "-la", "."],
        ["test", "-n", "fixed"],
        ["test", "fixed", "=", "fixed"],
        ["[", "fixed", "=", "fixed", "]"],
        ["uv", "run", "test", "-n", "fixed"],
    ],
)
def test_context_free_predicates_are_not_evidence(tmp_path: Path, command: list[str]) -> None:
    with pytest.raises(CommandRejected, match="project-specific"):
        enforce_verification_policy(command, root=tmp_path)


def test_run_command_returns_structured_success_and_failure(tmp_path: Path) -> None:
    (tmp_path / "success.py").write_text("print('proof')\n", encoding="utf-8")
    (tmp_path / "failure.py").write_text(
        "import sys\nprint('bad', file=sys.stderr)\nraise SystemExit(7)\n",
        encoding="utf-8",
    )
    success = run_command([sys.executable, "success.py"], root=tmp_path)
    failure = run_command([sys.executable, "failure.py"], root=tmp_path)

    assert success.passed is True
    assert success.exit_code == 0
    assert success.stdout == "proof\n"
    assert failure.passed is False
    assert failure.exit_code == 7
    assert failure.stderr == "bad\n"


def test_policy_allows_only_path_selected_absolute_executables(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected_test = shutil.which("test")
    assert selected_test is not None

    (tmp_path / "proof.txt").write_text("present\n", encoding="utf-8")
    accepted = run_command([selected_test, "-f", "proof.txt"], root=tmp_path)
    assert accepted.passed is True
    uv_accepted = run_command(["uv", "run", selected_test, "-f", "proof.txt"], root=tmp_path)
    assert uv_accepted.passed is True

    project = tmp_path / "project"
    selected_directory = tmp_path / "selected"
    other_directory = tmp_path / "other"
    for directory in (project, selected_directory, other_directory):
        directory.mkdir()
    selected = selected_directory / "verifier"
    other = other_directory / "verifier"
    for path in (selected, other):
        path.write_text('#!/bin/sh\ntest -f "$PWD/proof.txt"\n', encoding="utf-8")
        path.chmod(0o755)
    (project / "proof.txt").write_text("present\n", encoding="utf-8")
    monkeypatch.setenv("PATH", str(selected_directory))

    assert run_command([str(selected)], root=project).passed is True
    with pytest.raises(CommandRejected, match="path operands"):
        run_command([str(other)], root=project)


def test_run_command_times_out_and_bounds_output(tmp_path: Path) -> None:
    (tmp_path / "slow.py").write_text("import time\ntime.sleep(1)\n", encoding="utf-8")
    (tmp_path / "large.py").write_text("print('x' * 5000)\n", encoding="utf-8")
    timeout = run_command(
        [sys.executable, "slow.py"],
        root=tmp_path,
        timeout_seconds=0.01,
    )
    bounded = run_command(
        [sys.executable, "large.py"],
        root=tmp_path,
        output_limit=1024,
    )

    assert timeout.timed_out is True
    assert timeout.exit_code == 124
    assert bounded.passed is True
    assert bounded.truncated is True
    assert "bytes omitted" in bounded.stdout


@pytest.mark.parametrize(
    ("caller_set", "caller_value", "expected"),
    [("1", "/host/pythonpath", "/host/pythonpath"), ("0", "", None)],
)
def test_verifier_restores_wrapper_caller_pythonpath_and_applies_overrides(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caller_set: str,
    caller_value: str,
    expected: str | None,
) -> None:
    probe = tmp_path / "env.py"
    probe.write_text(
        "import json, os\n"
        "print(json.dumps({\n"
        "  'pythonpath': os.environ.get('PYTHONPATH'),\n"
        "  'set_marker': os.environ.get('PK_STACK_CALLER_PYTHONPATH_SET'),\n"
        "  'value_marker': os.environ.get('PK_STACK_CALLER_PYTHONPATH'),\n"
        "}))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONPATH", "/controller/src")
    monkeypatch.setenv("PK_STACK_CALLER_PYTHONPATH_SET", caller_set)
    monkeypatch.setenv("PK_STACK_CALLER_PYTHONPATH", caller_value)

    restored = run_command([sys.executable, "env.py"], root=tmp_path)
    overridden = run_command(
        [sys.executable, "env.py"],
        root=tmp_path,
        env={"PYTHONPATH": "/explicit/override"},
    )

    restored_payload = json.loads(restored.stdout)
    overridden_payload = json.loads(overridden.stdout)
    assert restored_payload == {
        "pythonpath": expected,
        "set_marker": None,
        "value_marker": None,
    }
    assert overridden_payload["pythonpath"] == "/explicit/override"
    assert overridden_payload["set_marker"] is None
    assert overridden_payload["value_marker"] is None
