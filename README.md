# weewx-windy
Uploader for WeeWX weather data to temperatur.nu

Copyright 2021 Konrad Skeri Ekblad

## Installation instructions:

1. Download  
`wget -O weewx-temperaturnu.zip https://github.com/LapplandsCohan/weewx-temperaturnu/archive/master.zip`
2. Run the extension installer  
`wee_extension --install weewx-temperaturnu.zip`
3. Modify weewx.conf  
```
    [StdRESTful]
        [[TemperaturNu]]
            hash = TEMPERATURNU_HASH
```
4. Restart weewx  
`sudo systemctl restart weewx`
