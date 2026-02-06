"""
Codebase Analyzer - Scans and analyzes code repositories.

Provides intelligent code analysis to understand:
- Project structure and architecture
- Components, classes, and functions
- Dependencies and imports
- Code patterns and conventions
- Test coverage gaps
"""

import os
import ast
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from proofkit.utils.logger import logger


@dataclass
class CodeComponent:
    """Represents a discovered code component (class, function, etc.)."""
    name: str
    type: str  # class, function, method, module
    file_path: str
    line_number: int
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    complexity: int = 0  # Cyclomatic complexity estimate
    lines_of_code: int = 0


@dataclass
class FileAnalysis:
    """Analysis result for a single file."""
    path: str
    language: str
    lines: int
    components: List[CodeComponent] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    has_tests: bool = False
    has_docstrings: bool = False


@dataclass
class AnalysisResult:
    """Complete codebase analysis result."""
    root_path: str
    analyzed_at: str
    file_count: int = 0
    component_count: int = 0
    function_count: int = 0
    class_count: int = 0
    total_lines: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    files: List[FileAnalysis] = field(default_factory=list)
    components: List[CodeComponent] = field(default_factory=list)
    structure: Dict[str, Any] = field(default_factory=dict)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)

    def save(self, output_dir: Path) -> Dict[str, str]:
        """Save analysis results to files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        files = {}

        # Save full JSON report
        report_path = output_dir / "analysis_report.json"
        report_data = {
            "root_path": self.root_path,
            "analyzed_at": self.analyzed_at,
            "summary": {
                "file_count": self.file_count,
                "component_count": self.component_count,
                "function_count": self.function_count,
                "class_count": self.class_count,
                "total_lines": self.total_lines,
                "languages": self.languages,
            },
            "structure": self.structure,
            "dependencies": self.dependencies,
            "insights": self.insights,
            "components": [
                {
                    "name": c.name,
                    "type": c.type,
                    "file_path": c.file_path,
                    "line_number": c.line_number,
                    "docstring": c.docstring,
                    "parameters": c.parameters,
                    "complexity": c.complexity,
                }
                for c in self.components
            ],
        }
        report_path.write_text(json.dumps(report_data, indent=2), encoding='utf-8')
        files["report"] = str(report_path)

        # Save markdown summary
        md_path = output_dir / "CODEBASE_ANALYSIS.md"
        md_path.write_text(self._generate_markdown(), encoding='utf-8')
        files["markdown"] = str(md_path)

        # Save component list
        components_path = output_dir / "components.json"
        components_path.write_text(
            json.dumps([
                {"name": c.name, "type": c.type, "file": c.file_path, "line": c.line_number}
                for c in self.components
            ], indent=2),
            encoding='utf-8'
        )
        files["components"] = str(components_path)

        # Generate visual HTML report
        try:
            from .visual_report import VisualReportGenerator
            visual_gen = VisualReportGenerator(report_data)
            html_path = output_dir / "analysis_report.html"
            visual_gen.generate_analysis_report(html_path)
            files["html_report"] = str(html_path)
        except Exception as e:
            logger.warning(f"Failed to generate visual report: {e}")

        return files

    def _generate_markdown(self) -> str:
        """Generate markdown summary of analysis."""
        md = f"""# Codebase Analysis Report

**Analyzed:** {self.root_path}
**Date:** {self.analyzed_at}

## Summary

| Metric | Value |
|--------|-------|
| Files | {self.file_count} |
| Total Lines | {self.total_lines:,} |
| Classes | {self.class_count} |
| Functions | {self.function_count} |
| Components | {self.component_count} |

## Languages

