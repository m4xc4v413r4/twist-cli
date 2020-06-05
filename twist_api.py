import requests
from cryptojs_aes_port import decrypt
import subprocess
import os
import code
import sys
from tempfile import TemporaryFile
from tqdm import tqdm

API_KEY = "1rj2vRtegS8Y60B3w3qNZm5T2Q0TN2NR"
AES_KEY = b"LXgIVP&PorO68Rq7dTx8N^lP!Fa5sGJ^*XK"

def api_request(url):
    r = requests.get(
        f"https://twist.moe/api{url}",
        headers = {
            "x-access-token": API_KEY
        }
    )

    r.raise_for_status()
    return r.json()

def get_show_to_slug():
    shows_json = api_request("/anime")
    shows_jp = {
        i["title"]: i["slug"]["slug"] for i in shows_json
    }

    return shows_jp

def get_title_translations():
    shows_json = api_request("/anime")
    translation = {
        i["title"]: i["alt_title"] for i in shows_json
    }

    for title in translation:
        if translation[title] is None:
            translation[title] = title

    translation = {
        translation[x]: x for x in translation
    }

    return translation

def get_source(slug, ep_number):
    sources = api_request(f"/anime/{slug}/sources")
    encrypted_url = list(filter(lambda ep: ep["number"] == ep_number, sources))[0]["source"]
    url = decrypt(AES_KEY, encrypted_url)
    return f"https://twistcdn.bunny.sh{url}"

def get_num_episodes(slug):
    sources = api_request(f"/anime/{slug}/sources")
    return len(sources)

def download(slug, ep, out=None):
    out = out if out else f"{slug}-{ep}.mp4"
    url = get_source(slug, ep)

    r = requests.get(
        url,
        headers={
            "Referer": "https://twist.moe/"
        },
        stream=True
    )
    r.raise_for_status()
    
    with open(out, "wb") as f:
        try:
            for chunk in tqdm(r.iter_content(), total=int(r.headers["Content-Length"]), unit="B", unit_scale=True):
                f.write(chunk)
        except KeyboardInterrupt:
            return True
    

def stream(slug, ep_number):
    killed_by_ctrl_c = False
    url = get_source(slug, ep_number)

    r = requests.get(
        url,
        headers={
            "Referer": "https://twist.moe/"
        },
        stream=True
    )
    r.raise_for_status()
    p = subprocess.Popen(["mplayer", "-really-quiet", "-msglevel", "all=-1", "-cache", "32768", "-"], stdin=subprocess.PIPE, stderr=TemporaryFile())

    try:
        for chunk in r.iter_content(32768):
            p.stdin.write(chunk)
    except TypeError:
        killed_by_ctrl_c = True
    except KeyboardInterrupt:
        killed_by_ctrl_c = True
    except BrokenPipeError:
        pass
    
    p.kill()
    
    return killed_by_ctrl_c

if __name__ == "__main__":
    # download("kobayashi-san-chi-no-maid-dragon", [1])
    stream("kobayashi-san-chi-no-maid-dragon", 6)