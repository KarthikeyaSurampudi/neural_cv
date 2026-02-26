import asyncio
import argparse
from pathlib import Path

from database.engine import init_db
from services.analysis_service import process_analysis


async def main(jd_path: Path, resumes_path: Path, model: str = None):

    await init_db()

    jd_text = jd_path.read_text(encoding="utf-8")
    resume_files = list(resumes_path.glob("*"))

    await process_analysis(
        analysis_name="CLI_Run",
        jd_text=jd_text,
        resume_paths=resume_files,
        user_id=None,
        model=model
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jd", required=True)
    parser.add_argument("--resumes", required=True)
    parser.add_argument("--model", default=None)

    args = parser.parse_args()

    asyncio.run(
        main(
            jd_path=Path(args.jd),
            resumes_path=Path(args.resumes),
            model=args.model
        )
    )