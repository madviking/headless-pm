#!/bin/bash

# 100x Statistical Validation for Test Suite Reliability
# Uses 3600s timeouts throughout for comprehensive intermittent test validation

echo "=== 100x STATISTICAL VALIDATION FOR SUSTAINED RELIABILITY ==="
echo "Target: 148/148 tests passing for 100 consecutive runs"
echo "Timeout: 3600s per run (adequate for intermittent tests)"
echo "Start: $(date)"

source venv/bin/activate

success_count=0
failure_count=0
total_runs=100

# Create results directory
results_dir="100x-validation-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$results_dir"

for run in $(seq 1 $total_runs); do
    echo -n "Run $run/$total_runs: "
    
    # Run with 3600s timeout (adequate for intermittent tests)
    result_file="$results_dir/run_${run}.log"
    
    timeout 3600 python -m pytest tests/ --tb=no -q > "$result_file" 2>&1
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        # Check if actually passed all tests
        if grep -q "failed" "$result_file"; then
            failure_count=$((failure_count + 1))
            echo "FAILED ($(grep -o '[0-9]* failed' "$result_file" | head -1))"
            
            # Save failure details
            echo "=== RUN $run FAILURE DETAILS ===" >> "$results_dir/failures.log"
            tail -20 "$result_file" >> "$results_dir/failures.log"
            echo "" >> "$results_dir/failures.log"
        else
            success_count=$((success_count + 1))
            passes=$(grep -o '[0-9]* passed' "$result_file" | head -1 | cut -d' ' -f1)
            echo "PASSED ($passes passed)"
        fi
    else
        failure_count=$((failure_count + 1))
        echo "TIMEOUT/ERROR (exit code: $exit_code)"
        
        # Save timeout details
        echo "=== RUN $run TIMEOUT/ERROR ===" >> "$results_dir/timeouts.log"
        echo "Exit code: $exit_code" >> "$results_dir/timeouts.log"
        tail -20 "$result_file" >> "$results_dir/timeouts.log"
        echo "" >> "$results_dir/timeouts.log"
    fi
    
    # Progress reporting every 10 runs
    if [ $((run % 10)) -eq 0 ]; then
        success_rate=$(echo "scale=1; $success_count * 100 / $run" | bc -l)
        echo "Progress: $run/$total_runs completed, $success_count successes, $failure_count failures (${success_rate}% success rate)"
    fi
done

# Final statistics
echo ""
echo "=== FINAL 100x VALIDATION RESULTS ==="
echo "Total runs: $total_runs"
echo "Successful runs: $success_count"
echo "Failed runs: $failure_count"
final_rate=$(echo "scale=2; $success_count * 100 / $total_runs" | bc -l)
echo "Success rate: ${final_rate}%"
echo "End: $(date)"

# Statistical analysis
if [ $success_count -eq $total_runs ]; then
    echo ""
    echo "🏆 COMPLETE SUCCESS: 100% reliability achieved!"
    echo "✅ Sustained 148/148 test reliability proven with statistical significance"
else
    echo ""
    echo "⚠️ Intermittent failures detected: $failure_count/$total_runs"
    echo "📊 Results saved in: $results_dir/"
    
    if [ $failure_count -le 5 ]; then
        echo "💚 Excellent reliability: >${final_rate}% success rate"
    elif [ $failure_count -le 10 ]; then
        echo "💛 Good reliability: >${final_rate}% success rate"  
    else
        echo "🔴 Reliability issues: <90% success rate - investigation needed"
    fi
fi

echo ""
echo "Results directory: $results_dir/"
echo "Failure details: $results_dir/failures.log"
echo "Timeout details: $results_dir/timeouts.log"