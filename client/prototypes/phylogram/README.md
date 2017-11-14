To run:

1. cd to this directory

2. `mkdir data`

3. using your browser (UIUC SSO authentication complicates curl/wget), download four files from Box:

    * https://uofi.app.box.com/files/0/f/6347659961/1/f_51671216133 to data/myNewick1.nwk

    * https://uofi.app.box.com/files/0/f/6347659961/1/f_51671222165 to data/myNewick2.nwk

    * https://uofi.app.box.com/files/0/f/6347659961/1/f_51671229513 to data/myNewick3.nwk

    * https://uofi.app.box.com/files/0/f/6347659961/1/f_52986984597 to data/Abundance.csv

4. `python -m SimpleHTTPServer 8002`

5. open http://<hostname>:8002 in a browser
