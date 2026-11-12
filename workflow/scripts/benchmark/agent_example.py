# Test the agent on ONE question. For ALL questions, use agent.py.
#
# Run from the repo folder:
#   pixi run agent-example Q014            without skills
#   pixi run agent-example Q014 --skills   with all skills in skills/
#   pixi run agent-example Q014 --dry-run  only show the prompt (no agent, no Ollama needed)
# Replace Q014 with any question ID (Q001-Q100).
#
# Next step, once this works: all questions (agent.py)
#   pixi run agent                         without skills
#   pixi run agent --skills                with all skills in skills/
#
# Needs: nothing extra. Ollama is started and the model downloaded automatically if needed.
#        The agent downloads the PSets it needs from ORCESTRA itself.
# Saves:
#   data/results/benchmark/agent/example/Q014_<model>.txt   the answer (+ "_skills" if used)
#   logs/benchmark/example/Q014_<model>.log                 the agent's thinking: every step, code and output
#                                                           (written live; last line says how the run ended)

import csv
import datetime
import os
import sys
from pathlib import Path

from biomni.agent import A1
from biomni.config import default_config
from ollama_fix import fix_agent   # fixes empty replies + small context, see ollama_fix.py
from live_log import run_with_live_log   # writes each step to the log right away


# Step 1: read the question ID (e.g. Q014) and check if --skills was added
qids = [arg for arg in sys.argv[1:] if arg.startswith("Q")]
if not qids:
    sys.exit("Give a question ID, e.g.:  pixi run agent-example Q014")
qid = qids[0]
use_skills = "--skills" in sys.argv


# Step 2: look up the question text for Q014 in the questions file
# Q014 = "Which five drugs is PANC-1 most sensitive to in CTRPv2?"
questions = list(csv.DictReader(open("metadata/benchmark_questions.csv")))
question = [q["question"] for q in questions if q["qid"] == qid][0]


# Step 3: put Q014 and its question into the prompt template
prompt = Path("metadata/benchmark_prompt_template.txt").read_text()
prompt = prompt.replace("{qid}", qid).replace("{question}", question)


# Step 4: if --skills was added, put all skills from skills/ before the question
skill_files = sorted(Path("skills").glob("*/SKILL.md"))
if use_skills:
    skills_text = "You have these skills. Use them when answering.\n"
    skills_text += "Their reference files are in the same folders; read them with code when needed.\n"
    for skill_file in skill_files:
        skills_text += f"\n===== SKILL: {skill_file} =====\n\n" + skill_file.read_text()
    prompt = skills_text + "\n\n===== QUESTION =====\n\n" + prompt

print(prompt)   # show what the agent will get

# with --dry-run: stop here (check the prompt without starting the agent, no Ollama needed)
if "--dry-run" in sys.argv:
    sys.exit("\nDry run: this is the prompt the agent would get. Agent not started.")


# Step 5: start the agent (Biomni with our local model in Ollama)
model = os.environ.get("AGENT_MODEL", "qwen3:8b")   # set in pixi.toml
default_config.llm = model
default_config.source = "Ollama"

# make sure Ollama is running; if not, start it ourselves in the background
import subprocess
import time
import ollama
try:
    ollama.list()
except Exception:
    print("\nOllama is not running, starting it ...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):                           # wait up to 30 s until it answers
        time.sleep(1)
        try:
            ollama.list()
            break
        except Exception:
            pass
    else:
        sys.exit("Could not start Ollama. Try it yourself in another terminal:  pixi run ollama serve")

# make sure the model is downloaded (first time on this computer: download it)
models_in_ollama = [m.model for m in ollama.list().models]
if model not in models_in_ollama:
    print(f"\nModel {model} is not downloaded yet. Downloading it now (only once, can take a while) ...")
    ollama.pull(model)

agent = A1(path="./data", llm=model, source="Ollama", expected_data_lake_files=[])
agent = fix_agent(agent, model)


# Step 6: names and header for the saved files
# file name = question + model (+ skills), e.g. Q014_qwen3-8b_skills
name = qid + "_" + model.replace(":", "-") + ("_skills" if use_skills else "")

header = (
    "QUESTION ID: " + qid + "\n"
    + "QUESTION: " + question + "\n"
    + "MODEL: " + model + "\n"
    + "SKILLS: " + (", ".join(str(f) for f in skill_files) if use_skills else "none") + "\n"
    + "DATE: " + datetime.datetime.now().isoformat(timespec="seconds") + "\n"
)
log_file = Path("logs/benchmark/example") / (name + ".log")
print("Log (written live, step by step):", log_file)


# Step 7: ask the agent Q014; every step goes into the log right away
answer = run_with_live_log(agent, prompt, log_file, header)


# Step 8: save the answer -> data/results/
result_folder = Path("data/results/benchmark/agent/example")
result_folder.mkdir(parents=True, exist_ok=True)
(result_folder / (name + ".txt")).write_text(header + "\nPROMPT:\n" + prompt + "\n\nANSWER:\n" + str(answer))

print("Answer saved:", result_folder / (name + ".txt"))
print("Log saved:   ", log_file)
