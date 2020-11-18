#!/bin/sh
fc-cache -f
soffice "--accept=socket,host=0,port=2002;urp;" --nologo --headless --norestore --nofirststartwizard &
exec gunicorn -k uvicorn.workers.UvicornWorker -c uvicorn_conf.py  doxgen_libreoffice_worker.server:main
