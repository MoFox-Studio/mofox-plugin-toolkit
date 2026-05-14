"""
静态检查命令实现
"""

import json

from pathlib import Path

from rich.panel import Panel
from rich.table import Table

from mpdt.utils.color_printer import console, print_error, print_info, print_success, print_warning
from mpdt.utils.manifest_metadata import ensure_manifest_metadata_interactive
from mpdt.validators import (
    AutoFixValidator,
    ComponentValidator,
    ConfigValidator,
    MetadataValidator,
    StructureValidator,
    StyleValidator,
    TypeValidator,
    ValidationLevel,
    ValidationResult,
)


def check_plugin(
    plugin_path: str,
    level: str = "warning",
    auto_fix: bool = False,
    report_format: str = "console",
    output_path: str | None = None,
    skip_structure: bool = False,
    skip_metadata: bool = False,
    skip_component: bool = False,
    skip_type: bool = False,
    skip_style: bool = False,
    verbose: bool = False,
) -> None:
    """
    检查插件

    Args:
        plugin_path: 插件路径
        level: 显示级别 (error, warning, info)
        auto_fix: 自动修复
        report_format: 报告格式 (console, markdown)
        output_path: 输出路径
        skip_structure: 跳过结构检查
        skip_metadata: 跳过元数据检查
        skip_component: 跳过组件检查
        skip_type: 跳过类型检查
        skip_style: 跳过代码风格检查
        skip_security: 跳过安全检查
        verbose: 详细输出
    """
    path = Path(plugin_path).resolve()

    if not path.exists():
        print_error(f"插件路径不存在: {plugin_path}")
        return

    if not path.is_dir():
        print_error(f"插件路径不是目录: {plugin_path}")
        return

    console.print(Panel.fit(f"🔍 检查插件: [cyan]{path.name}[/cyan]", border_style="blue"))

    # 收集所有验证结果
    all_results: list[ValidationResult] = []

    # 结构验证
    if not skip_structure:
        print_info("正在检查插件结构...")
        validator = StructureValidator(path)
        result = validator.validate()
        all_results.append(result)
        _print_validation_summary(result, verbose)

    # 元数据验证
    if not skip_metadata:
        print_info("正在检查插件元数据...")
        manifest_path = path / "manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    manifest_data = json.load(f)
                ensure_manifest_metadata_interactive(path, manifest_data)
            except json.JSONDecodeError:
                pass
            except ValueError as e:
                print_error(str(e))
                return
        validator = MetadataValidator(path)
        result = validator.validate()
        all_results.append(result)
        _print_validation_summary(result, verbose)

    # 组件验证
    if not skip_component:
        print_info("正在检查组件元数据...")
        validator = ComponentValidator(path)
        result = validator.validate()
        all_results.append(result)
        _print_validation_summary(result, verbose)

    # 配置验证
    print_info("正在检查配置文件...")
    validator = ConfigValidator(path)
    result = validator.validate()
    all_results.append(result)
    _print_validation_summary(result, verbose)

    # 类型检查
    if not skip_type:
        print_info("正在进行类型检查...")
        validator = TypeValidator(path)
        result = validator.validate()
        all_results.append(result)
        _print_validation_summary(result, verbose)

    # 代码风格检查
    if not skip_style:
        print_info("正在检查代码风格...")
        validator = StyleValidator(path)
        result = validator.validate()
        all_results.append(result)
        _print_validation_summary(result, verbose)

    # 自动修复（如果启用）
    auto_fixer = None
    if auto_fix:
        print_info("正在应用自动修复...")
        auto_fixer = AutoFixValidator(path)
        fix_result = auto_fixer.fix_issues(all_results)

        # 从原始结果中移除已修复的问题（使用对象 id 比较）
        fixed_issue_ids = {id(issue) for issue in auto_fixer.fixed_issues}
        for result in all_results:
            result.issues = [issue for issue in result.issues if id(issue) not in fixed_issue_ids]
            # 更新计数
            result._update_counts()

        # 如果应用了 ruff 修复，移除所有可以被 ruff 修复的问题
        if any("ruff" in fix for fix in auto_fixer.fixes_applied):
            import re
            ruff_fixed_count = 0
            for result in all_results:
                original_count = len(result.issues)
                # 移除所有 ruff 错误格式的问题（如果建议包含"可自动修复"或问题本身就是 ruff 格式）
                result.issues = [
                    issue for issue in result.issues
                    if not (
                        re.match(r'^[A-Z]\d+:', issue.message) and
                        (issue.suggestion is None or "可自动修复" in issue.suggestion or "--fix" in issue.suggestion)
                    )
                ]
                ruff_fixed_count += original_count - len(result.issues)
                # 更新计数
                result._update_counts()

        # 显示修复摘要
        if auto_fixer.fixes_applied:
            print_success(f"  ✓ 成功修复 {len(auto_fixer.fixes_applied)} 个问题")
            if verbose:
                for fix in auto_fixer.fixes_applied:
                    console.print(f"    [green]✓[/green] {fix}")

        if auto_fixer.fixes_failed:
            print_warning(f"  ⚠ {len(auto_fixer.fixes_failed)} 个问题修复失败")
            if verbose:
                for fail in auto_fixer.fixes_failed:
                    console.print(f"    [yellow]✗[/yellow] {fail}")

        if not auto_fixer.fixes_applied and not auto_fixer.fixes_failed:
            print_info("  ℹ 未发现可自动修复的问题")

    # 生成总体报告
    _print_overall_report(all_results, level, auto_fixer)

    # 保存报告（如果需要）
    if output_path:
        _save_report(all_results, output_path, report_format, auto_fixer)


