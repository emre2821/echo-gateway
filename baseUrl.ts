const vercelUrl = process.env.VERCEL_URL;

export const baseURL =
  process.env.BASE_URL ||
  (process.env.NODE_ENV === "development"
    ? "http://localhost:3000"
    : vercelUrl
      ? `https://${vercelUrl}`
      : "http://localhost:3000");
