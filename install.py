# installer for WeeWX Temperatur.nu uploader
# Copyright 2021 Konrad Skeri Ekblad

from weecfg.extension import ExtensionInstaller

def loader():
    return TemperaturNuInstaller()

class TemperaturNuInstaller(ExtensionInstaller):
    def __init__(self):
        super(TemperaturNuInstaller, self).__init__(
            version="0.1",
            name='temperaturnu',
            description='Upload weather data to temperatur.nu.',
            author="Konrad Skeri Ekblad",
            author_email="mwall@users.sourceforge.net",
            restful_services='user.temperaturnu.TemperaturNu',
            config={
                'StdRESTful': {
                    'TemperaturNu': {
                        'hash': 'TEMPERATURNU_HASH',
            files=[('bin/user', ['bin/user/temperaturnu.py'])]
            )
