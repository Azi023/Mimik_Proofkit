"""
Visual Report Generator

Creates HTML reports with graphical visualizations of:
- Test results
- Code coverage
- Codebase analysis
- Performance metrics
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class VisualReportGenerator:
    """
    Generates visual HTML reports with charts and graphs.

    Uses Chart.js for visualizations (embedded CDN).
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize with report data.

        Args:
            data: Dictionary containing report data
        """
        self.data = data

    def generate_analysis_report(self, output_path: Path) -> str:
        """
        Generate visual codebase analysis report.

        Args:
            output_path: Path to save the HTML report

        Returns:
            Path to generated report
        """
        html = self._generate_html_template(
            title="Codebase Analysis Report",
            content=self._generate_analysis_content(),
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding='utf-8')
        return str(output_path)

    def generate_test_results_report(
        self,
        test_results: Dict[str, Any],
        output_path: Path
    ) -> str:
        """
        Generate visual test results report.

        Args:
            test_results: Dict with test execution results
            output_path: Path to save the HTML report

        Returns:
            Path to generated report
        """
        html = self._generate_html_template(
            title="Test Results Report",
            content=self._generate_test_results_content(test_results),
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding='utf-8')
        return str(output_path)

    def _generate_html_template(self, title: str, content: str) -> str:
        """Generate HTML document with styling and scripts."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - ProofKit</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e4e4e4;
            min-height: 100vh;
            padding: 2rem;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem;
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            backdrop-filter: blur(10px);
        }}

        header h1 {{
            font-size: 2.5rem;
            background: linear-gradient(90deg, #4facfe, #00f2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}

        header .subtitle {{
            color: #888;
            font-size: 1rem;
        }}

        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .card {{
            background: rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .card h2 {{
            font-size: 1.1rem;
            color: #888;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .metric {{
            font-size: 3rem;
            font-weight: bold;
            background: linear-gradient(90deg, #4facfe, #00f2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .metric-label {{
            color: #666;
            font-size: 0.9rem;
        }}

        .chart-container {{
            position: relative;
            height: 300px;
            margin: 1rem 0;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-top: 1rem;
        }}

        .stat-item {{
            text-align: center;
            padding: 1rem;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
        }}

        .stat-value {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #4facfe;
        }}

        .stat-label {{
            font-size: 0.75rem;
            color: #888;
            text-transform: uppercase;
        }}

        .list-section {{
            margin-top: 2rem;
        }}

        .list-item {{
            display: flex;
            align-items: center;
            padding: 1rem;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            margin-bottom: 0.5rem;
            transition: background 0.2s;
        }}

        .list-item:hover {{
            background: rgba(255,255,255,0.1);
        }}

        .badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: bold;
            margin-right: 1rem;
        }}

        .badge-success {{ background: #22c55e; color: white; }}
        .badge-warning {{ background: #eab308; color: black; }}
        .badge-error {{ background: #ef4444; color: white; }}
        .badge-info {{ background: #3b82f6; color: white; }}

        .progress-bar {{
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4facfe, #00f2fe);
            transition: width 0.5s ease;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}

        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}

        th {{
            color: #888;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 1px;
        }}

        footer {{
            text-align: center;
            margin-top: 3rem;
            padding: 2rem;
            color: #666;
            font-size: 0.875rem;
        }}

        footer a {{
            color: #4facfe;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p class="subtitle">Generated by ProofKit - {datetime.now().strftime("%B %d, %Y at %H:%M")}</p>
        </header>

        {content}

        <footer>
            <p>Generated by <a href="#">ProofKit</a> | Mimik Creations</p>
        </footer>
    </div>
</body>
</html>'''

    def _generate_analysis_content(self) -> str:
        """Generate content for codebase analysis report."""
        summary = self.data.get("summary", {})
        languages = summary.get("languages", {})
        components = self.data.get("components", [])
        insights = self.data.get("insights", [])

        # Prepare chart data
        lang_labels = list(languages.keys())
        lang_values = list(languages.values())

        return f'''
        <div class="dashboard">
            <div class="card">
                <h2>Total Files</h2>
                <div class="metric">{summary.get("file_count", 0)}</div>
                <div class="metric-label">code files analyzed</div>
            </div>

            <div class="card">
                <h2>Lines of Code</h2>
                <div class="metric">{summary.get("total_lines", 0):,}</div>
                <div class="metric-label">total lines</div>
            </div>

            <div class="card">
                <h2>Components</h2>
                <div class="metric">{summary.get("component_count", 0)}</div>
                <div class="metric-label">classes, functions, methods</div>
            </div>

            <div class="card">
                <h2>Classes</h2>
                <div class="metric">{summary.get("class_count", 0)}</div>
                <div class="metric-label">class definitions</div>
            </div>
        </div>

        <div class="dashboard">
            <div class="card" style="grid-column: span 2;">
                <h2>Language Distribution</h2>
                <div class="chart-container">
                    <canvas id="languageChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h2>Key Insights</h2>
                <div class="list-section">
                    {"".join(f'<div class="list-item"><span class="badge badge-info">Insight</span>{insight}</div>' for insight in insights)}
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Top Components</h2>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>File</th>
                        <th>Line</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(f'''<tr>
                        <td>{c.get("name", "")}</td>
                        <td><span class="badge badge-info">{c.get("type", "")}</span></td>
                        <td>{c.get("file_path", "")}</td>
                        <td>{c.get("line_number", "")}</td>
                    </tr>''' for c in components[:15])}
                </tbody>
            </table>
        </div>

        <script>
            // Language Chart
            new Chart(document.getElementById('languageChart'), {{
                type: 'doughnut',
                data: {{
                    labels: {json.dumps(lang_labels)},
                    datasets: [{{
                        data: {json.dumps(lang_values)},
                        backgroundColor: [
                            '#4facfe', '#00f2fe', '#22c55e', '#eab308',
                            '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899'
                        ],
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'right',
                            labels: {{
                                color: '#888',
                                padding: 20
                            }}
                        }}
                    }}
                }}
            }});
        </script>'''

    def _generate_test_results_content(self, results: Dict[str, Any]) -> str:
        """Generate content for test results report."""
        total = results.get("total", 0)
        passed = results.get("passed", 0)
        failed = results.get("failed", 0)
        skipped = results.get("skipped", 0)
        duration = results.get("duration", 0)

        pass_rate = (passed / total * 100) if total > 0 else 0
        tests = results.get("tests", [])

        return f'''
        <div class="dashboard">
            <div class="card">
                <h2>Pass Rate</h2>
                <div class="metric">{pass_rate:.1f}%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {pass_rate}%;"></div>
                </div>
            </div>

            <div class="card">
                <h2>Total Tests</h2>
                <div class="metric">{total}</div>
                <div class="metric-label">test cases executed</div>
            </div>

            <div class="card">
                <h2>Duration</h2>
                <div class="metric">{duration:.2f}s</div>
                <div class="metric-label">total execution time</div>
            </div>

            <div class="card">
                <h2>Results Breakdown</h2>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" style="color: #22c55e;">{passed}</div>
                        <div class="stat-label">Passed</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" style="color: #ef4444;">{failed}</div>
                        <div class="stat-label">Failed</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" style="color: #eab308;">{skipped}</div>
                        <div class="stat-label">Skipped</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" style="color: #3b82f6;">{total}</div>
                        <div class="stat-label">Total</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="dashboard">
            <div class="card" style="grid-column: span 2;">
                <h2>Results Distribution</h2>
                <div class="chart-container">
                    <canvas id="resultsChart"></canvas>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Test Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(self._format_test_row(t) for t in tests[:20])}
                </tbody>
            </table>
        </div>

        <script>
            // Results Chart
            new Chart(document.getElementById('resultsChart'), {{
                type: 'bar',
                data: {{
                    labels: ['Passed', 'Failed', 'Skipped'],
                    datasets: [{{
                        data: [{passed}, {failed}, {skipped}],
                        backgroundColor: ['#22c55e', '#ef4444', '#eab308'],
                        borderWidth: 0,
                        borderRadius: 8
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            grid: {{
                                color: 'rgba(255,255,255,0.1)'
                            }},
                            ticks: {{
                                color: '#888'
                            }}
                        }},
                        x: {{
                            grid: {{
                                display: false
                            }},
                            ticks: {{
                                color: '#888'
                            }}
                        }}
                    }}
                }}
            }});
        </script>'''

    def _format_test_row(self, test: Dict[str, Any]) -> str:
        """Format a single test result row."""
        status = test.get("status", "unknown")
        badge_class = {
            "passed": "badge-success",
            "failed": "badge-error",
            "skipped": "badge-warning",
        }.get(status, "badge-info")

        return f'''<tr>
            <td>{test.get("name", "")}</td>
            <td><span class="badge {badge_class}">{status.upper()}</span></td>
            <td>{test.get("duration", 0):.3f}s</td>
            <td>{test.get("message", "")[:50]}</td>
        </tr>'''


def generate_visual_report(
    data: Dict[str, Any],
    report_type: str,
    output_path: Path
) -> str:
    """
    Convenience function to generate visual reports.

    Args:
        data: Report data
        report_type: 'analysis' or 'test_results'
        output_path: Path to save report

    Returns:
        Path to generated report
    """
    generator = VisualReportGenerator(data)

    if report_type == "analysis":
        return generator.generate_analysis_report(output_path)
    elif report_type == "test_results":
        return generator.generate_test_results_report(data, output_path)
    else:
        raise ValueError(f"Unknown report type: {report_type}")
