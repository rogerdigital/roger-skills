"""Validate the repository's executable skill contracts."""

from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

import yaml


DANGEROUS_TOOLS = [
    r"rm\s+-[rf]{1,2}f?",
    r"--no-verify",
    r"curl\b.*\|\s*(?:bash|sh)",
    r"wget\b.*\|\s*(?:bash|sh)",
    r"sudo\s+rm",
    r":\s*\(\)\s*\{.*\}\s*;",
    r"mkfs\b",
    r"dd\s+if=",
]
ACTION = (
    r"\b(?:search(?:\s+for)?|find|locate|read|extract|collect|gather|grep|scan|"
    r"look\s+for|retrieve|fetch|access|dump|list|cat|harvest)\b"
)
SENSITIVE_TARGETS = [
    (
        r"(?:api[\s_-]*key|access[\s_-]*key|secret[\s_-]*key|private[\s_-]*key|"
        r"auth(?:entication)?[\s_-]*token|bearer[\s_-]*token|\.env\b|credential|"
        r"password|passwd|passphrase)",
        "credentials/secrets",
    ),
    (
        r"(?:personal[\s_-]*info(?:rmation)?|id[\s_-]*card|passport\b|date[\s_-]*of[\s_-]*birth|"
        r"\bssn\b|social[\s_-]*security|home[\s_-]*address|phone[\s_-]*number|"
        r"mobile[\s_-]*number)",
        "personal information",
    ),
    (
        r"(?:account[\s_-]*number|credit[\s_-]*card|bank[\s_-]*account|"
        r"billing[\s_-]*info(?:rmation)?|payment[\s_-]*info(?:rmation)?|card[\s_-]*number|"
        r"cvv\b|routing[\s_-]*number)",
        "account/financial information",
    ),
    (
        r"(?:confidential|proprietary|internal[\s_-]*doc(?:ument)?|client[\s_-]*data|"
        r"employee[\s_-]*record|salary\b|payroll\b|trade[\s_-]*secret|nda\b)",
        "company/work information",
    ),
]
EXFILTRATION = [
    (
        r"\b(?:send|upload|post|transmit|exfiltrate|forward)\b[^.!?;,\n]*?\bto\s+https?://",
        "exfiltration to external URL",
    ),
    (r"curl\b[^`\n]*-[xX]\s*POST[^`\n]*https?://", "curl POST to external URL"),
    (r"wget\b[^`\n]*--post[^`\n]*https?://", "wget POST to external URL"),
]
SHELL_COMMANDS = {
    "bundle", "cargo", "cat", "composer", "find", "gh", "git", "go", "gradle", "grep",
    "head", "ls", "make", "mvn", "npm", "pip", "pip-audit", "pnpm", "poetry", "pytest",
    "python", "python3", "sed", "wc", "yarn",
}
OPEN_FENCE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>[^\n]*)$")
IGNORE_MARKER = re.compile(
    r'^\s*<!--\s*skill-validator:\s*ignore-shell\s+reason="[^"\n]*\S[^"\n]*"\s*-->\s*$'
)
ANY_IGNORE_MARKER = re.compile(r"skill-validator:\s*ignore-shell")
README_SKILL_LINK = re.compile(r"\[([^\]]+)\]\(skills/([^/]+)/SKILL\.md\)")
ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
CHMOD_OPTIONS = {
    "-R", "--recursive", "-f", "-v", "-c", "--changes", "--silent", "--quiet", "--verbose",
    "--preserve-root", "--no-preserve-root", "--help", "--version",
}
CHMOD_OPTIONS_WITH_ARGUMENT = {"--reference"}
COMMAND_OPTIONS = {"-p", "-v", "-V"}


def relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def extract_frontmatter(content: str) -> tuple[str, str, int] | None:
    if not content.startswith("---\n"):
        return None
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", content, re.DOTALL)
    if not match:
        return ("", "", 0)
    return match.group(1), content[match.end() :], content[: match.end()].count("\n") + 1


def extract_bash_patterns(value: object) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"Bash\(([^)]*)\)", str(value))]


