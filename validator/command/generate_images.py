# -*- coding: utf-8 -*-
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

"""Helper tool to generate valid test images in docker format"""

import logging
import sys
import os
from docker import Client as DockerClient
from oslo_config import cfg
import re

CONF = cfg.CONF
CONF.register_opt(cfg.StrOpt('config_dir', default="../../etc/validator"))
CONF.register_opt(cfg.StrOpt('url', default="tcp://127.0.0.1:2375"), group="clients_docker")
LOG = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)


def dock_image(df):
    """generate docker image"""
    status = True
    dc = DockerClient(base_url=CONF.clients_docker.url)
    dc.info()
    with open(df) as dockerfile:
        tag = re.findall("(?im)^# tag: (.*)$", dockerfile.read())[0].strip()
        LOG.debug("Generating %s from %s" % (tag, df))
        resp = dc.build(
            fileobj=dockerfile,
            rm=True,
            tag=tag
        )
    for l in resp:
        if "error" in l.lower():
            status = False
        LOG.debug(l)
    return status


def dock_images(wp):
    # find dockerfiles in config dir
    LOG.info("Generating Images...")
    for df in os.listdir(wp):
        if df.endswith(".dockerfile"):
            LOG.info("Generating Image for %s" % df)
            dock_image(df)


def main():
    """
    Generates a Docker Image of test environments based on a local dockerfile.
    """
    # inject config files dir to syspath
    wp = os.path.abspath(CONF.config_dir)
    sys.path.insert(0, wp)
    os.chdir(wp)
    dock_images(wp)

if __name__ == '__main__':
    # include arg --config-dir={configpath}
    main()
