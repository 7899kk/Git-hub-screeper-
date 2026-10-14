import argparse
import logging
import os

from apscheduler.schedulers.blocking import BlockingScheduler

from .collectors import enqueue_due, process_jobs
from .providers import LicensedFeed, ingest
from .storage import database


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    _, sessions = database()

    def refresh():
        try:
            logging.info("Imported %d new observations", ingest(sessions, LicensedFeed()))
        except Exception:
            # Preserve previous observations; never substitute fabricated data.
            logging.exception("Authorized feed refresh failed")
            if args.once:
                raise

    logging.basicConfig(level=logging.INFO)
    refresh()
    enqueue_due(sessions)
    process_jobs(sessions)
    if not args.once:
        scheduler = BlockingScheduler(timezone="UTC")
        scheduler.add_job(
            refresh,
            "interval",
            seconds=int(os.getenv("PULSE_REFRESH_SECONDS", "21600")),
            max_instances=1,
            coalesce=True,
        )
        scheduler.add_job(
            lambda: process_jobs(sessions), "interval", seconds=5, max_instances=1, coalesce=True
        )
        scheduler.add_job(
            lambda: enqueue_due(sessions), "interval", seconds=300, max_instances=1, coalesce=True
        )
        scheduler.start()


if __name__ == "__main__":
    main()
