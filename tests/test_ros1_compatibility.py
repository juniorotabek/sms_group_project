from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TERMS = ["rcl" + "py", "ros" + "2", "a" + "ment", "col" + "con", ".launch" + ".py"]
REQUIRED_TERMS = ["rospy", "roslaunch", "rosrun", "rosbag", "rostopic", "catkin"]


def iter_runtime_files():
    scan_roots = [
        ROOT / "src",
        ROOT / "scripts",
        ROOT / "launch",
        ROOT / "docs",
        ROOT / "README.md",
        ROOT / "package.xml",
        ROOT / "CMakeLists.txt",
        ROOT / "setup.py",
    ]
    for root in scan_roots:
        if not root.exists():
            continue
        paths = root.rglob("*") if root.is_dir() else [root]
        for path in paths:
            if path.is_dir():
                continue
            if "legacy_ros2_reference" in path.parts:
                continue
            if any(part in {".git", "build", "devel", "install", "log", "logs", "__pycache__"} for part in path.parts):
                continue
            yield path


def test_no_forbidden_ros2_terms_in_runtime_files() -> None:
    violations: list[str] = []
    for path in iter_runtime_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line in text.splitlines():
            normalized_line = line.strip()
            if "validate no-ros2" in normalized_line or "validate_no_ros2" in normalized_line:
                continue
            for term in FORBIDDEN_TERMS:
                if term in normalized_line:
                    violations.append(f"{path.relative_to(ROOT)} contains forbidden term '{term}'")
    assert not violations, "ROS 1 compatibility violations found:\n" + "\n".join(violations)


def test_required_ros1_terms_exist_somewhere() -> None:
    combined_text: list[str] = []
    for path in iter_runtime_files():
        try:
            combined_text.append(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue
    all_text = "\n".join(combined_text)
    missing = [term for term in REQUIRED_TERMS if term not in all_text]
    assert not missing, f"Expected ROS 1 terms not found in project files: {missing}"
