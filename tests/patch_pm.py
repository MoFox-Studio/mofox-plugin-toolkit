"""Patch package_manager.py to apply remaining edits (2 and 3)."""
from pathlib import Path

FPATH = Path("mpdt/utils/managers/package_manager.py")

content = FPATH.read_text(encoding="utf-8")

# --- Edit 2: modify collect_files signature ---
OLD_SIG = "    def collect_files(self, with_docs: bool = False) -> list[Path]:"
NEW_SIG = '    def collect_files(self, with_docs: bool = False, output_dir: str = "dist") -> list[Path]:'
assert OLD_SIG in content, "Edit 2a: old signature not found"
content = content.replace(OLD_SIG, NEW_SIG)
print("Edit 2a: signature updated")

# --- Edit 2: modify collect_files body ---
# Replace the entire collect_files method body.
# Old body from "递归收集" to "return files" before calculate_sha256
OLD_BODY_START = '        """递归收集插件目录中需要打包的文件列表'
OLD_BODY_END = '        return files'
NEW_BODY = '''        """递归收集插件目录中需要打包的文件列表
        
        Args:
            with_docs: 是否包含文档文件
            output_dir: 输出目录名称，根级别的该目录将被排除
            
        Returns:
            文件路径列表（绝对路径）
        """
        files: list[Path] = []
        
        for item in sorted(self.plugin_path.rglob("*")):
            relative = item.relative_to(self.plugin_path)
            parts = relative.parts
            
            # 根级别的输出目录跳过
            if len(parts) >= 1 and parts[0] == output_dir:
                continue
            
            # 根级别的 README 始终包含，不受 with_docs 控制
            if len(parts) == 1 and item.is_file() and item.name in ("README.md", "README.rst"):
                files.append(item)
                continue
            
            excluded = False
            for part in parts:
                part_path = Path(part)
                if self.is_excluded(part_path, with_docs):
                    excluded = True
                    break
            
            if excluded:
                continue
            
            if item.is_file():
                files.append(item)
        
        return files'''

# Find old body start and end
start_idx = content.find(OLD_BODY_START)
assert start_idx != -1, "Edit 2b: old body start not found"
# Find the "return files" that closes collect_files
end_marker = OLD_BODY_END
# Find from start_idx, then match the next occurrence of end_marker
# Actually we need the "return files" that belongs to collect_files, not later ones
# The old collect_files has its own "return files" at the method end
# Let's find from after the start
search_from = content.find('    def calculate_sha256', start_idx)
assert search_from != -1, "Edit 2b: calculate_sha256 not found after collect_files"
# The old body is from start_idx to the line before calculate_sha256
old_body = content[start_idx:search_from]
# Remove trailing blank lines
old_body = old_body.rstrip('\n')

NEW_BODY_FULL = NEW_BODY + '\n    '  # add the newline before next method

assert old_body in content, f"Edit 2b: old body not found in content. Length: {len(old_body)}"
content = content.replace(old_body, NEW_BODY_FULL.rstrip('\n'))
print("Edit 2b: body updated")

# --- Edit 3: modify build_package call ---
OLD_CALL = "        # 收集文件\n        files = self.collect_files(with_docs)"
NEW_CALL = "        # 收集文件（根级别 output_dir 会被排除，根级别 README 始终包含）\n        output_dir_name = Path(output_dir).name\n        files = self.collect_files(with_docs, output_dir=output_dir_name)"
assert OLD_CALL in content, "Edit 3: old call not found"
content = content.replace(OLD_CALL, NEW_CALL)
print("Edit 3: call updated")

FPATH.write_text(content, encoding="utf-8")
print("All edits applied successfully!")
