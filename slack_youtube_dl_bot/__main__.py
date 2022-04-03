import os

import youtube_dl
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.environ["SLACK_BOT_TOKEN"])


@app.message("")
def echo(message, say):
    # TODO: text の mrkdwn 形式から plain_text 形式への変換をちゃんとやる
    # NOTE: https://api.slack.com/reference/surfaces/formatting
    text = message["text"].strip("<>")

    def hook(d):
        if d["status"] == "finished":
            if "_elapsed_str" in d:
                say(
                    f"{d['filename']} is successfully downloaded in {d['_elapsed_str']}"
                )
            else:
                say(f"{d['filename']} has already been downloaded")
        if d["status"] == "error":
            say(f"ERROR: {d=}")

    ydl_opts = {
        "ignoreerrors": True,
        "outtmpl": "/out/%(extractor)s/%(title)s-%(id)s.%(ext)s",
        "progress_hooks": [hook],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        say(f"start downloading {text}")

        try:
            ydl.download([text])
        except youtube_dl.utils.DownloadError as e:
            say(str(e))


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
