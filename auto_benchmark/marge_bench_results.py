import re
import pandas as pd
from pathlib import Path

# 定义要提取的指标列表（包含带括号的指标）
metrics = [
    "Backend", "Traffic request rate", "Max request concurrency", "Successful requests",
    "Benchmark duration (s)", "Total input tokens", "Total generated tokens",
    "Total generated tokens (retokenized)", "Request throughput (req/s)",
    "Input token throughput (tok/s)", "Output token throughput (tok/s)",
    "Total token throughput (tok/s)", "Concurrency",  # 这里是文件内容中的实测并发数
    "Mean E2E Latency (ms)", "Median E2E Latency (ms)",
    "Mean TTFT (ms)", "Median TTFT (ms)", "P99 TTFT (ms)",
    "Mean ITL (ms)", "Median ITL (ms)", "P95 ITL (ms)", "P99 ITL (ms)", "Max ITL (ms)"
]

data = []
report_dir = Path("/project/full_benchmark/sglang_bench_results_20250815_040232")  # 报告文件所在目录
SECONDS_PER_DAY = 86400

for file in report_dir.glob("concurrency_*.txt"):
    print(f"处理文件: {file.name}")
    
    # 1. 解析文件名中的【配置的最大并发数】
    name_pattern = re.compile(r"concurrency_(\d+)_input_(\d+)_output_(\d+)\.txt")
    match = name_pattern.match(file.name)
    if not match:
        print(f"文件名不匹配: {file.name}，跳过")
        continue
    configured_concurrency, input_len, output_len = match.groups()  # 配置的并发数
    
    # 2. 读取文件内容
    try:
        content = file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"读取文件失败 {file.name}: {e}")
        continue
    
    # 3. 定位报告片段
    start_marker = "============ Serving Benchmark Result ============"
    end_marker = "=================================================="
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    if start_idx == -1 or end_idx == -1:
        print(f"文件 {file.name} 未找到报告标记，跳过")
        continue
    bench_content = content[start_idx:end_idx]
    
    # 4. 提取指标（区分配置并发数和实测并发数）
    row = {
        "Configured Concurrency": configured_concurrency,  # 文件名中的配置并发数
        "Input Length": input_len,
        "Output Length": output_len
    }
    for metric in metrics:
        metric_pattern = re.compile(rf"{re.escape(metric)}:\s+(.*?)[\n\r]")
        metric_match = metric_pattern.search(bench_content)
        if metric_match:
            value = metric_match.group(1).strip()
            # 对文件内容中的"Concurrency"重命名为"Measured Concurrency"（实测并发数）
            if metric == "Concurrency":
                row["Measured Concurrency"] = value
            else:
                row[metric] = value
        else:
            if metric == "Concurrency":
                row["Measured Concurrency"] = None
            else:
                row[metric] = None
            print(f"文件 {file.name} 未找到指标: {metric}")
    
    # 5. 计算每日token数
    try:
        input_throughput = float(row.get("Input token throughput (tok/s)", 0))
        row["每日最大输入token数"] = int(round(input_throughput * SECONDS_PER_DAY, 0))
        
        output_throughput = float(row.get("Output token throughput (tok/s)", 0))
        row["每日最大输出token数"] = int(round(output_throughput * SECONDS_PER_DAY, 0))
    except (ValueError, TypeError):
        row["每日最大输入token数"] = None
        row["每日最大输出token数"] = None
        print(f"文件 {file.name} 吞吐量数据无效，无法计算每日token数")
    
    data.append(row)

# 6. 生成汇总表格
if data:
    df = pd.DataFrame(data)
    # 调整列顺序（配置并发数在前，实测并发数在指标中）
    columns_order = [
        "Configured Concurrency", "Input Length", "Output Length"
    ] + [m if m != "Concurrency" else "Measured Concurrency" for m in metrics] + [
        "每日最大输入token数", "每日最大输出token数"
    ]
    df = df.reindex(columns=columns_order)
    df.to_csv("benchmark_summary_fixed.csv", index=False, encoding="utf-8")
    print("汇总完成，结果保存至 benchmark_summary_fixed.csv")
else:
    print("未找到有效数据")