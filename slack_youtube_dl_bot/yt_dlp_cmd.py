from typing import Final

_DEFAULT_OUTPUT_TEMPLATE: Final[str] = (
    "/out/%(extractor)s/%(channel)s - %(channel_id)s/"
    "%(playlist)s - %(playlist_id)s/"
    "%(title)s - %(id)s.%(ext)s"
)


def build_yt_dlp_cmd(
    *, url: str, output_template: str = _DEFAULT_OUTPUT_TEMPLATE
) -> tuple[str, ...]:
    return (
        "python",
        "-m",
        "yt_dlp",
        "-o",
        output_template,
        "--no-progress",
        url,
    )
