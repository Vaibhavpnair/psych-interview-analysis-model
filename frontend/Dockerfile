FROM node:18-alpine

WORKDIR /app

COPY package.json .
# Note: In a real prod build we'd use 'npm ci' and build static assets.
# For this dev prototype, we keep it simple.
RUN npm install

COPY . .

CMD ["npm", "run", "dev", "--", "--host"]