def _print_validation_summary(result: ValidationResult, verbose: bool = False) -> None:
    """打印验证摘要

    Args:
        result: 验证结果
        verbose: 是否详细输出
    """
    if result.success:
        print_success(f"  ✓ {result.validator_name}: 通过")
    else:
        print_error(f"  ✗ {result.validator_name}: 发现 {result.error_count} 个错误")

    if verbose and result.issues:
        for issue in result.issues:
            _print_issue(issue)


def _print_issue(issue) -> None:
    """打印单个问题

    Args:
        issue: 验证问题
    """
    level_colors = {
        ValidationLevel.ERROR: "red",
        ValidationLevel.WARNING: "yellow",
        ValidationLevel.INFO: "blue",
    }

    level_icons = {
        ValidationLevel.ERROR: "✗",
        ValidationLevel.WARNING: "⚠",
        ValidationLevel.INFO: "ℹ",
    }

    color = level_colors.get(issue.level, "white")
    icon = level_icons.get(issue.level, "•")

    message = f"    [{color}]{icon}[/{color}] {issue.message}"

    if issue.file_path:
        message += f" ([dim]{issue.file_path}"
        if issue.line_number:
            message += f":{issue.line_number}"
        message += "[/dim])"

    console.print(message)

    if issue.suggestion:
        console.print(f"      [dim]💡 {issue.suggestion}[/dim]")


