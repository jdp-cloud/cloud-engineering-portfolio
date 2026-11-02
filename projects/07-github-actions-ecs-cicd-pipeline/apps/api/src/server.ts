import { createApp } from "./app.js";
import { readEnv } from "./env.js";

const port = Number(readEnv("PORT", "3001"));
const app = createApp();

app.listen(port, "0.0.0.0", () => {
  console.log(`api listening on ${port}`);
});
