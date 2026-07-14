"""Fast, credential-free repository checks for local use and CI."""

import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def share_files() -> list[Path]:
    """Return tracked files in Git, or all files before the repository is initialized."""
    if (ROOT / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]

    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and "session" not in path.relative_to(ROOT).parts
    ]


class RepositoryChecks(unittest.TestCase):
    def test_vendor_neutral_ai_entry_points_exist(self) -> None:
        required = [
            ROOT / "AGENTS.md",
            ROOT / "CLAUDE.md",
            ROOT / "GEMINI.md",
            ROOT / ".github" / "copilot-instructions.md",
            ROOT / ".cursor" / "rules" / "project.mdc",
            ROOT / "SETUP.md",
            ROOT / "bin" / "doctor.ps1",
        ]
        self.assertEqual([], [str(path.relative_to(ROOT)) for path in required if not path.is_file()])

    def test_open_agent_skills_have_valid_names_and_metadata(self) -> None:
        skills_root = ROOT / ".agents" / "skills"
        skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
        self.assertTrue(skill_dirs)
        for skill_dir in skill_dirs:
            with self.subTest(skill=skill_dir.name):
                self.assertRegex(skill_dir.name, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
                content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                self.assertRegex(content, rf"(?m)^name:\s*{re.escape(skill_dir.name)}\s*$")
                self.assertRegex(content, r"(?m)^description:\s*(?:>|\S)")

    def test_claude_adapters_cover_canonical_skills_and_roles(self) -> None:
        canonical_skills = {
            path.name for path in (ROOT / ".agents" / "skills").iterdir() if path.is_dir()
        }
        claude_skills = {
            path.name for path in (ROOT / ".claude" / "skills").iterdir() if path.is_dir()
        }
        canonical_roles = {
            path.name for path in (ROOT / ".agents" / "roles").glob("*.md")
        }
        claude_roles = {
            path.name for path in (ROOT / ".claude" / "agents").glob("*.md")
        }
        self.assertEqual(canonical_skills, claude_skills)
        self.assertEqual(canonical_roles, claude_roles)

    def test_canonical_guidance_does_not_depend_on_claude_paths(self) -> None:
        canonical_files = [ROOT / "AGENTS.md", ROOT / "SETUP.md"]
        canonical_files.extend((ROOT / ".agents").rglob("*.md"))
        violations = []
        for path in canonical_files:
            text = path.read_text(encoding="utf-8").lower()
            if ".claude/skills" in text or ".claude\\skills" in text:
                violations.append(str(path.relative_to(ROOT)))
        self.assertEqual([], violations)

    def test_current_bot_portal_is_documented(self) -> None:
        env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
        setup_guide = (ROOT / "SETUP.md").read_text(encoding="utf-8")
        self.assertIn("https://portal.api.bot.or.th/", env_example)
        self.assertIn("https://portal.api.bot.or.th/", setup_guide)
        self.assertNotIn("https://iapi.bot.or.th/", env_example)

    def test_python_files_compile(self) -> None:
        for path in ROOT.rglob("*.py"):
            relative = path.relative_to(ROOT)
            if any(part in {".git", "__pycache__", "session"} for part in relative.parts):
                continue
            with self.subTest(path=relative):
                compile(path.read_text(encoding="utf-8"), str(relative), "exec")

    def test_json_files_parse(self) -> None:
        for path in ROOT.rglob("*.json"):
            if ".git" in path.parts:
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                json.loads(path.read_text(encoding="utf-8"))

    def test_private_binary_artifacts_are_not_shared(self) -> None:
        forbidden_names = {".env", "x13as.exe"}
        forbidden_suffixes = {".otf", ".ttf", ".whl", ".pyc"}
        violations = [
            str(path.relative_to(ROOT))
            for path in share_files()
            if path.name in forbidden_names or path.suffix.lower() in forbidden_suffixes
        ]
        self.assertEqual([], violations)

    def test_no_absolute_windows_user_paths(self) -> None:
        pattern = re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE)
        violations = []
        for path in share_files():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if pattern.search(text):
                violations.append(str(path.relative_to(ROOT)))
        self.assertEqual([], violations)

    def test_env_example_contains_placeholders_only(self) -> None:
        values = []
        for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and "=" in line:
                values.append(line.split("=", 1)[1])
        self.assertTrue(values)
        self.assertTrue(all(value.startswith("your_") for value in values))

    def test_ceic_dependency_is_optional(self) -> None:
        core = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
        optional = (ROOT / "requirements-ceic.txt").read_text(encoding="utf-8").lower()
        self.assertNotIn("ceic-api-client", core)
        self.assertIn("ceic-api-client", optional)


if __name__ == "__main__":
    unittest.main()
