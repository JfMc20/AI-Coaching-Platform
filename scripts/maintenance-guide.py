#!/usr/bin/env python3
"""
Maintenance guide for testing infrastructure improvements.
Provides actionable recommendations for ongoing maintenance and optimization.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import subprocess


class MaintenanceGuide:
    """Provides maintenance recommendations for testing infrastructure."""
    
    def __init__(self):
        self.workspace_root = Path.cwd()
        self.recommendations = []
    
    def add_recommendation(self, category: str, priority: str, title: str, description: str, action: str):
        """Add a maintenance recommendation."""
        self.recommendations.append({
            'category': category,
            'priority': priority,
            'title': title,
            'description': description,
            'action': action,
            'timestamp': datetime.now().isoformat()
        })
    
    def check_log_rotation(self):
        """Check if log rotation is needed."""
        logs_dir = self.workspace_root / "logs"
        if logs_dir.exists():
            total_size = sum(f.stat().st_size for f in logs_dir.rglob('*') if f.is_file())
            if total_size > 100 * 1024 * 1024:  # 100MB
                self.add_recommendation(
                    "Maintenance",
                    "Medium",
                    "Log Rotation Needed",
                    f"Log directory size: {total_size / 1024 / 1024:.1f}MB",
                    "Implement log rotation or cleanup old logs: rm logs/*.log.old"
                )
    
    def check_docker_cleanup(self):
        """Check if Docker cleanup is needed."""
        try:
            # Check Docker system usage
            result = subprocess.run(["docker", "system", "df"], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Build Cache' in line and 'GB' in line:
                        self.add_recommendation(
                            "Performance",
                            "Low",
                            "Docker Build Cache Cleanup",
                            "Large build cache detected",
                            "Run: docker builder prune -f"
                        )
        except Exception:
            pass
    
    def check_github_secrets(self):
        """Check GitHub Secrets configuration."""
        workflow_path = self.workspace_root / ".github" / "workflows" / "test.yml"
        if workflow_path.exists():
            content = workflow_path.read_text(encoding='utf-8')
            required_secrets = ["TEST_POSTGRES_PASSWORD", "TEST_JWT_SECRET_KEY"]
            
            for secret in required_secrets:
                if f"secrets.{secret}" in content:
                    self.add_recommendation(
                        "Security",
                        "High",
                        f"Verify GitHub Secret: {secret}",
                        "Ensure secret is configured in repository settings",
                        f"Go to Repository Settings → Secrets → Actions → Add {secret}"
                    )
    
    def check_dependency_updates(self):
        """Check for dependency updates."""
        requirements_files = [
            "requirements.txt",
            "requirements-test.txt"
        ]
        
        for req_file in requirements_files:
            req_path = self.workspace_root / req_file
            if req_path.exists():
                self.add_recommendation(
                    "Security",
                    "Medium",
                    f"Review {req_file} Dependencies",
                    "Regular dependency updates improve security",
                    f"Run: pip-audit {req_file} && pip list --outdated"
                )
    
    def check_test_data_cleanup(self):
        """Check test data cleanup configuration."""
        sql_path = self.workspace_root / "scripts" / "docker-entrypoint-initdb.d" / "03-setup-functions.sql"
        if sql_path.exists():
            content = sql_path.read_text()
            if "cleanup_test_data" in content:
                self.add_recommendation(
                    "Maintenance",
                    "Low",
                    "Test Data Cleanup Validation",
                    "Verify cleanup function works with current schema",
                    "Test: SELECT cleanup_test_data(true); in test database"
                )
    
    def check_performance_monitoring(self):
        """Check performance monitoring setup."""
        self.add_recommendation(
            "Monitoring",
            "Medium",
            "Set Up Performance Monitoring",
            "Track test execution times and resource usage",
            "Implement: pytest-benchmark for performance regression detection"
        )
        
        self.add_recommendation(
            "Monitoring",
            "Low",
            "CI/CD Metrics Dashboard",
            "Monitor build times, artifact sizes, and success rates",
            "Set up GitHub Actions insights or external monitoring"
        )
    
    def generate_weekly_tasks(self):
        """Generate weekly maintenance tasks."""
        weekly_tasks = [
            "Review and rotate log files if needed",
            "Check Docker system usage: docker system df",
            "Verify all tests are passing in CI/CD",
            "Review GitHub Actions artifact storage usage",
            "Check for security updates in dependencies"
        ]
        
        for task in weekly_tasks:
            self.add_recommendation(
                "Weekly",
                "Low",
                "Weekly Maintenance Task",
                task,
                "Add to weekly maintenance checklist"
            )
    
    def generate_monthly_tasks(self):
        """Generate monthly maintenance tasks."""
        monthly_tasks = [
            "Update base Docker images to latest versions",
            "Review and update GitHub Secrets if needed",
            "Audit test coverage and add missing tests",
            "Review and optimize Docker Compose configurations",
            "Check for new testing tools and best practices"
        ]
        
        for task in monthly_tasks:
            self.add_recommendation(
                "Monthly",
                "Medium",
                "Monthly Maintenance Task",
                task,
                "Add to monthly maintenance checklist"
            )
    
    def generate_optimization_opportunities(self):
        """Generate future optimization opportunities."""
        optimizations = [
            {
                "title": "Multi-stage Docker Builds",
                "description": "Further reduce image size with build-time vs runtime dependencies",
                "benefit": "Additional 20-30% image size reduction"
            },
            {
                "title": "Parallel Test Execution",
                "description": "Run tests in parallel to reduce CI/CD time",
                "benefit": "50-70% faster test execution"
            },
            {
                "title": "Test Result Caching",
                "description": "Cache test results for unchanged code",
                "benefit": "Skip redundant tests, faster feedback"
            },
            {
                "title": "Resource Monitoring",
                "description": "Add memory and CPU monitoring to tests",
                "benefit": "Detect performance regressions early"
            }
        ]
        
        for opt in optimizations:
            self.add_recommendation(
                "Future",
                "Low",
                opt["title"],
                opt["description"],
                f"Research and implement - Expected benefit: {opt['benefit']}"
            )
    
    def generate_report(self):
        """Generate comprehensive maintenance report."""
        print("🔧 Testing Infrastructure Maintenance Guide")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run all checks
        self.check_log_rotation()
        self.check_docker_cleanup()
        self.check_github_secrets()
        self.check_dependency_updates()
        self.check_test_data_cleanup()
        self.check_performance_monitoring()
        self.generate_weekly_tasks()
        self.generate_monthly_tasks()
        self.generate_optimization_opportunities()
        
        # Group recommendations by priority
        by_priority = {}
        for rec in self.recommendations:
            priority = rec['priority']
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(rec)
        
        # Display by priority
        priority_order = ['High', 'Medium', 'Low']
        for priority in priority_order:
            if priority in by_priority:
                print(f"\n🚨 {priority} Priority Tasks:")
                print("-" * 40)
                
                for rec in by_priority[priority]:
                    icon = "🔴" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
                    print(f"{icon} {rec['title']} ({rec['category']})")
                    print(f"   📝 {rec['description']}")
                    print(f"   🎯 Action: {rec['action']}")
                    print()
        
        # Summary statistics
        total_recs = len(self.recommendations)
        by_category = {}
        for rec in self.recommendations:
            cat = rec['category']
            by_category[cat] = by_category.get(cat, 0) + 1
        
        print("📊 Summary:")
        print(f"   Total recommendations: {total_recs}")
        for category, count in sorted(by_category.items()):
            print(f"   {category}: {count}")
        
        # Save to file
        report_file = self.workspace_root / "maintenance-report.json"
        with open(report_file, 'w') as f:
            json.dump({
                'generated': datetime.now().isoformat(),
                'recommendations': self.recommendations,
                'summary': {
                    'total': total_recs,
                    'by_category': by_category,
                    'by_priority': {p: len(by_priority.get(p, [])) for p in priority_order}
                }
            }, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # Quick start commands
        print("\n🚀 Quick Start Commands:")
        print("   # Run validation of all improvements")
        print("   python scripts/validate-all-improvements.py")
        print()
        print("   # Run demonstration of improvements")
        print("   python scripts/demo-improvements.py")
        print()
        print("   # Clean up test environment")
        print("   python scripts/clean-test-state.py")
        print()
        print("   # Validate compose services")
        print("   python scripts/validate-compose-services.py docker-compose.test.yml --services postgres-test redis-test --check-health")


def main():
    """Main function."""
    guide = MaintenanceGuide()
    guide.generate_report()


if __name__ == "__main__":
    main()