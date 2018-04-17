#!/usr/bin/python3

import pytest
import amulet
# import requests
# import time


@pytest.fixture(scope="module")
def deploy():
    deploy = amulet.Deployment(series='artful')
    deploy.add('sftp-server')
    deploy.expose('sftp-server')
    deploy.configure('sftp-server', {'sftp-config': ('user1,/tmp:system-tmp;'
                                                     'user2,/tmp')})
    deploy.setup(timeout=1000)
    return deploy


@pytest.fixture(scope="module")
def sftp(deploy):
    return deploy.sentry['sftp-server'][0]


class TestHaproxy():

    def test_deploy(self, deploy):
        try:
            deploy.sentry.wait(timeout=1500)
        except amulet.TimeoutError:
            raise

    # def test_web_frontend(self, deploy, duplicati):
    #     page = requests.get('http://{}:{}'.format(duplicati.info['public-address'], 8200))
    #     assert page.status_code == 200
    #     print(page)

    # def test_reverseproxy(self, deploy, duplicati, haproxy):
    #     page = requests.get('http://{}:{}'.format(duplicati.info['public-address'], 8200))
    #     assert page.status_code == 200
    #     # page = requests.get('https://{}:{}/duplicati'.format(haproxy.info['public-address'], 443))
    #     # assert page.status_code == 503
    #     deploy.relate('duplicati:reverseproxy', 'haproxy:reverseproxy')
    #     time.sleep(15)
    #     page = requests.get('http://{}:{}/duplicati'.format(haproxy.info['public-address'], 80))
    #     assert page.status_code == 200

    #     # test we can access over http
    #     # page = requests.get('http://{}'.format(self.unit.info['public-address']))
    #     # self.assertEqual(page.status_code, 200)
    #     # Now you can use self.d.sentry[SERVICE][UNIT] to address each of the units and perform
    #     # more in-depth steps. Each self.d.sentry[SERVICE][UNIT] has the following methods:
    #     # - .info - An array of the information of that unit from Juju
    #     # - .file(PATH) - Get the details of a file on that unit
    #     # - .file_contents(PATH) - Get plain text output of PATH file from that unit
    #     # - .directory(PATH) - Get details of directory
    #     # - .directory_contents(PATH) - List files and folders in PATH on that unit
    #     # - .relation(relation, service:rel) - Get relation data from return service