def _print_overall_report(
    results: list[ValidationResult], level: str, auto_fixer: AutoFixValidator | None = None
) -> None:
    """打印总体报告

    Args:
        results: 所有验证结果
        level: 显示级别
        auto_fixer: 自动修复器对象（如果启用了自动修复）
    """
    console.print()
    console.print("=" * 60)
    console.print()

    # 统计总数
    total_errors = sum(r.error_count for r in results)
    total_warnings = sum(r.warning_count for r in results)

    # 创建统计表格
    table = Table(title="检查结果汇总", show_header=True, header_style="bold")
    table.add_column("验证器", style="cyan")
    table.add_column("错误", style="red")
    table.add_column("警告", style="yellow")
    table.add_column("信息", style="blue")
    table.add_column("状态", style="green")

    for result in results:
        status = "✓ 通过" if result.success else "✗ 失败"
        status_style = "green" if result.success else "red"
        table.add_row(
            result.validator_name,
            str(result.error_count),
            str(result.warning_count),
            str(result.info_count),
            f"[{status_style}]{status}[/{status_style}]",
        )

    console.print(table)
    console.print()

    # 打印详细问题列表
    level_filter = ValidationLevel(level)
    for result in results:
        filtered_issues = [
            issue
            for issue in result.issues
            if (issue.level == ValidationLevel.ERROR)
            or (
                issue.level == ValidationLevel.WARNING
                and level_filter in [ValidationLevel.WARNING, ValidationLevel.INFO]
            )
            or (issue.level == ValidationLevel.INFO and level_filter == ValidationLevel.INFO)
        ]

        if filtered_issues:
            console.print(f"\n[bold]{result.validator_name}:[/bold]")
            for issue in filtered_issues:
                _print_issue(issue)

    # 总结
    console.print()
    if auto_fixer:
        console.print("[bold cyan]═══ 修复统计 ═══[/bold cyan]")
        console.print()

        if auto_fixer.fixes_applied:
            console.print(f"[green]✓ 成功修复: {len(auto_fixer.fixes_applied)} 个[/green]")
            for fix in auto_fixer.fixes_applied:
                console.print(f"  [green]•[/green] {fix}")
            console.print()

        if auto_fixer.fixes_failed:
            console.print(f"[yellow]✗ 修复失败: {len(auto_fixer.fixes_failed)} 个[/yellow]")
            for fail in auto_fixer.fixes_failed:
                console.print(f"  [yellow]•[/yellow] {fail}")
            console.print()

        if not auto_fixer.fixes_applied and not auto_fixer.fixes_failed:
            console.print("[blue]ℹ 未发现可自动修复的问题[/blue]")
            console.print()

    console.print("[bold cyan]═══ 最终结果 ═══[/bold cyan]")
    console.print()
    if total_errors > 0:
        print_error(f"剩余 {total_errors} 个错误，{total_warnings} 个警告")
    elif total_warnings > 0:
        print_warning(f"剩余 {total_warnings} 个警告")
    else:
        print_success("所有检查通过！")


def _save_report(
    results: list[ValidationResult], output_path: str, report_format: str, auto_fixer: AutoFixValidator | None = None
) -> None:
    """保存检查报告

    Args:
        results: 验证结果列表
        output_path: 输出路径
        report_format: 报告格式
        auto_fixer: 自动修复器对象（如果启用了自动修复）
    """
    if report_format == "markdown":
        _save_markdown_report(results, output_path, auto_fixer)
    elif report_format == "json":
        _save_json_report(results, output_path, auto_fixer)
    else:
        print_warning(f"不支持的报告格式: {report_format}")