def split_shell_segments(line: str) -> list[tuple[str, str | None]]:
    segments: list[tuple[str, str | None]] = []
    start = 0
    index = 0
    quote: str | None = None
    in_word = False
    preceding_connector: str | None = None
    while index < len(line):
        character = line[index]
        if quote:
            if character == "\\" and quote == '"':
                in_word = True
                index += 2
                continue
            if character == quote:
                quote = None
            else:
                in_word = True
            index += 1
            continue
        if character == "\\":
            in_word = True
            index += 2
            continue
        if character in {"'", '"'}:
            quote = character
            in_word = True
            index += 1
            continue
        if character.isspace():
            in_word = False
            index += 1
            continue
        if character == "#" and not in_word:
            break

        connector_length = 0
        if character == "&":
            if index + 1 < len(line) and line[index + 1] == "&":
                connector_length = 2
            elif (index > 0 and line[index - 1] in "><") or (
                index + 1 < len(line) and line[index + 1] in "><"
            ):
                in_word = True
                index += 1
                continue
            else:
                connector_length = 1
        elif character == "|":
            connector_length = 2 if index + 1 < len(line) and line[index + 1] in "|&" else 1
        elif character == ";":
            connector_length = 1

        if connector_length:
            segment = line[start:index].strip()
            if segment:
                segments.append((segment, preceding_connector))
            preceding_connector = line[index : index + connector_length]
            index += connector_length
            start = index
            in_word = False
            continue
        in_word = True
        index += 1
    segment = line[start:index].strip()
    if segment:
        segments.append((segment, preceding_connector))
    return segments


def normalize_shell_command(segment: str) -> str | None:
    tokens = shlex.split(segment, posix=True, comments=False)
    while tokens and ENV_ASSIGNMENT.match(tokens[0]):
        tokens.pop(0)
    if not tokens:
        return None
    return " ".join(tokens)


