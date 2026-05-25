const { execSync } = require("child_process");
const path = require("path");

const backendDir = path.join(__dirname, "backend");

console.log("Installing Python dependencies...");
execSync("pip install --no-cache-dir .", { cwd: backendDir, stdio: "inherit" });

console.log("Starting PyFlow Blog API...");
execSync("uvicorn app.main:app --host 0.0.0.0 --port 3001", {
  cwd: backendDir,
  stdio: "inherit",
});
