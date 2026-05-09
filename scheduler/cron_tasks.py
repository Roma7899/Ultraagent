# ============================================================
# UltraAgent — scheduler/cron_tasks.py
# كل الـ scheduled jobs في مكان واحد
# ============================================================

import sys
import structlog
log = structlog.get_logger()


def run_dreaming():
    """Dreaming Mode — بيتشغل كل يوم 02:00 UTC."""
    from memory.long_term import long_term
    log.info("cron_dreaming_start")
    count = long_term.consolidate()
    log.info("cron_dreaming_done", consolidated=count)


def run_self_improve():
    """Self-Improvement — بيتشغل كل أحد 03:00 UTC."""
    from advanced.self_improvement import self_improvement
    log.info("cron_self_improve_start")
    result = self_improvement.run_weekly()
    log.info("cron_self_improve_done", result=result)


def run_predict():
    """Predict-Preload — بيتشغل كل 6 ساعات."""
    from advanced.reputation_gossip import predict_preload
    log.info("cron_predict_start")
    result = predict_preload.run()
    log.info("cron_predict_done", result=result)


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    jobs = {
        "dreaming": run_dreaming,
        "self_improve": run_self_improve,
        "predict": run_predict,
    }
    if command in jobs:
        jobs[command]()
    else:
        print(f"Unknown command: {command}. Available: {list(jobs.keys())}")
