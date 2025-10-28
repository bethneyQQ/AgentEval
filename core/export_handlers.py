"""
Export handlers for evaluation results.

This module provides exporters to convert evaluation results into various formats
including HTML reports and CSV files.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import csv
import json

from core.batch_orchestrator import EvaluationResult
from core.benchmark_adapter_base import TaskResult, TaskStatus


class HTMLExporter:
    """Export evaluation results to HTML format."""

    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize HTML exporter.

        Args:
            template_path: Optional path to custom HTML template
        """
        self.template_path = template_path

    def export(
        self,
        result: EvaluationResult,
        output_path: str,
        title: Optional[str] = None
    ) -> None:
        """
        Export evaluation result to HTML file.

        Args:
            result: The evaluation result to export
            output_path: Path where HTML file will be saved
            title: Optional custom title for the report
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        html_content = self._generate_html(result, title)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_html(
        self,
        result: EvaluationResult,
        title: Optional[str] = None
    ) -> str:
        """
        Generate HTML content from evaluation result.

        Args:
            result: The evaluation result
            title: Optional custom title

        Returns:
            HTML content as string
        """
        if title is None:
            title = f"Evaluation Report: {result.request.model_name} on {result.request.benchmark_name}"

        # Generate sections
        header = self._generate_header(title)
        summary = self._generate_summary_section(result)
        task_results = self._generate_task_results_section(result)
        metrics = self._generate_metrics_section(result)
        footer = self._generate_footer()

        return f"""<!DOCTYPE html>
<html lang="en">
{header}
<body>
    <div class="container">
        <h1>{title}</h1>
        {summary}
        {metrics}
        {task_results}
    </div>
    {footer}
