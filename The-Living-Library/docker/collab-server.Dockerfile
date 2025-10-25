FROM node:20-alpine

WORKDIR /app

COPY collab-server/package*.json ./

RUN npm ci

COPY collab-server ./

RUN npm run build

EXPOSE 8080

CMD ["node", "dist/server.js"]
