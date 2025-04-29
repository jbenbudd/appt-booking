#!/usr/bin/env python3
"""
Analyze Load Test Results

This script parses the load_test.log file and generates a simple analysis of the results.
"""

import re
import statistics
import matplotlib.pyplot as plt
from collections import defaultdict

def parse_log_file(filename="load_test.log"):
    """Parse the log file and extract request data"""
    request_pattern = re.compile(r'(.*) - INFO - Request to (.*): status=(\d+|error), duration=([\d\.]+)s')
    
    requests = []
    with open(filename, 'r') as f:
        for line in f:
            match = request_pattern.match(line)
            if match:
                timestamp, endpoint, status, duration = match.groups()
                requests.append({
                    'timestamp': timestamp,
                    'endpoint': endpoint,
                    'status': status if status == 'error' else int(status),
                    'duration': float(duration)
                })
    
    return requests

def analyze_results(requests):
    """Analyze the load test results"""
    if not requests:
        print("No requests found in log file")
        return
    
    # Basic stats
    total_requests = len(requests)
    successful_requests = sum(1 for r in requests if isinstance(r['status'], int) and 200 <= r['status'] < 300)
    success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
    
    # Latency stats
    durations = [r['duration'] for r in requests]
    avg_duration = statistics.mean(durations)
    median_duration = statistics.median(durations)
    max_duration = max(durations)
    min_duration = min(durations)
    p95_duration = sorted(durations)[int(len(durations) * 0.95)]
    
    # Group by endpoint
    endpoints = defaultdict(list)
    for r in requests:
        endpoints[r['endpoint']].append(r['duration'])
    
    # Print summary
    print(f"=== Load Test Results Summary ===")
    print(f"Total Requests: {total_requests}")
    print(f"Successful Requests: {successful_requests} ({success_rate:.2f}%)")
    print(f"Average Response Time: {avg_duration:.3f}s")
    print(f"Median Response Time: {median_duration:.3f}s")
    print(f"95th Percentile Response Time: {p95_duration:.3f}s")
    print(f"Min/Max Response Time: {min_duration:.3f}s / {max_duration:.3f}s")
    
    print("\n=== Results by Endpoint ===")
    for endpoint, times in endpoints.items():
        avg_time = statistics.mean(times)
        count = len(times)
        print(f"{endpoint}: {count} requests, avg: {avg_time:.3f}s")
    
    # Create a simple histogram of response times
    plt.figure(figsize=(10, 6))
    plt.hist(durations, bins=50, alpha=0.7, color='blue')
    plt.xlabel('Response Time (seconds)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Response Times')
    plt.grid(True, alpha=0.3)
    plt.savefig('response_time_distribution.png')
    print("\nGenerated response time histogram: response_time_distribution.png")
    
    # Create a bar chart of average response times by endpoint
    plt.figure(figsize=(10, 6))
    endpoints_avg = {k: statistics.mean(v) for k, v in endpoints.items()}
    plt.bar(endpoints_avg.keys(), endpoints_avg.values(), color='green', alpha=0.7)
    plt.xlabel('Endpoint')
    plt.ylabel('Average Response Time (seconds)')
    plt.title('Average Response Time by Endpoint')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('endpoint_response_times.png')
    print("Generated endpoint comparison chart: endpoint_response_times.png")
    
if __name__ == "__main__":
    print("Analyzing load test results...")
    requests = parse_log_file()
    analyze_results(requests)
    print("\nAnalysis complete!") 