def covers_command(command: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if command == pattern:
            return True
        if pattern.endswith(" *") and (
            command == pattern[:-2] or command.startswith(pattern[:-1])
        ):
            return True
    return False


def fenced_blocks(path: str, body: str, body_start_line: int) -> tuple[list[tuple[int, str, str, bool]], list[str]]:
    lines = body.splitlines()
    blocks: list[tuple[int, str, str, bool]] = []
    errors: list[str] = []
    index = 0
    while index < len(lines):
        opening = OPEN_FENCE.match(lines[index])
        if not opening:
            index += 1
            continue
        fence = opening.group("fence")
        info = opening.group("info").strip()
        language = info.split(maxsplit=1)[0].lower() if info else ""
        closing = re.compile(
            r"^ {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}[ \t]*$"
        )
        end = index + 1
        while end < len(lines) and not closing.match(lines[end]):
            end += 1
        if end == len(lines):
            errors.append(f"{path}:{body_start_line + index}: unclosed fenced block")
            break
        ignored = index > 0 and bool(IGNORE_MARKER.match(lines[index - 1]))
        blocks.append((body_start_line + index, language, "\n".join(lines[index + 1 : end]), ignored))
        index = end + 1
    return blocks, errors


def invalid_bash_pattern(pattern: str) -> str | None:
    if not pattern:
        return "Bash permission pattern must not be empty"
    if pattern.startswith("*"):
        return "Bash permission pattern must not begin with '*'"
    if any(character in pattern for character in "?[]"):
        return "invalid Bash permission pattern; ?, [, and ] are not allowed"
    wildcard_count = pattern.count("*")
    if wildcard_count == 0:
        return None
    if wildcard_count == 1 and pattern.endswith(" *") and pattern[:-2]:
        return None
    return "invalid Bash permission pattern; only one final ' *' argument wildcard is allowed"


def unsafe_chmod_mode(tokens: list[str]) -> str | None:
    index = 1
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            index += 1
            break
        if token in CHMOD_OPTIONS_WITH_ARGUMENT:
            index += 2
            continue
        if any(token.startswith(f"{option}=") for option in CHMOD_OPTIONS_WITH_ARGUMENT):
            index += 1
            continue
        if token in CHMOD_OPTIONS or (
            token.startswith("-")
            and not token.startswith("--")
            and len(token) > 1
            and set(token[1:]) <= {"R", "f", "v", "c"}
        ):
            index += 1
            continue
        break
    if index >= len(tokens):
        return None
    mode = tokens[index]
    if re.fullmatch(r"[0-7]+", mode) and mode[-1] in "2367":
        return f"world-writable chmod mode '{mode}'"
    for clause in mode.split(","):
        match = re.fullmatch(r"(?P<who>[ugoa]*)(?P<operator>[+=])(?P<permissions>[rwxXstugo]+)", clause)
        if match and "w" in match.group("permissions"):
            who = match.group("who")
            if not who or "o" in who or "a" in who:
                return f"world-writable chmod clause '{clause}'"
    return None


def unwrap_command_tokens(tokens: list[str]) -> list[str]:
    index = 0
    while index < len(tokens) and ENV_ASSIGNMENT.match(tokens[index]):
        index += 1
    while index < len(tokens):
        if tokens[index] == "command":
            index += 1
            if index < len(tokens) and tokens[index] == "--":
                index += 1
            while index < len(tokens) and tokens[index] in COMMAND_OPTIONS:
                index += 1
            continue
        if tokens[index] != "env":
            break
        index += 1
        while index < len(tokens):
            token = tokens[index]
            if token == "--":
                index += 1
                break
            if ENV_ASSIGNMENT.match(token):
                index += 1
                continue
            if token in {"-u", "--unset", "-C", "--chdir"}:
                index += 2
                continue
            if (
                token.startswith("-u") and len(token) > 2
            ) or token.startswith("--unset=") or token.startswith("--chdir="):
                index += 1
                continue
            if token.startswith("-"):
                index += 1
                continue
            break
    return tokens[index:]


def dangerous_command_reason(command: str) -> str | None:
    try:
        tokens = shlex.split(command, posix=True, comments=False)
    except ValueError:
        return None
    tokens = unwrap_command_tokens(tokens)
    if len(tokens) >= 2 and tokens[:2] == ["git", "push"]:
        if any(
            option.startswith("--force")
            or (option.startswith("-") and not option.startswith("--") and "f" in option[1:])
            for option in tokens[2:]
        ):
            return "force push"
    if tokens and tokens[0] == "rm":
        recursive = any(
            option == "--recursive"
            or option in {"-r", "-R"}
            or (
                option.startswith("-")
                and not option.startswith("--")
                and any(flag in option[1:] for flag in "rR")
            )
            for option in tokens[1:]
        )
        if recursive:
            return "recursive rm"
    if tokens and tokens[0] == "chmod":
        return unsafe_chmod_mode(tokens)
    for pattern in DANGEROUS_TOOLS:
        if re.search(pattern, " ".join(tokens), re.IGNORECASE):
            return f"matched pattern '{pattern}'"
    return None


def check_security(path: str, content: str, frontmatter: dict[object, object]) -> list[str]:
    errors: list[str] = []
    allowed_tools = frontmatter.get("allowed-tools", "")
    if isinstance(allowed_tools, str):
        for command in extract_bash_patterns(allowed_tools):
            if reason := dangerous_command_reason(command):
                errors.append(f"{path}: dangerous command in allowed-tools: {reason}")

    if frontmatter.get("security-audit") is True:
        return errors
    clauses = re.split(r"[.!?;,\n]+", content.lower())
    negation = re.compile(r"\b(?:do not|don't|never|avoid|without)\s*$")
    for clause in clauses:
        for target_pattern, category in SENSITIVE_TARGETS:
            pattern = re.compile(
                rf"(?P<action>{ACTION})[^.!?;,\n]{{0,120}}{target_pattern}", re.IGNORECASE
            )
            for match in pattern.finditer(clause):
                if negation.search(clause[: match.start("action")]):
                    continue
                errors.append(f"{path}: suspicious intent — instruction to collect {category} detected")
        for pattern, label in EXFILTRATION:
            for match in re.finditer(pattern, clause, re.IGNORECASE):
                if negation.search(clause[: match.start()]):
                    continue
                errors.append(f"{path}: suspicious intent — {label} detected")
    return errors


def check_shell_blocks(
    path: str, body: str, body_start_line: int, bash_patterns: list[str]
) -> list[str]:
    errors: list[str] = []
    for number, line in enumerate(body.splitlines(), start=body_start_line):
        if ANY_IGNORE_MARKER.search(line) and not IGNORE_MARKER.match(line):
            errors.append(f"{path}:{number}: invalid ignore-shell marker; reason must be nonempty and quoted")

    blocks, fence_errors = fenced_blocks(path, body, body_start_line)
    errors.extend(fence_errors)
    for line_number, language, block, ignored in blocks:
        is_shell = language in {"bash", "sh"}
        if language and not is_shell:
            continue
        for offset, line in enumerate(block.splitlines()):
            context = f"{path}:{line_number + 1 + offset}"
            try:
                segments = split_shell_segments(line)
                commands_with_connectors = [
                    (command, connector)
                    for segment, connector in segments
                    if (command := normalize_shell_command(segment))
                ]
            except ValueError as error:
                errors.append(f"{context}: invalid shell syntax — {error}")
                continue
            commands = [command for command, _ in commands_with_connectors]
            if not is_shell:
                commands = [
                    command for command in commands if command.split(maxsplit=1)[0] in SHELL_COMMANDS
                ]
            if not commands:
                continue
            if not is_shell:
                errors.append(f"{context}: shell command in fenced block must be labelled bash or sh")
                continue
            for index, (command, connector) in enumerate(commands_with_connectors):
                if index == 0 or connector not in {"|", "|&"}:
                    continue
                preceding_command = commands_with_connectors[index - 1][0]
                if (
                    preceding_command.split(maxsplit=1)[0] in {"curl", "wget"}
                    and command.split(maxsplit=1)[0] in {"bash", "sh"}
                ):
                    errors.append(f"{context}: dangerous command: download-to-shell pipeline")
            for command in commands:
                if reason := dangerous_command_reason(command):
                    errors.append(f"{context}: dangerous command: {reason}")
            if ignored:
                continue
            for command in commands:
                if not covers_command(command, bash_patterns):
                    errors.append(f"{context}: command '{command}' is not covered by allowed-tools")
    return errors


def readme_skill_links(readme: str) -> list[tuple[str, str]]:
    section = re.search(r"^## Skills[ \t]*$", readme, re.MULTILINE)
    if not section:
        return []
    following = readme[section.end() :]
    next_section = re.search(r"^#{1,2}\s+", following, re.MULTILINE)
    section_text = following[: next_section.start()] if next_section else following
    return README_SKILL_LINK.findall(section_text)


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    skill_files = sorted((root / "skills").glob("*/SKILL.md"))
    if not skill_files:
        return ["skills: no SKILL.md files found"]

    names: dict[str, str] = {}
    directories: set[str] = set()
    for skill_path in skill_files:
        path = relative_path(root, skill_path)
        directory = skill_path.parent.name
        directories.add(directory)
        content = skill_path.read_text(encoding="utf-8")
        extracted = extract_frontmatter(content)
        if extracted is None:
            errors.append(f"{path}: missing frontmatter (must start with ---)")
            continue
        frontmatter_text, body, body_start_line = extracted
        if body_start_line == 0:
            errors.append(f"{path}: frontmatter block not closed with ---")
            continue
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as error:
            errors.append(f"{path}: invalid YAML in frontmatter — {error}")
            continue
        if not isinstance(frontmatter, dict):
            errors.append(f"{path}: frontmatter must be a YAML mapping")
            continue
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{path}: missing required field 'name'")
        else:
            if name in names:
                errors.append(f"{path}: duplicate skill name '{name}' (also in {names[name]})")
            else:
                names[name] = path
            if name != directory:
                errors.append(f"{path}: name '{name}' does not match directory '{directory}'")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{path}: missing required field 'description'")
        if not body.strip():
            errors.append(f"{path}: skill body is empty")
            continue

        allowed_tools = frontmatter.get("allowed-tools", "")
        if "allowed-tools" in frontmatter and not isinstance(allowed_tools, str):
            errors.append(f"{path}: allowed-tools must be a string")
            allowed_tools = ""
        errors.extend(check_security(path, content, frontmatter))
        bash_patterns = extract_bash_patterns(allowed_tools)
        for pattern in bash_patterns:
            if error := invalid_bash_pattern(pattern):
                errors.append(f"{path}: {error}: {pattern}")
        errors.extend(check_shell_blocks(path, body, body_start_line, bash_patterns))

    readme_path = root / "README.md"
    skill_links: list[tuple[str, str]] = []
    if readme_path.exists():
        skill_links = readme_skill_links(readme_path.read_text(encoding="utf-8"))
    linked_directories = {directory for _, directory in skill_links}
    duplicate_links = sorted(
        directory for directory in linked_directories if sum(link[1] == directory for link in skill_links) > 1
    )
    if duplicate_links:
        errors.append(f"README duplicate skill links: {', '.join(duplicate_links)}")
    for label, directory in skill_links:
        if label != directory:
            errors.append(f"README skill link label '{label}' does not match directory '{directory}'")
    missing = sorted(directories - linked_directories)
    stale = sorted(linked_directories - directories)
    if missing:
        errors.append(f"README missing skill links: {', '.join(missing)}")
    if stale:
        errors.append(f"README stale skill links: {', '.join(stale)}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_repository(root)
    if errors:
        print("Validation failed:\n")
        for error in errors:
            print(f"  ✗ {error}")
        return 1
    count = len(list((root / "skills").glob("*/SKILL.md")))
    print(f"All {count} SKILL.md files passed validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
