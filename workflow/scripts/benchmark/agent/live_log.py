# Run the agent and write EVERY step to the log file as soon as it happens.
# So if the run stops early (Ctrl+C, an error, or too many steps) the log still shows
# everything up to that point, and the last line says why it stopped.
#
# Use:  answer = run_with_live_log(agent, prompt, log_file, header)

import datetime
import os
import traceback

MAX_STEPS = int(os.environ.get("AGENT_MAX_STEPS", "100"))   # stop endless loops


def run_with_live_log(agent, prompt, log_file, header):
    log_file.parent.mkdir(parents=True, exist_ok=True)
    answer = ""
    with open(log_file, "w") as log:
        log.write(header + "\nSTEPS:\n\n")
        log.flush()

        def end(reason):
            log.write(f"\n\n===== ENDED: {reason} ({datetime.datetime.now():%Y-%m-%d %H:%M:%S}) =====\n")
            log.flush()

        try:
            for n, step in enumerate(agent.go_stream(prompt), start=1):
                answer = step["output"]
                log.write(f"----- step {n} -----\n{answer}\n\n")
                log.flush()                     # write to disk now, not at the end
                if n >= MAX_STEPS:
                    end(f"stopped after {MAX_STEPS} steps (AGENT_MAX_STEPS)")
                    return "ERROR: too many steps\n" + answer
            end("finished normally")
            state = getattr(agent, "_conversation_state", None)
            if state:
                answer = state["messages"][-1].content
        except KeyboardInterrupt:
            end("stopped by user (Ctrl+C)")
            raise
        except Exception:
            log.write("\n" + traceback.format_exc())
            end("Python error (see above)")
            return "ERROR: see log\n" + answer
    return answer