</body>
</html>"""

    def _generate_header(self, title: str) -> str:
        """Generate HTML header with CSS."""
        return f"""<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }}
        .summary-label {{
            font-size: 0.9em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .summary-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 5px;
        }}
        .pass-rate {{
            border-left-color: #27ae60;
        }}
        .fail-rate {{
            border-left-color: #e74c3c;
        }}
        .error-rate {{
            border-left-color: #f39c12;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .status-badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .status-completed {{
            background-color: #d4edda;
            color: #155724;
        }}
        .status-error {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .status-failed {{
            background-color: #fff3cd;
            color: #856404;
        }}
        .metadata {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .metadata-item {{
            margin: 5px 0;
        }}
        .metadata-label {{
            font-weight: 600;
            color: #34495e;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>"""

    def _generate_summary_section(self, result: EvaluationResult) -> str:
        """Generate summary section HTML."""
        summary = result.summary
        request = result.request

        metadata_items = ""
        if request.metadata:
            for key, value in request.metadata.items():
                metadata_items += f'<div class="metadata-item"><span class="metadata-label">{key}:</span> {value}</div>\n'

        metadata_html = ""
        if metadata_items:
            metadata_html = f"""
        <div class="metadata">
            <h3>Metadata</h3>
            {metadata_items}
        </div>"""

        return f"""
        <h2>Summary</h2>
        <div class="metadata">
            <div class="metadata-item"><span class="metadata-label">Model:</span> {request.model_name}</div>
            <div class="metadata-item"><span class="metadata-label">Benchmark:</span> {request.benchmark_name}</div>
            {f'<div class="metadata-item"><span class="metadata-label">Task:</span> {request.task_name}</div>' if request.task_name else ''}
            <div class="metadata-item"><span class="metadata-label">Start Time:</span> {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
            <div class="metadata-item"><span class="metadata-label">End Time:</span> {result.end_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
            <div class="metadata-item"><span class="metadata-label">Total Time:</span> {result.total_time:.2f}s</div>
        </div>
        {metadata_html}

        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-label">Total Tasks</div>
                <div class="summary-value">{summary.get('total_tasks', 0)}</div>
            </div>
            <div class="summary-card pass-rate">
                <div class="summary-label">Passed Tasks</div>
                <div class="summary-value">{summary.get('passed_tasks', 0)}</div>
            </div>
            <div class="summary-card fail-rate">
                <div class="summary-label">Failed Tasks</div>
                <div class="summary-value">{summary.get('failed_tasks', 0)}</div>
            </div>
            <div class="summary-card error-rate">
                <div class="summary-label">Error Tasks</div>
                <div class="summary-value">{summary.get('error_tasks', 0)}</div>
            </div>
            <div class="summary-card pass-rate">
                <div class="summary-label">Pass Rate</div>
                <div class="summary-value">{summary.get('pass_rate', 0):.1%}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Average Score</div>
                <div class="summary-value">{summary.get('average_score', 0):.3f}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Avg Execution Time</div>
                <div class="summary-value">{summary.get('average_execution_time', 0):.2f}s</div>
            </div>
        </div>"""

    def _generate_metrics_section(self, result: EvaluationResult) -> str:
        """Generate metrics section HTML."""
        if not result.metrics:
            return ""

        metrics_html = ""
        for category, metric_list in result.metrics.items():
            if not metric_list:
                continue

            rows = ""
            for metric in metric_list:
                rows += f"""
                <tr>
                    <td>{metric.name}</td>
                    <td>{metric.value:.4f}</td>
                    <td>{metric.unit or '-'}</td>
                </tr>"""

            metrics_html += f"""
            <h3>{category.replace('_', ' ').title()}</h3>
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Unit</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>"""

        if not metrics_html:
            return ""

        return f"""
        <h2>Metrics</h2>
        {metrics_html}"""

    def _generate_task_results_section(self, result: EvaluationResult) -> str:
        """Generate task results section HTML."""
        if not result.task_results:
            return "<h2>Task Results</h2><p>No task results available.</p>"

        rows = ""
        for task_result in result.task_results:
            status_class = f"status-{task_result.status.value.lower()}"
            status_text = task_result.status.value

            error_cell = ""
            if task_result.error_message:
                error_cell = f"<td>{task_result.error_message}</td>"
            else:
                error_cell = "<td>-</td>"

            rows += f"""
            <tr>
                <td>{task_result.task_id}</td>
                <td><span class="{status_class} status-badge">{status_text}</span></td>
                <td>{'Yes' if task_result.passed else 'No'}</td>
                <td>{task_result.score:.4f}</td>
                <td>{task_result.execution_time:.2f}s</td>
                {error_cell}
            </tr>"""

        return f"""
        <h2>Task Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Task ID</th>
                    <th>Status</th>
                    <th>Passed</th>
                    <th>Score</th>
                    <th>Execution Time</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>"""

    def _generate_footer(self) -> str:
        """Generate HTML footer."""
        return f"""
    <div class="footer">
        <p>Generated by AgentEval at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>"""


class CSVExporter:
    """Export evaluation results to CSV format."""

    def export(
        self,
        result: EvaluationResult,
        output_path: str,
        include_summary: bool = True
    ) -> None:
        """
        Export evaluation result to CSV file.

        Args:
            result: The evaluation result to export
            output_path: Path where CSV file will be saved
            include_summary: Whether to include summary as first rows
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            if include_summary:
                self._write_summary(writer, result)
                writer.writerow([])  # Empty row separator

            self._write_task_results(writer, result)

    def _write_summary(self, writer: csv.writer, result: EvaluationResult) -> None:
        """Write summary section to CSV."""
        writer.writerow(['EVALUATION SUMMARY'])
        writer.writerow(['Field', 'Value'])
        writer.writerow(['Model', result.request.model_name])
        writer.writerow(['Benchmark', result.request.benchmark_name])

        if result.request.task_name:
            writer.writerow(['Task', result.request.task_name])

        writer.writerow(['Start Time', result.start_time.strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['End Time', result.end_time.strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Total Time (seconds)', f'{result.total_time:.2f}'])
        writer.writerow([])

        writer.writerow(['SUMMARY STATISTICS'])
        writer.writerow(['Metric', 'Value'])
        for key, value in result.summary.items():
            if key == 'metrics':
                continue
            if isinstance(value, float):
                writer.writerow([key, f'{value:.4f}'])
            else:
                writer.writerow([key, value])
        writer.writerow([])

        if result.summary.get('metrics'):
            writer.writerow(['DETAILED METRICS'])
            writer.writerow(['Metric Name', 'Value'])
            for metric_name, metric_value in result.summary['metrics'].items():
                if isinstance(metric_value, float):
                    writer.writerow([metric_name, f'{metric_value:.4f}'])
                else:
                    writer.writerow([metric_name, metric_value])
            writer.writerow([])

    def _write_task_results(self, writer: csv.writer, result: EvaluationResult) -> None:
        """Write task results section to CSV."""
        writer.writerow(['TASK RESULTS'])

        # Header
        headers = [
            'Task ID',
            'Benchmark',
            'Status',
            'Passed',
            'Score',
            'Execution Time (s)',
            'Error Message'
        ]
        writer.writerow(headers)

        # Task results
        for task_result in result.task_results:
            row = [
                task_result.task_id,
                task_result.benchmark_name,
                task_result.status.value,
                'Yes' if task_result.passed else 'No',
                f'{task_result.score:.4f}',
                f'{task_result.execution_time:.2f}',
                task_result.error_message or ''
            ]
            writer.writerow(row)


class JSONExporter:
    """Export evaluation results to JSON format."""

    def export(
        self,
        result: EvaluationResult,
        output_path: str,
        indent: int = 2
    ) -> None:
        """
        Export evaluation result to JSON file.

        Args:
            result: The evaluation result to export
            output_path: Path where JSON file will be saved
            indent: Number of spaces for indentation
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = self._serialize_result(result)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    def _serialize_result(self, result: EvaluationResult) -> Dict[str, Any]:
        """Serialize evaluation result to dictionary."""
        return {
            'request': {
                'model_name': result.request.model_name,
                'benchmark_name': result.request.benchmark_name,
                'task_name': result.request.task_name,
                'max_samples': result.request.max_samples,
                'metadata': result.request.metadata
            },
            'summary': result.summary,
            'metrics': {
                category: [
                    {
                        'name': metric.name,
                        'value': metric.value,
                        'category': metric.category,
                        'unit': metric.unit
                    }
                    for metric in metric_list
                ]
                for category, metric_list in result.metrics.items()
            },
            'task_results': [
                {
                    'task_id': tr.task_id,
                    'benchmark_name': tr.benchmark_name,
                    'status': tr.status.value,
                    'passed': tr.passed,
                    'score': tr.score,
                    'execution_time': tr.execution_time,
                    'error_message': tr.error_message,
                    'metrics': tr.metrics,
                    'timestamp': tr.timestamp.isoformat()
                }
                for tr in result.task_results
            ],
            'timing': {
                'start_time': result.start_time.isoformat(),
                'end_time': result.end_time.isoformat(),
                'total_time': result.total_time
            },
            'error': result.error
        }
