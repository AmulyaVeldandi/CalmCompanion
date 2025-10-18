FROM node:20-alpine

WORKDIR /app

RUN npm install --global live-server

COPY voice_pwa /app

EXPOSE 8080

CMD ["live-server", "--host=0.0.0.0", "--port=8080", "--no-browser", "--wait=200"]
