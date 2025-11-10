FROM node:20-alpine

WORKDIR /app

ENV VITE_API_URL=http://backend:8000/iss/now

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
