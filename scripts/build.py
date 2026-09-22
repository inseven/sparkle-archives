#!/usr/bin/env python3

import argparse
import logging
import os
import shutil
import sys
import time
import urllib.parse

import requests

import xml.etree.ElementTree as ET

ACCEPT_JSON = "application/vnd.github+json"
ACCEPT_STREAM = "application/octet-stream"

APPCAST_TEMPLATE = """<?xml version="1.0" standalone="yes"?>
<rss xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle" version="2.0">
    <channel>
        <title>Reconnect</title>
    </channel>
</rss>
"""


ET.register_namespace('sparkle', 'http://www.andymatuschak.org/xml-namespaces/sparkle')


def spinning_cursor():
    while True:
        for cursor in ["zzzz", "Zzzz", "zZzz", "zzZz", "zzzZ"]:
            yield cursor


class Sleeper:

    def __init__(self):
        self.polling_duration = 0.2
        self.duration = 0
        self.did_sleep = False
        self.spinner = spinning_cursor()
        self.is_interactive = sys.stdout.isatty()

    def sleep(self, duration):
        self.did_sleep = True
        self.duration = duration
        while self.duration > 0:
            if self.is_interactive:
                print("\r", end="")
                print(next(self.spinner), end="")
            time.sleep(self.polling_duration)
            self.duration = self.duration - self.polling_duration

    def finalize(self):
        if self.did_sleep and self.is_interactive:
            print("\r", end="")


def perform_with_backoff(fn, url, accept, *args, **kwargs):
    if "headers" not in kwargs:
        kwargs["headers"] = {}
    kwargs["headers"]["Accept"] = accept
    kwargs["headers"]["X-GitHub-Api-Version"] = "2022-11-28"
    if "GITHUB_TOKEN" in os.environ:
        kwargs["headers"]["Authorization"] = f"Bearer {os.environ["GITHUB_TOKEN"]}"
    kwargs["allow_redirects"] = True
    sleeper = Sleeper()
    duration = 8
    while True:
        logging.debug(f"GET {url}")
        try:
            response = fn(url, *args, **kwargs)
            if not response.status_code in [403, 429, 500, 502, 504]:
                break
        except http.client.RemoteDisconnected:
            pass
        did_wait = True
        sleeper.sleep(duration)
        duration = min(duration * 2, 60)
    response.raise_for_status()
    sleeper.finalize()
    return response


def generate_appcast(owner, repo, title, output_path):

    appcast = ET.fromstring(APPCAST_TEMPLATE)
    appcast_title = appcast.find(".//title")
    appcast_channel = appcast.find(".//channel")

    appcast_title.text = title

    response = perform_with_backoff(requests.get, f"https://api.github.com/repos/{owner}/{repo}/releases", ACCEPT_JSON)
    releases = response.json()
    if releases:
        for release in releases:
            if release['prerelease']:
                continue
            release_name = release['name']
            assets = {asset['name']: asset['browser_download_url'] for asset in release.get('assets', [])}
            if 'appcast.xml' in assets:
                print(f"{owner}/{repo} {release_name}")
                appcast_response = perform_with_backoff(requests.get, assets['appcast.xml'], ACCEPT_STREAM)
                appcast_response.raise_for_status()
                root = ET.fromstring(appcast_response.content)
                items = root.findall('.//item')
                for item in items:
                    enclosure = item.find('./enclosure')
                    url = enclosure.get('url')
                    asset_name = os.path.basename(urllib.parse.urlparse(url).path)
                    enclosure.set('url', assets[asset_name])
                    appcast_channel.append(item)

    root = ET.ElementTree(appcast)
    with open(output_path, 'w') as fh:
        fh.write('<?xml version="1.0" standalone="yes"?>\n')
        root.write(fh, encoding='unicode', xml_declaration=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output')
    options = parser.parse_args()

    # Clean up previous builds if necessary.
    output_path = os.path.abspath(options.output)
    if os.path.exists(output_path):
        shutil.rmtree(output_path)

    # Create the output path.
    os.makedirs(output_path)

    repositories = [
        ('inseven', 'fileaway', 'Fileaway'),
        ('inseven', 'folders', 'Folders'),
        ('inseven', 'incontext', 'InContext Helper'),
        ('inseven', 'overview', 'Overview'),
        ('inseven', 'reconnect', 'Reconnect'),
        ('inseven', 'symbolic', 'Symbolic'),
        ('inseven', 'taillight', 'TailLight'),
        ('inseven', 'thoughts', 'Thoughts'),
        ('inseven', 'tinyboard', 'TinyBoard'),
    ]

    for (owner, repo, title) in repositories:
        appcast_directory = os.path.join(output_path, owner, repo)
        os.makedirs(appcast_directory)
        generate_appcast(owner, repo, title, os.path.join(appcast_directory, 'appcast.xml'))


if __name__ == "__main__":
    main()