"""
        for lang, count in sorted(self.languages.items(), key=lambda x: -x[1]):
            md += f"- **{lang}**: {count} files\n"

        md += "\n## Key Components\n\n"
        for comp in self.components[:20]:
            md += f"- `{comp.name}` ({comp.type}) - {comp.file_path}:{comp.line_number}\n"
            if comp.docstring:
                md += f"  - {comp.docstring[:100]}...\n" if len(comp.docstring) > 100 else f"  - {comp.docstring}\n"

        if self.insights:
            md += "\n## Insights\n\n"
            for insight in self.insights:
                md += f"- {insight}\n"

        md += "\n---\n*Generated by ProofKit Codebase QA*\n"
        return md


class CodebaseAnalyzer:
    """
    Analyzes codebases to extract structure and components.

    Supports:
    - Python (.py)
    - TypeScript/JavaScript (.ts, .tsx, .js, .jsx)
    - Go (.go)
    - Rust (.rs)
    - And more...
    """

    # Language detection by extension
    LANGUAGE_MAP = {
        ".py": "Python",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".rb": "Ruby",
        ".php": "PHP",
        ".cs": "C#",
        ".cpp": "C++",
        ".c": "C",
        ".h": "C/C++ Header",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".vue": "Vue",
        ".svelte": "Svelte",
    }

    # Default patterns to exclude
    DEFAULT_EXCLUDES = {
        "node_modules", "__pycache__", ".git", ".svn", "venv", "env",
        ".venv", "dist", "build", ".next", ".nuxt", "target", "vendor",
        ".pytest_cache", ".mypy_cache", "coverage", ".coverage",
        "*.egg-info", ".tox", ".eggs",
    }

    def __init__(
        self,
        root_path: Path,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ):
        """
        Initialize the analyzer.

        Args:
            root_path: Root directory to analyze
            include_patterns: File patterns to include (e.g., ["*.py", "*.ts"])
            exclude_patterns: Patterns to exclude (e.g., ["tests/*"])
        """
        self.root_path = Path(root_path).resolve()
        self.include_patterns = include_patterns
        self.exclude_patterns = set(exclude_patterns or []) | self.DEFAULT_EXCLUDES

        self._files: List[FileAnalysis] = []
        self._components: List[CodeComponent] = []

    def analyze(self) -> AnalysisResult:
        """
        Perform full codebase analysis.

        Returns:
            AnalysisResult with all discovered information
        """
        logger.info(f"Analyzing codebase at {self.root_path}")

        # Discover and analyze files
        self._discover_files()
        self._analyze_files()

        # Build result
        result = AnalysisResult(
            root_path=str(self.root_path),
            analyzed_at=datetime.utcnow().isoformat(),
            files=self._files,
            components=self._components,
        )

        # Calculate stats
        result.file_count = len(self._files)
        result.total_lines = sum(f.lines for f in self._files)
        result.component_count = len(self._components)
        result.function_count = sum(1 for c in self._components if c.type in ("function", "method"))
        result.class_count = sum(1 for c in self._components if c.type == "class")

        # Language breakdown
        for f in self._files:
            result.languages[f.language] = result.languages.get(f.language, 0) + 1

        # Build structure tree
        result.structure = self._build_structure_tree()

        # Extract dependencies
        result.dependencies = self._extract_dependencies()

        # Generate insights
        result.insights = self._generate_insights(result)

        logger.info(f"Analysis complete: {result.file_count} files, {result.component_count} components")
        return result

    def _discover_files(self) -> None:
        """Discover all relevant files in the codebase."""
        for root, dirs, files in os.walk(self.root_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude(d)]

            for filename in files:
                file_path = Path(root) / filename

                # Check if file matches include patterns
                if self.include_patterns:
                    if not any(file_path.match(p) for p in self.include_patterns):
                        continue

                # Check if file should be excluded
                if self._should_exclude(filename):
                    continue

                # Check if it's a recognized code file
                ext = file_path.suffix.lower()
                if ext in self.LANGUAGE_MAP:
                    self._files.append(FileAnalysis(
                        path=str(file_path.relative_to(self.root_path)),
                        language=self.LANGUAGE_MAP[ext],
                        lines=0,
                    ))

    def _should_exclude(self, name: str) -> bool:
        """Check if a file/directory should be excluded."""
        for pattern in self.exclude_patterns:
            if name == pattern or name.startswith(pattern):
                return True
            if "*" in pattern:
                import fnmatch
                if fnmatch.fnmatch(name, pattern):
                    return True
        return False

    def _analyze_files(self) -> None:
        """Analyze each discovered file."""
        for file_analysis in self._files:
            file_path = self.root_path / file_analysis.path
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                file_analysis.lines = len(content.splitlines())

                # Analyze based on language
                if file_analysis.language == "Python":
                    self._analyze_python_file(file_analysis, content)
                elif file_analysis.language in ("TypeScript", "JavaScript"):
                    self._analyze_js_file(file_analysis, content)
                else:
                    # Generic analysis
                    self._analyze_generic_file(file_analysis, content)

            except Exception as e:
                logger.warning(f"Failed to analyze {file_analysis.path}: {e}")

    def _analyze_python_file(self, file_analysis: FileAnalysis, content: str) -> None:
        """Analyze a Python file using AST."""
        try:
            tree = ast.parse(content)

            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        file_analysis.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        file_analysis.imports.append(node.module)

            # Extract classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    component = CodeComponent(
                        name=node.name,
                        type="class",
                        file_path=file_analysis.path,
                        line_number=node.lineno,
                        docstring=ast.get_docstring(node),
                        decorators=[self._get_decorator_name(d) for d in node.decorator_list],
                    )
                    self._components.append(component)
                    file_analysis.components.append(component)

                    # Extract methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method = CodeComponent(
                                name=f"{node.name}.{item.name}",
                                type="method",
                                file_path=file_analysis.path,
                                line_number=item.lineno,
                                docstring=ast.get_docstring(item),
                                parameters=[arg.arg for arg in item.args.args],
                                decorators=[self._get_decorator_name(d) for d in item.decorator_list],
                            )
                            self._components.append(method)

                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    # Top-level function
                    component = CodeComponent(
                        name=node.name,
                        type="function",
                        file_path=file_analysis.path,
                        line_number=node.lineno,
                        docstring=ast.get_docstring(node),
                        parameters=[arg.arg for arg in node.args.args],
                        decorators=[self._get_decorator_name(d) for d in node.decorator_list],
                    )
                    self._components.append(component)
                    file_analysis.components.append(component)

            # Check for docstrings
            file_analysis.has_docstrings = any(c.docstring for c in file_analysis.components)

            # Check if it's a test file
            file_analysis.has_tests = "test" in file_analysis.path.lower()

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_analysis.path}: {e}")

    def _analyze_js_file(self, file_analysis: FileAnalysis, content: str) -> None:
        """Analyze JavaScript/TypeScript file using regex patterns."""
        # Extract imports
        import_patterns = [
            r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]',
            r'require\([\'"](.+?)[\'"]\)',
        ]
        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                file_analysis.imports.append(match.group(1))

        # Extract classes
        class_pattern = r'(?:export\s+)?class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            component = CodeComponent(
                name=match.group(1),
                type="class",
                file_path=file_analysis.path,
                line_number=line_num,
            )
            self._components.append(component)
            file_analysis.components.append(component)

        # Extract functions
        func_patterns = [
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)',
            r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\(',
            r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\w+\s*=>\s*',
        ]
        for pattern in func_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                component = CodeComponent(
                    name=match.group(1),
                    type="function",
                    file_path=file_analysis.path,
                    line_number=line_num,
                )
                self._components.append(component)
                file_analysis.components.append(component)

        # Check for tests
        file_analysis.has_tests = any(
            test_indicator in content
            for test_indicator in ['describe(', 'it(', 'test(', 'expect(']
        )

    def _analyze_generic_file(self, file_analysis: FileAnalysis, content: str) -> None:
        """Generic analysis for other languages."""
        # Simple function detection
        func_pattern = r'(?:func|def|fn|function)\s+(\w+)'
        for match in re.finditer(func_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            component = CodeComponent(
                name=match.group(1),
                type="function",
                file_path=file_analysis.path,
                line_number=line_num,
            )
            self._components.append(component)
            file_analysis.components.append(component)

    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return "unknown"

    def _build_structure_tree(self) -> Dict[str, Any]:
        """Build a tree structure of the codebase."""
        tree: Dict[str, Any] = {}

        for file_analysis in self._files:
            parts = Path(file_analysis.path).parts
            current = tree

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = {
                "language": file_analysis.language,
                "lines": file_analysis.lines,
                "components": len(file_analysis.components),
            }

        return tree

    def _extract_dependencies(self) -> Dict[str, List[str]]:
        """Extract dependency graph from imports."""
        deps: Dict[str, Set[str]] = {}

        for file_analysis in self._files:
            file_deps = set()
            for imp in file_analysis.imports:
                # Filter to internal dependencies
                if not imp.startswith((".", "..")):
                    # Check if it's an internal module
                    for f in self._files:
                        module_name = Path(f.path).stem
                        if imp.endswith(module_name) or imp == module_name:
                            file_deps.add(f.path)
                            break
                else:
                    # Relative import
                    file_deps.add(imp)

            if file_deps:
                deps[file_analysis.path] = list(file_deps)

        return {k: list(v) for k, v in deps.items()}

    def _generate_insights(self, result: AnalysisResult) -> List[str]:
        """Generate insights about the codebase."""
        insights = []

        # Language distribution
        if result.languages:
            primary_lang = max(result.languages.items(), key=lambda x: x[1])
            insights.append(f"Primary language: {primary_lang[0]} ({primary_lang[1]} files)")

        # Code metrics
        if result.file_count > 0:
            avg_lines = result.total_lines // result.file_count
            insights.append(f"Average file size: {avg_lines} lines")

        # Component density
        if result.file_count > 0:
            density = result.component_count / result.file_count
            insights.append(f"Component density: {density:.1f} components per file")

        # Test coverage indicator
        test_files = sum(1 for f in self._files if f.has_tests)
        if test_files > 0:
            insights.append(f"Test files found: {test_files}")
        else:
            insights.append("No test files detected - consider adding tests")

        # Documentation
        documented = sum(1 for c in self._components if c.docstring)
        if self._components:
            doc_percent = (documented / len(self._components)) * 100
            insights.append(f"Documentation coverage: {doc_percent:.0f}%")

        return insights

    def generate_tests(self, output_dir: Path) -> Dict[str, Any]:
        """
        Generate test scripts for discovered components.

        Args:
            output_dir: Directory to save generated tests

        Returns:
            Dict with generation results
        """
        from .test_generator import CodebaseTestGenerator

        generator = CodebaseTestGenerator(self._components, self.root_path)
        return generator.generate(output_dir)
