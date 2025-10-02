#!/usr/bin/env python3
"""
Statistical Validation of Test Reliability
Implements 100x validation framework for HeadlessPM test suite reliability measurement.
"""

import os
import sys
import time
import json
import subprocess
import statistics
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Determine project root directory (where this script is located)
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.append(str(PROJECT_ROOT))

class ReliabilityValidator:
    """100x validation framework for sustained test reliability measurement."""

    def __init__(self, target_runs: int = 100, timeout_per_run: int = 600, project_root: Path = None):
        self.target_runs = target_runs
        self.timeout_per_run = timeout_per_run
        self.project_root = project_root or PROJECT_ROOT
        self.results: List[Dict] = []
        self.start_time = datetime.now()
        
    def run_single_test_suite(self, run_number: int) -> Dict:
        """Run single test suite and capture detailed results."""
        print(f"\n=== RUN {run_number}/{self.target_runs} ===")
        start = time.time()
        
        try:
            # Run complete test suite with timeout
            cmd = ["python", "-m", "pytest", "tests/", "--tb=no", "-q"]
            result = subprocess.run(
                cmd,
                timeout=self.timeout_per_run,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            duration = time.time() - start
            
            # Parse pytest output for pass/fail counts
            output_lines = result.stdout.split('\n')
            summary_line = None
            for line in output_lines:
                if 'failed' in line and 'passed' in line:
                    summary_line = line
                    break
            
            passed = failed = 0
            if summary_line:
                # Parse "2 failed, 146 passed" format
                parts = summary_line.split()
                for i, part in enumerate(parts):
                    if part == 'failed,':
                        failed = int(parts[i-1])
                    elif part == 'passed,':
                        passed = int(parts[i-1])
                    elif part.endswith('passed'):
                        if 'failed' not in summary_line:
                            passed = int(part.replace('passed', ''))
            
            total = passed + failed
            success_rate = passed / total if total > 0 else 0
            
            run_result = {
                'run_number': run_number,
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': duration,
                'return_code': result.returncode,
                'passed': passed,
                'failed': failed,
                'total': total,
                'success_rate': success_rate,
                'output_summary': summary_line or result.stdout.split('\n')[-3:],
            }
            
            print(f"✅ Run {run_number}: {passed}/{total} passed ({success_rate*100:.1f}%) in {duration:.1f}s")
            return run_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            print(f"⏰ Run {run_number}: TIMEOUT after {duration:.1f}s")
            return {
                'run_number': run_number,
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': duration,
                'return_code': -1,
                'passed': 0,
                'failed': 148,  # Assume total failure on timeout
                'total': 148,
                'success_rate': 0.0,
                'output_summary': ['TIMEOUT'],
            }
        except Exception as e:
            duration = time.time() - start
            print(f"❌ Run {run_number}: ERROR - {e}")
            return {
                'run_number': run_number,
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': duration,
                'return_code': -2,
                'passed': 0,
                'failed': 148,
                'total': 148,
                'success_rate': 0.0,
                'output_summary': [str(e)],
            }

    def run_validation(self) -> Dict:
        """Execute 100x validation and generate comprehensive report."""
        print(f"🎯 STARTING 100x RELIABILITY VALIDATION")
        print(f"Target: {self.target_runs} runs, {self.timeout_per_run}s timeout per run")
        print(f"Expected duration: ~{(self.target_runs * self.timeout_per_run) / 60:.0f} minutes")
        
        # Run test suite multiple times
        for run_num in range(1, self.target_runs + 1):
            result = self.run_single_test_suite(run_num)
            self.results.append(result)
            
            # Save intermediate results every 10 runs
            if run_num % 10 == 0:
                self._save_intermediate_results(run_num)
                self._print_intermediate_stats()
        
        # Generate final comprehensive report
        final_report = self._generate_final_report()
        self._save_final_report(final_report)
        self._print_final_summary(final_report)
        
        return final_report
    
    def _save_intermediate_results(self, run_num: int):
        """Save intermediate results to file."""
        filename = f"reliability_validation_intermediate_run_{run_num}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def _print_intermediate_stats(self):
        """Print intermediate statistics."""
        if not self.results:
            return
            
        success_rates = [r['success_rate'] for r in self.results]
        avg_rate = statistics.mean(success_rates)
        total_passed = sum(r['passed'] for r in self.results)
        total_tests = sum(r['total'] for r in self.results)
        
        print(f"📊 INTERMEDIATE: {len(self.results)} runs, "
              f"avg {avg_rate*100:.1f}% success, "
              f"{total_passed}/{total_tests} total passed")
    
    def _generate_final_report(self) -> Dict:
        """Generate comprehensive final report."""
        if not self.results:
            return {"error": "No results to analyze"}
        
        # Basic statistics
        success_rates = [r['success_rate'] for r in self.results]
        durations = [r['duration_seconds'] for r in self.results]
        
        total_runs = len(self.results)
        successful_runs = sum(1 for r in self.results if r['return_code'] == 0)
        
        # Detailed statistics
        avg_success_rate = statistics.mean(success_rates)
        median_success_rate = statistics.median(success_rates)
        min_success_rate = min(success_rates)
        max_success_rate = max(success_rates)
        stdev_success_rate = statistics.stdev(success_rates) if len(success_rates) > 1 else 0
        
        avg_duration = statistics.mean(durations)
        total_duration = sum(durations)
        
        # Count perfect runs (148/148)
        perfect_runs = sum(1 for r in self.results if r['success_rate'] == 1.0)
        near_perfect_runs = sum(1 for r in self.results if r['success_rate'] >= 0.986)  # 146/148 or better
        
        # Test failure analysis
        failure_patterns = {}
        for result in self.results:
            if result['failed'] > 0:
                pattern = f"{result['passed']}/{result['total']}"
                failure_patterns[pattern] = failure_patterns.get(pattern, 0) + 1
        
        return {
            'validation_summary': {
                'target_runs': self.target_runs,
                'actual_runs': total_runs,
                'successful_runs': successful_runs,
                'completion_rate': successful_runs / total_runs,
                'validation_duration_hours': total_duration / 3600,
                'timestamp': datetime.now().isoformat(),
            },
            'reliability_metrics': {
                'average_success_rate': avg_success_rate,
                'median_success_rate': median_success_rate,
                'minimum_success_rate': min_success_rate,
                'maximum_success_rate': max_success_rate,
                'success_rate_std_dev': stdev_success_rate,
                'perfect_runs_count': perfect_runs,
                'perfect_runs_percentage': perfect_runs / total_runs * 100,
                'near_perfect_runs_count': near_perfect_runs,
                'near_perfect_runs_percentage': near_perfect_runs / total_runs * 100,
            },
            'performance_metrics': {
                'average_duration_seconds': avg_duration,
                'total_duration_seconds': total_duration,
                'total_duration_hours': total_duration / 3600,
                'runs_per_hour': total_runs / (total_duration / 3600),
            },
            'failure_analysis': {
                'failure_patterns': failure_patterns,
                'most_common_result': max(failure_patterns.items(), key=lambda x: x[1]) if failure_patterns else None,
            },
            'acceptance_criteria': {
                'target': '100% test pass rate for 100x runs (148/148 × 100)',
                'achieved': f"{perfect_runs}/100 perfect runs ({perfect_runs}%)",
                'criteria_met': perfect_runs == self.target_runs,
                'notes': 'Sustained reliability validation complete'
            },
            'raw_results': self.results[-10:],  # Last 10 runs for reference
        }
    
    def _save_final_report(self, report: Dict):
        """Save final comprehensive report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reliability_validation_final_report_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"💾 Final report saved: {filename}")
    
    def _print_final_summary(self, report: Dict):
        """Print final validation summary."""
        print(f"\n{'='*60}")
        print(f"🎯 FINAL RELIABILITY VALIDATION REPORT")
        print(f"{'='*60}")
        
        summary = report['validation_summary']
        metrics = report['reliability_metrics']
        performance = report['performance_metrics']
        criteria = report['acceptance_criteria']
        
        print(f"📊 VALIDATION SUMMARY:")
        print(f"   Runs completed: {summary['actual_runs']}/{summary['target_runs']} ({summary['completion_rate']*100:.1f}%)")
        print(f"   Total duration: {summary['validation_duration_hours']:.1f} hours")
        
        print(f"\n🎯 RELIABILITY METRICS:")
        print(f"   Average success rate: {metrics['average_success_rate']*100:.2f}%")
        print(f"   Perfect runs (148/148): {metrics['perfect_runs_count']}/{summary['actual_runs']} ({metrics['perfect_runs_percentage']:.1f}%)")
        print(f"   Near-perfect runs (≥146/148): {metrics['near_perfect_runs_count']}/{summary['actual_runs']} ({metrics['near_perfect_runs_percentage']:.1f}%)")
        print(f"   Success rate std dev: {metrics['success_rate_std_dev']*100:.2f}%")
        
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"   Average run time: {performance['average_duration_seconds']:.1f}s")
        print(f"   Throughput: {performance['runs_per_hour']:.1f} runs/hour")
        
        print(f"\n🏆 ACCEPTANCE CRITERIA:")
        print(f"   Target: {criteria['target']}")
        print(f"   Achieved: {criteria['achieved']}")
        print(f"   Criteria met: {'✅ YES' if criteria['criteria_met'] else '❌ NO'}")
        
        if report.get('failure_analysis', {}).get('most_common_result'):
            pattern, count = report['failure_analysis']['most_common_result']
            print(f"\n📋 MOST COMMON RESULT: {pattern} ({count} occurrences)")

def main():
    """Main execution function."""
    print("🚀 HeadlessPM Reliability Validation Framework")
    print("Testing sustained reliability across 100 runs")
    print(f"Project root: {PROJECT_ROOT}")

    # Change to project directory
    os.chdir(PROJECT_ROOT)
    
    # Activate virtual environment
    if not os.environ.get('VIRTUAL_ENV'):
        print("⚠️  Virtual environment not detected. Ensure 'source venv/bin/activate' is run.")
    
    validator = ReliabilityValidator(target_runs=100, timeout_per_run=600)
    
    try:
        final_report = validator.run_validation()
        
        # Check if acceptance criteria met
        if final_report['acceptance_criteria']['criteria_met']:
            print("\n🎉 ACCEPTANCE CRITERIA ACHIEVED!")
            print("✅ 100% test pass rate sustained across 100 runs")
        else:
            perfect_runs = final_report['reliability_metrics']['perfect_runs_count']
            avg_rate = final_report['reliability_metrics']['average_success_rate'] * 100
            print(f"\n📈 SIGNIFICANT PROGRESS:")
            print(f"✅ {perfect_runs}/100 perfect runs achieved")
            print(f"✅ {avg_rate:.1f}% average reliability sustained")
            
        return final_report
        
    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted by user")
        return None
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return None

if __name__ == "__main__":
    main()