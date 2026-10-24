<div align="center">

# 📊 Understanding DeepResearch via Reports

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
<br>
<a href="./Communication.md"><img src="https://img.shields.io/badge/💬Feishu-Group-07c160?style=for-the-badge&logoColor=white&labelColor=1a1a2e"></a>
<a href="./Communication.md"><img src="https://img.shields.io/badge/WeChat-Group-07c160?style=for-the-badge&logo=wechat&logoColor=white&labelColor=1a1a2e"></a>

**🔍 一个用于长篇技术报告/研究报告的自动化评测与事实核查工具集**


*聚焦报告质量评估与内容事实性验证*

</div>

---
## 为什么需要通过理解reports来理解deepreearch系统？

因为报告是 DeepResearch 输出中最经典且最具代表性的形式。高质量的研究报告具备清晰的结构、严谨的逻辑、密集的信息含量以及真实可靠的引用，这些特征对于知识密集型研究场景至关重要。为此，我们提出了 DeepResearch-ReportEval 框架——一种混合评估方法，结合 LLM-as-a-Jduge 对最终报告质量进行自动评估，并辅以专家人工判断以确保可靠性。该框架从多个维度评估报告质量，包括全面性、冗余度和事实准确性。我们同时发布了一个精心整理的数据集，包含覆盖多样类别的 100 个查询，以及由 [Qwen-DeepResearch](https://chat.qwen.ai/?inputFeature=deep_research) 生成的 100 份对应报告，以支持系统化的评估研究。


## ✨ 功能特色

<div align="center">

| 🎯 质量评测 | 🔍 事实核查 | 📈 重复性检测 |
|:---:|:---:|:---:|
| 五维度评分系统 | 网页内容验证 | 段落对分析 |

</div>

## 🚀 核心功能

### 📊 质量评测 (`judge_score.py`)
- ✅ **五维度评分**：完整性、连贯性、清晰度、洞见性、总体评分
- 🔄 **重复性检测**：智能段落对采样，计算平均重复性分数
- 📝 **详细原因**：提供评分依据与解释说明
- 💾 **断点恢复**：支持中断续跑，避免重复计算

### 🔍 事实核查 (`judge_fact.py`)
- 🌐 **网页抓取**：支持 Firecrawl 和 Jina Reader 双引擎
- 📋 **批量验证**：对 URL 上下文进行逐条事实核验
- 🎯 **精确评分**：-1（不支持）/0（不确定）/1（支持）
- 📄 **详细说明**：提供核查依据与支持度分析

---

## 📁 项目结构

```
DeepResearch-ReportEval/
├── 📊 judge_score.py          # 质量评测主脚本
├── 🔍 judge_fact.py           # 事实核查主脚本
├── 🛠️ Atools.py               # 工具函数与模型调用
├── 📝 Aprompts.py             # 提示词模板
├── 📂 data/                   # 数据集
│   ├── topic/                 # 高质量主题
│   └── report/                # 来自Qwen-DeepResearch的研究报告，采集时间为九月初, 2025年
└── 📋 example/                # 示例数据与输出
    ├── judge_fact_result/     # 事实核查示例
    └── judge_score_result/    # 质量与冗余评分示例
```

---

## ⚙️ 环境配置

### 📋 系统要求
- **Python**: 3.10+ 
- **操作系统**: Windows / macOS / Linux

### 📦 依赖安装

```bash
# 克隆项目
git clone https://github.com/HKUDS/DeepResearch-Eval.git
cd DeepResearch-Eval

# 安装依赖
pip install openai json-repair firecrawl-python python-dotenv tqdm requests dashscope
```

### 🔑 环境变量配置

创建 `.env` 文件或设置环境变量：

```bash
# 必需配置
export OPENAI_API_KEY="your-openai-api-key"
export FIRECRAWL_KEY="your-firecrawl-key"        # 或
export JINA_API_KEY="your-jina-api-key"

# 可选配置
export OPENAI_API_BASE="your api base"  # 自定义 API 端点
```

---

## 📊 数据格式

### 📝 质量评测

**输入格式** (JSONL):
```json
{"topic": "人工智能在医疗领域的应用", "report": "# 报告标题\n\n## 引言\n..."}
```

**输出格式** (JSON):
```json
{
  "file_id": "abc123...",
  "topic": "人工智能在医疗领域的应用",
  "comprehensiveness_score": 2,
  "coherence_score": 3,
  "clarity_score": 4,
  "insight_score": 3,
  "overall_score": 3,
  "quality_reason": "报告结构清晰，论证充分...",
  "repeat_score": 3.12,
  "repeat_results": [...]
}
```

### 🔍 事实核查

**输入格式** (JSONL):
```json
{"https://example.com/page": {"contexts": ["句子A", "句子B", ...]}}
```

**输出格式** (JSONL):
```json
{"url": "https://example.com/page", "context": "句子A", "label": {"is_factual": 1, "sentence_support": "..."}}
```

> 📌 **评分说明**: `is_factual` 取值 -1（不支持）/ 0（不确定）/ 1（支持）

---

## 🚀 快速开始

### 📋 准备数据
- **质量评测**: 使用 `data/topic/high_quality_topics.jsonl` 或自备 JSONL 格式数据
- **事实核查**: 参考 `example/judge_fact_result/example_fact_judge_input.jsonl` 格式

### 💻 运行示例

#### 📊 质量评测
```bash
# 基础运行
python judge_score.py \
  --inputpath data/topic/high_quality_topics.jsonl \
  --outputpath exp/score_results

# 断点恢复
python judge_score.py \
  --inputpath data/topic/high_quality_topics.jsonl \
  --outputpath exp/score_results \
  --resume

# 清除断点重新开始
python judge_score.py \
  --inputpath data/topic/high_quality_topics.jsonl \
  --outputpath exp/score_results \
  --clear_checkpoint
```

#### 🔍 事实核查
```bash
# 核查模式（默认）
python judge_fact.py \
  --inputpath example/judge_fact_result/example_fact_judge_input.jsonl \
  --outputpath example/judge_fact_result/example_fact_judge_output.jsonl \
  --provider jina \
  --limit 3 \
  --task judge

# 仅抓取模式
python judge_fact.py \
  --inputpath example/judge_fact_result/example_fact_judge_input.jsonl \
  --outputpath example/judge_fact_result/example_fact_scrape.out.jsonl \
  --provider jina \
  --limit 3 \
  --task scrape
```

---

## 📁 输出文件

### 📊 质量评测输出
```
exp/score_results/
├── abc123def456.json    # 主题1的评测结果
├── def456ghi789.json    # 主题2的评测结果
└── ...

checkpoint.json         # 断点文件（项目根目录）

exp/
├── judge.txt            # 详细日志
└── judge.json           # 进度记录
```

### 🔍 事实核查输出
```
example/judge_fact_result/
├── example_fact_judge_output.jsonl    # 核查结果
└── example_fact_scrape.out.jsonl      # 抓取结果
```

---

## ❓ 常见问题

<details>
<summary><strong>🌐 无法抓取网页内容？</strong></summary>

- ✅ 确认已设置 `FIRECRAWL_KEY` 或 `JINA_API_KEY`
- 🔄 尝试切换 `--provider` (firecrawl/jina)
- ⚡ 某些站点可能有访问限制，建议降低并发

</details>

<details>
<summary><strong>🤖 大模型返回解析失败？</strong></summary>

- 🛠️ 代码已使用 `json_repair` 做鲁棒解析
- 🔄 内置重试策略，失败时会记录日志并跳过
- 📝 检查日志文件 `./exp/judge.txt` 获取详细错误信息

</details>

<details>
<summary><strong>📊 重复性对数为 0？</strong></summary>

- 📋 确保报告存在以 `## ` 开头的一级标题
- 📏 适当增大报告长度（建议 > 200 字符）

</details>

---

## 📄 许可证


**本项目采用 [MIT 协议](LICENSE) 开源**

