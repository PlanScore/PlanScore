#!/bin/bash -ex
perl -pi -e 's/font-family=".SF NS Text"//' design/Upload-Map.svg
java -jar /usr/local/share/svg-buddy-runner.jar design/Upload-Map.svg design/Upload-Map-with-font.svg
svgo design/Upload-Map-with-font.svg -o planscore/website/static/supported-states.svg
