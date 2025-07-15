#!/usr/bin/env python3

import argparse
import os
import shutil
import time
import urllib.parse

import requests

import xml.etree.ElementTree as ET

ET.register_namespace('sparkle', 'http://www.andymatuschak.org/xml-namespaces/sparkle')


APPCAST_TEMPLATE = """<?xml version="1.0" standalone="yes"?>
<rss xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle" version="2.0">
    <channel>
        <title>Reconnect</title>
    </channel>
</rss>
"""


def generate_appcast(owner, repo, title, output_path):

    appcast = ET.fromstring(APPCAST_TEMPLATE)
    appcast_title = appcast.find(".//title")
    appcast_channel = appcast.find(".//channel")

    appcast_title.text = title

    # Default API headers.
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Use a GitHub token if it's present in the environment as this is likely to have fewer rate limits.
    if "GITHUB_TOKEN" in os.environ:
        headers["Authorization"] = f"Bearer {os.environ["GITHUB_TOKEN"]}"

    # Fetch the required data with an exponential backoff (max 5m) if we hit a 403 rate limit.
    attempt = 1
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            break
        elif response.status_code == 403:
            sleep_duration_s = min(300, 2 ** attempt)
            logging.info(f"Waiting {sleep_duration_s}s for GitHub API rate limits...")
            time.sleep(sleep_duration_s)
            attempt += 1
            continue
        else:
            response.raise_for_status()

    releases = response.json()
    if releases:
        for release in releases:
            if release['prerelease']:
                continue
            release_name = release['name']
            assets = {asset['name']: asset['browser_download_url'] for asset in release.get('assets', [])}
            if 'appcast.xml' in assets:
                print(f"{owner}/{repo} {release_name}")
                appcast_response = requests.get(assets['appcast.xml'])
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
        ('inseven', 'reconnect', 'Reconnect'),
        ('inseven', 'thoughts', 'Thoughts'),
    ]

    for (owner, repo, title) in repositories:
        appcast_directory = os.path.join(output_path, owner, repo)
        os.makedirs(appcast_directory)
        generate_appcast(owner, repo, title, os.path.join(appcast_directory, 'appcast.xml'))


if __name__ == "__main__":
    main()