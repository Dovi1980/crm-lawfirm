FROM node:18-alpine

WORKDIR /app

COPY package.json .

RUN npm install

COPY . .

EXPOSE 3000

# Set environment variables for Vite dev server binding
ENV VITE_PORT=3000
ENV HOST=0.0.0.0

CMD ["npm", "run", "dev"]
