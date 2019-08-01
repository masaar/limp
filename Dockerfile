FROM python:3.7

WORKDIR /usr/src/app

EXPOSE 8081

COPY . .

RUN python limpd.py --install-deps

CMD [ "python", "limpd.py" ]