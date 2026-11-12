# Ask the agent ALL benchmark questions. To test one question first, use agent_example.py.
# The agent uses the PSets already in data/procdata/psets/ (no downloading),
# see metadata/benchmark_prompt_template_local.txt.
#
#   pixi run agent              without skills
#   pixi run agent --skills     with all skills in skills/
#
# Saves (new folder each run, e.g. 2026-11-12_1430_qwen3-8b_skills):
#   data/results/benchmark/agent/<run>/   Q001.txt ... (answers) + answers.csv (all answers)
#   logs/benchmark/<run>/                 Q001.log ... (the agent's thinking, written live step by step)

import csv
import datetime
import os
import subprocess
import sys
import time
from pathlib import Path

import ollama
from biomni.agent import A1
from biomni.config import default_config
from live_log import run_with_live_log   # writes each step to the log right away

# settings
use_skills = "--skills" in sys.argv
model = os.environ.get("AGENT_MODEL", "qwen3:8b")   # set in pixi.toml
default_config.llm = model
default_config.source = "Ollama"

# start Ollama if needed, and get the model (downloads only the first time)
try:
    ollama.list()
except Exception:
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)
ollama.pull(model)

# questions, prompt template, and skills
questions = list(csv.DictReader(open("metadata/benchmark_questions.csv")))
template = Path("metadata/benchmark_prompt_template_local.txt").read_text()
skills = ""
if use_skills:
    for skill_file in sorted(Path("skills").glob("*/SKILL.md")):
        skills += f"===== SKILL: {skill_file} =====\n{skill_file.read_text()}\n\n"
    skills += "===== QUESTION =====\n"

# folders for this run
run = datetime.datetime.now().strftime("%Y-%m-%d_%H%M") + "_" + model.replace(":", "-") + ("_skills" if use_skills else "")
results = Path("data/results/benchmark/agent") / run
logs = Path("logs/benchmark") / run
results.mkdir(parents=True)
logs.mkdir(parents=True)

# ask each question to a new agent
answers = [["qid", "answer", "method"]]
for q in questions:
    qid = q["qid"]
    print(qid, "...")
    prompt = skills + template.replace("{qid}", qid).replace("{question}", q["question"])

    # every step goes into logs/<run>/Q001.log right away; errors are noted there and we go on
    try:
        agent = A1(path="./data", llm=model, source="Ollama", expected_data_lake_files=[])
        answer = run_with_live_log(agent, prompt, logs / f"{qid}.log", f"{qid}: {q['question']}\n")
    except Exception as error:   # e.g. the agent could not even start
        answer = f"ERROR: {error}"

    # save the answer
    (results / f"{qid}.txt").write_text(f"{qid}: {q['question']}\n\n{answer}")

    # the agent's last line should be "Q014 | answer | method"
    line = [l for l in str(answer).replace("<solution>", "").splitlines() if l.strip().startswith(qid + " |")]
    parts = line[-1].split("|") if line else [qid, "", ""]
    answers.append([qid, parts[1].strip(), parts[2].replace("</solution>", "").strip() if len(parts) > 2 else ""])

    with open(results / "answers.csv", "w", newline="") as f:   # save after every question
        csv.writer(f).writerows(answers)

print("Done. Answers:", results, " Logs:", logs)
