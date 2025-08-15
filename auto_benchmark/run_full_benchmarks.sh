#!/bin/bash

# 定义测试参数组合
CONCURRENCIES=(128 32 8 1)                   # 并发数
INPUT_LENGTHS=(32 64 128 256 512 1048 8192)   # 输入token长度
OUTPUT_LENGTHS=(32 64 128 256 512 1048 8192)  # 输出token长度

# 创建报告根目录（按时间戳命名，避免覆盖）
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_ROOT="sglang_bench_results_${TIMESTAMP}"
mkdir -p ${REPORT_ROOT}
echo "所有测试报告将保存至：$(pwd)/${REPORT_ROOT}"
echo "总测试组合数：${#CONCURRENCIES[@]} × ${#INPUT_LENGTHS[@]} × ${#OUTPUT_LENGTHS[@]} = $(( ${#CONCURRENCIES[@]} * ${#INPUT_LENGTHS[@]} * ${#OUTPUT_LENGTHS[@]} )) 组"
echo "开始测试..."
echo "========================================="

# 遍历所有参数组合
for concurrency in "${CONCURRENCIES[@]}"; do
  for input_len in "${INPUT_LENGTHS[@]}"; do
    for output_len in "${OUTPUT_LENGTHS[@]}"; do
      # 定义当前组合的报告文件名（包含所有参数，便于区分）
      report_file="${REPORT_ROOT}/concurrency_${concurrency}_input_${input_len}_output_${output_len}.txt"
      
      # 打印当前测试进度
      echo "正在测试：并发数=${concurrency}，输入长度=${input_len}，输出长度=${output_len}"
      echo "报告文件：${report_file}"
      
      # 运行压测命令（重定向 stdout 和 stderr 到报告文件）
      python -m sglang.bench_serving \
        --backend sglang \
        --host 0.0.0.0 \
        --port 25815 \
        --model /root/.cache/Mistral-Small-24B-Instruct-2501-abliterated \
        --dataset-name sharegpt \
        --dataset-path /root/.cache/ShareGPT_Vicuna_unfiltered/ShareGPT_V3_unfiltered_cleaned_split.json \
        --random-input-len ${input_len} \
        --random-output-len ${output_len} \
        --max-concurrency ${concurrency} \
        --num-prompts 128 \
        > ${report_file} 2>&1
      
      # 检查命令是否执行成功
      if [ $? -eq 0 ]; then
        echo "测试完成：并发数=${concurrency}，输入长度=${input_len}，输出长度=${output_len}"
      else
        echo "⚠️ 测试失败：并发数=${concurrency}，输入长度=${input_len}，输出长度=${output_len}（详情见报告文件）"
      fi
      echo "-----------------------------------------"
    done
  done
done

echo "所有测试结束！完整报告目录：$(pwd)/${REPORT_ROOT}"