def _save_markdown_report(
    results: list[ValidationResult], output_path: str, auto_fixer: AutoFixValidator | None = None
) -> None:
    """保存 Markdown 格式的报告

    Args:
        results: 验证结果列表
        output_path: 输出路径
        auto_fixer: 自动修复器对象（如果启用了自动修复）
    """
    lines = ["# 插件检查报告\n\n"]

    # 统计
    total_errors = sum(r.error_count for r in results)
    total_warnings = sum(r.warning_count for r in results)
    total_info = sum(r.info_count for r in results)

    lines.append("## 摘要\n\n")
    lines.append(f"- 错误: {total_errors}\n")
    lines.append(f"- 警告: {total_warnings}\n")
    lines.append(f"- 信息: {total_info}\n")

    # 修复统计
    if auto_fixer:
        lines.append("\n### 自动修复统计\n\n")
        if auto_fixer.fixes_applied:
            lines.append(f"- ✅ 成功修复: {len(auto_fixer.fixes_applied)} 个\n")
            for fix in auto_fixer.fixes_applied:
                lines.append(f"  - {fix}\n")
        if auto_fixer.fixes_failed:
            lines.append(f"- ❌ 修复失败: {len(auto_fixer.fixes_failed)} 个\n")
            for fail in auto_fixer.fixes_failed:
                lines.append(f"  - {fail}\n")
        if not auto_fixer.fixes_applied and not auto_fixer.fixes_failed:
            lines.append("- ℹ️ 未发现可自动修复的问题\n")

    lines.append("\n")

    # 详细结果
    for result in results:
        lines.append(f"## {result.validator_name}\n")

        if result.success:
            lines.append("✓ 通过\n\n")
        else:
            lines.append(f"✗ 发现 {result.error_count} 个错误\n\n")

        if result.issues:
            lines.append("### 问题列表\n\n")
            for issue in result.issues:
                level_icons = {
                    ValidationLevel.ERROR: "❌",
                    ValidationLevel.WARNING: "⚠️",
                    ValidationLevel.INFO: "ℹ️",
                }
                icon = level_icons.get(issue.level, "•")
                lines.append(f"- {icon} **{issue.level.value.upper()}**: {issue.message}\n")

                if issue.file_path:
                    lines.append(f"  - 文件: `{issue.file_path}`")
                    if issue.line_number:
                        lines.append(f":{issue.line_number}")
                    lines.append("\n")

                if issue.suggestion:
                    lines.append(f"  - 建议: {issue.suggestion}\n")

            lines.append("\n")

    # 总结
    lines.append("## 总结\n\n")
    if auto_fixer and auto_fixer.fixes_applied:
        lines.append(f"✅ 成功修复 {len(auto_fixer.fixes_applied)} 个问题\n\n")
        if auto_fixer.fixes_failed:
            lines.append(f"⚠️ {len(auto_fixer.fixes_failed)} 个问题修复失败\n\n")

    if total_errors > 0:
        lines.append(f"❌ 剩余 {total_errors} 个错误，{total_warnings} 个警告\n")
    elif total_warnings > 0:
        lines.append(f"⚠️ 剩余 {total_warnings} 个警告\n")
    else:
        lines.append("✅ 所有检查通过！\n")

    # 写入文件
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print_success(f"报告已保存到: {output_path}")
    except Exception as e:
        print_error(f"保存报告失败: {e}")


def _save_json_report(
    results: list[ValidationResult], output_path: str, auto_fixer: AutoFixValidator | None = None
) -> None:
    """保存 JSON 格式的报告

    Args:
        results: 验证结果列表
        output_path: 输出路径
        auto_fixer: 自动修复器对象（如果启用了自动修复）
    """
    import json
    from datetime import datetime

    # 统计总数
    total_errors = sum(r.error_count for r in results)
    total_warnings = sum(r.warning_count for r in results)
    total_info = sum(r.info_count for r in results)

    # 构建报告数据结构
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_info": total_info,
            "success": total_errors == 0,
        },
        "validators": [],
        "issues": [],
    }

    # 添加自动修复统计
    if auto_fixer:
        report["auto_fix"] = {
            "enabled": True,
            "fixes_applied": len(auto_fixer.fixes_applied),
            "fixes_failed": len(auto_fixer.fixes_failed),
            "applied_fixes": auto_fixer.fixes_applied,
            "failed_fixes": auto_fixer.fixes_failed,
        }
    else:
        report["auto_fix"] = {"enabled": False}

    # 添加每个验证器的结果
    for result in results:
        validator_data = {
            "name": result.validator_name,
            "success": result.success,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "info_count": result.info_count,
        }
        report["validators"].append(validator_data)

        # 添加问题详情
        for issue in result.issues:
            issue_data = {
                "validator": result.validator_name,
                "level": issue.level.value,
                "message": issue.message,
                "file_path": issue.file_path,
                "line_number": issue.line_number,
                "suggestion": issue.suggestion,
            }
            report["issues"].append(issue_data)

    # 写入文件
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print_success(f"报告已保存到: {output_path}")
    except Exception as e:
        print_error(f"保存报告失败: {e}")
