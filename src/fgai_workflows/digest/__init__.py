"""Morning digest: parallel sub-agents for news + calendar."""

from datetime import datetime
from typing import Dict, List
import openclaw


class MorningDigest:
    """
    Orchestrates parallel sub-agents to gather information and formats a morning digest.

    Configuration via environment variables:
    - FGAI_TIMEZONE: default Asia/Shanghai
    - FGAI_CALENDAR_ID: default 'primary'
    - FGAI_NEWS_COUNT: default 3
    """

    def __init__(self, tz: str = "Asia/Shanghai"):
        self.tz = tz

    def run(self) -> Dict[str, str]:
        """Spawn sub-agents in parallel, collect and combine results."""
        # 1. News agent
        news_task = f"Summarize top {self.news_count} AI headlines from the past 24 hours with source links. Plain text."
        news_sess = openclaw.sessions_spawn(
            task=news_task,
            runtime="subagent",
            mode="run",
            timeoutSeconds=120,
            label="digest-news"
        )
        # 2. Calendar agent
        cal_task = f"List today's events in {self.tz} with times, summaries, and Meet links. Note conflicts. Plain text."
        cal_sess = openclaw.sessions_spawn(
            task=cal_task,
            runtime="subagent",
            mode="run",
            timeoutSeconds=120,
            label="digest-calendar"
        )

        # 3. Wait for both (in a real implementation we'd poll or use events)
        # For now, simple blocking wait (placeholder)
        news_result = self._wait_result(news_sess.sessionKey)
        cal_result = self._wait_result(cal_sess.sessionKey)

        # 4. Combine
        today = datetime.now().astimezone().__str__()[:19]
        digest = f"Morning Digest — {today}\n\n"
        digest += "📰 News\n" + ("-"*40) + "\n" + news_result + "\n\n"
        digest += "📅 Calendar\n" + ("-"*40) + "\n" + cal_result + "\n"
        return {"text": digest}

    def _wait_result(self, session_key: str) -> str:
        """Blocking wait; replace with event-driven collection in production."""
        # This is a placeholder that polls in a real scenario
        import time
        for _ in range(60):
            status = openclaw.sessions_history(sessionKey=session_key, limit=1)
            if status.messages:
                return status.messages[-1].content
            time.sleep(2)
        return "[timeout]"


def main() -> None:
    """CLI entry point for manual testing."""
    digest = MorningDigest()
    out = digest.run()
    print(out["text"])


if __name__ == "__main__":
    main()