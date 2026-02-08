export const baseURL =
  process.env.BASE_URL ||
  (process.env.NODE_ENV === "development" ? "http://localhost:3000" : "");
