#!/usr/bin/env python3

import argparse
import os
import shutil
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

    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    response = requests.get(url)
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
        ('inseven', 'reconnect', 'Reconnect'),
        ('inseven', 'incontext', 'InContext Helper'),
    ]

    for (owner, repo, title) in repositories:
        appcast_directory = os.path.join(output_path, owner, repo)
        os.makedirs(appcast_directory)
        generate_appcast(owner, repo, title, os.path.join(appcast_directory, 'appcast.xml'))


if __name__ == "__main__":
    main()