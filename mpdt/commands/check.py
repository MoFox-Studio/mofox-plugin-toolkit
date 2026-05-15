"""
静态检查命令实现
"""

from pathlib import Path

from rich.panel import Panel
from rich.table import Table

from mpdt.utils.color_printer import (
    console,
    print_colored,
    print_divider,
    print_empty_line,
    print_error,
    print_fit_panel,
    print_info,
    print_success,
    print_warning,
)
from mpdt.checkers import FixResult, ValidationLevel, ValidationResult
from mpdt.checkers.validators import (
    ComponentValidator,
    ConfigValidator,
    MetadataValidator,
    StructureValidator,
    StyleValidator,
    TypeValidator,
)
from mpdt.checkers.fixers import (
    AttributeFixer,
    DecoratorFixer,
    ManifestFixer,
    MethodFixer,
    StyleFixer,
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
    """
    path = Path(plugin_path).resolve()

    if not path.exists():
        print_error(f"插件路径不存在: {plugin_path}")
        return

    if not path.is_dir():
        print_error(f"插件路径不是目录: {plugin_path}")
        return

    print_fit_panel(f"🔍 检查插件: {path.name}", "", border_style="blue")

    # 收集所有验证结果
    all_results: list[ValidationResult] = []

    # 结构验证
    if not skip_structure:
        print_info("正在检查插件结构...")
        validator = StructureValidator(path)
        result = validator.validate()
        all_results.append(result)
        _print_validation_summary(result)

    # 元数据验证
    if not skip_metadata:
        print_info("正在检查插件元数据...")
        validator = MetadataValidator(path)
        result = validator.validate()
        all_results.append(result)
        _print_validation_summary(result)

    # 组件验证
    if not skip_component:
        print_info("正在检查组件元数据...")
        validator = ComponentValidator(path)
        result = validator.validate()
        all_results.append(result)
        _print_validation_summary(result)

    # 配置验证
    print_info("正在检查配置文件...")
    validator = ConfigValidator(path)
    result = validator.validate()
    all_results.append(result)
    _print_validation_summary(result)

    # 类型检查
    if not skip_type:
        print_info("正在进行类型检查...")
        validator = TypeValidator(path)
        result = validator.validate()
        all_results.append(result)
        _print_validation_summary(result)

    # 代码风格检查
    if not skip_style:
        print_info("正在检查代码风格...")
        validator = StyleValidator(path)
        result = validator.validate()
        all_results.append(result)
        _print_validation_summary(result)

    # 自动修复（如果启用）
    fix_result = None
    if auto_fix:
        print_info("正在应用自动修复...")
        
        # 收集所有问题
        all_issues = []
        for result in all_results:
            all_issues.extend(result.issues)
        
        if not all_issues:
            print_info("  ℹ 未发现需要修复的问题")
        else:
            # 创建修复器列表
            fixers = [
                ManifestFixer(path),
                DecoratorFixer(path),
                AttributeFixer(path),
                MethodFixer(path),
                StyleFixer(path),
            ]
            
            # 汇总所有修复结果
            fix_result = FixResult(fixer_name="AutoFix")
            
            for fixer in fixers:
                # 过滤出该修复器可以处理的问题
                fixable_issues = [issue for issue in all_issues if fixer.can_fix(issue)]
                
                if fixable_issues:
                    result = fixer.fix(fixable_issues)
                    fix_result.fixes_applied.extend(result.fixes_applied)
                    fix_result.fixes_failed.extend(result.fixes_failed)
                    fix_result.fixed_issues.extend(result.fixed_issues)
            
            # 从原始结果中移除已修复的问题
            fixed_issue_ids = {id(issue) for issue in fix_result.fixed_issues}
            for result in all_results:
                result.issues = [issue for issue in result.issues if id(issue) not in fixed_issue_ids]
                result._update_counts()
            
            # 显示修复摘要
            if fix_result.fixes_applied:
                print_success(f"  ✓ 成功修复 {len(fix_result.fixes_applied)} 个问题")
            
            if fix_result.fixes_failed:
                print_warning(f"  ⚠ {len(fix_result.fixes_failed)} 个问题修复失败")
            
            if not fix_result.fixes_applied and not fix_result.fixes_failed:
                print_info("  ℹ 未发现可自动修复的问题")

    # 生成总体报告
    _print_overall_report(all_results, level, fix_result if auto_fix else None)

    # 保存报告（如果需要）
    if output_path:
        _save_report(all_results, output_path, report_format, fix_result if auto_fix else None)


def _print_validation_summary(result: ValidationResult) -> None:
    """打印验证摘要

    Args:
        result: 验证结果
    """
    if result.success:
        print_success(f"  ✓ {result.validator_name}: 通过")
    else:
        print_error(f"  ✗ {result.validator_name}: 发现 {result.error_count} 个错误")


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

    message = f"    {icon} {issue.message}"

    if issue.file_path:
        file_info = f" ({issue.file_path}"
        if issue.line_number:
            file_info += f":{issue.line_number}"
        file_info += ")"
        message += file_info

    print_colored(message, color=color)

    if issue.suggestion:
        print_colored(f"      💡 {issue.suggestion}", dim=True)


def _print_overall_report(
    results: list[ValidationResult], level: str, fix_result: FixResult | None = None
) -> None:
    """打印总体报告

    Args:
        results: 所有验证结果
        level: 显示级别
        fix_result: 自动修复结果（如果启用了自动修复）
    """
    print_empty_line()
    print_divider("=", 60)
    print_empty_line()

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
    print_empty_line()

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
            print_colored(f"\n{result.validator_name}:", color="white", bold=True)
            for issue in filtered_issues:
                _print_issue(issue)

    # 总结
    print_empty_line()
    if fix_result:
        print_colored("═══ 修复统计 ═══", color="cyan", bold=True)
        print_empty_line()

        if fix_result.fixes_applied:
            print_colored(f"✓ 成功修复: {len(fix_result.fixes_applied)} 个", color="green")
            for fix in fix_result.fixes_applied:
                print_colored(f"  • {fix}", color="green")
            print_empty_line()

        if fix_result.fixes_failed:
            print_colored(f"✗ 修复失败: {len(fix_result.fixes_failed)} 个", color="yellow")
            for fail in fix_result.fixes_failed:
                print_colored(f"  • {fail}", color="yellow")
            print_empty_line()

        if not fix_result.fixes_applied and not fix_result.fixes_failed:
            print_info("未发现可自动修复的问题")
            print_empty_line()

    print_colored("═══ 最终结果 ═══", color="cyan", bold=True)
    print_empty_line()
    if total_errors > 0:
        print_error(f"剩余 {total_errors} 个错误，{total_warnings} 个警告")
    elif total_warnings > 0:
        print_warning(f"剩余 {total_warnings} 个警告")
    else:
        print_success("所有检查通过！")


def _save_report(
    results: list[ValidationResult], output_path: str, report_format: str, fix_result: FixResult | None = None
) -> None:
    """保存检查报告

    Args:
        results: 验证结果列表
        output_path: 输出路径
        report_format: 报告格式
        fix_result: 自动修复结果（如果启用了自动修复）
    """
    if report_format == "markdown":
        _save_markdown_report(results, output_path, fix_result)
    elif report_format == "json":
        _save_json_report(results, output_path, fix_result)
    else:
        print_warning(f"不支持的报告格式: {report_format}")


def _save_markdown_report(
    results: list[ValidationResult], output_path: str, fix_result: FixResult | None = None
) -> None:
    """保存 Markdown 格式的报告

    Args:
        results: 验证结果列表
        output_path: 输出路径
        fix_result: 自动修复结果（如果启用了自动修复）
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
    if fix_result:
        lines.append("\n### 自动修复统计\n\n")
        if fix_result.fixes_applied:
            lines.append(f"- ✅ 成功修复: {len(fix_result.fixes_applied)} 个\n")
            for fix in fix_result.fixes_applied:
                lines.append(f"  - {fix}\n")
        if fix_result.fixes_failed:
            lines.append(f"- ❌ 修复失败: {len(fix_result.fixes_failed)} 个\n")
            for fail in fix_result.fixes_failed:
                lines.append(f"  - {fail}\n")
        if not fix_result.fixes_applied and not fix_result.fixes_failed:
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
    if fix_result and fix_result.fixes_applied:
        lines.append(f"✅ 成功修复 {len(fix_result.fixes_applied)} 个问题\n\n")
        if fix_result.fixes_failed:
            lines.append(f"⚠️ {len(fix_result.fixes_failed)} 个问题修复失败\n\n")

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
    results: list[ValidationResult], output_path: str, fix_result: FixResult | None = None
) -> None:
    """保存 JSON 格式的报告

    Args:
        results: 验证结果列表
        output_path: 输出路径
        fix_result: 自动修复结果（如果启用了自动修复）
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
    if fix_result:
        report["auto_fix"] = {
            "enabled": True,
            "fixes_applied": len(fix_result.fixes_applied),
            "fixes_failed": len(fix_result.fixes_failed),
            "applied_fixes": fix_result.fixes_applied,
            "failed_fixes": fix_result.fixes_failed,
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
