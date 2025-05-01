import { spawn } from "child_process";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import fs from "fs";

// Get current directory
const __dirname = dirname(fileURLToPath(import.meta.url));
const flaskPath = resolve(__dirname, "./flask");
const flaskAppPath = resolve(flaskPath, "app.py");

// Check if Flask directory exists, create if not
if (!fs.existsSync(flaskPath)) {
  fs.mkdirSync(flaskPath, { recursive: true });
}

// Store the running Flask process
let flaskProcess: any = null;

/**
 * Start the Flask service that runs Vanna AI
 */
export async function startFlaskService() {
  return new Promise((resolve, reject) => {
    if (flaskProcess) {
      console.log("Flask service is already running");
      return resolve(true);
    }

    console.log("Setting up Python environment for Flask...");
    
    // Since we're running in Replit, we can directly use python3
    startFlaskApp()
      .then(resolve)
      .catch(reject);
  });
}

/**
 * Start the Flask application
 */
function startFlaskApp() {
  return new Promise((resolve, reject) => {
    // Use the system Python directly
    const pythonCommand = "python3";
    
    console.log("Starting Flask service...");
    // Set environment variables for the Flask app
    const env = { 
      ...process.env,
      FLASK_APP: flaskAppPath,
      FLASK_ENV: "development",
      FLASK_DEBUG: "1",
      // Enable built-in VANNA AI model without requiring an API key
      VANNA_MODEL: "demo"
    };
    
    flaskProcess = spawn(pythonCommand, [flaskAppPath], {
      cwd: flaskPath,
      shell: true,
      env
    });

    flaskProcess.stdout.on("data", (data) => {
      const output = data.toString();
      console.log(`Flask: ${output}`);
      
      // Check if the server is running
      if (output.includes("Running on http://")) {
        console.log("Flask service is now running");
        resolve(true);
      }
    });

    flaskProcess.stderr.on("data", (data) => {
      console.error(`Flask error: ${data}`);
    });

    flaskProcess.on("close", (code) => {
      console.log(`Flask process exited with code ${code}`);
      flaskProcess = null;
      
      if (code !== 0 && code !== null) {
        reject(new Error(`Flask process exited with code ${code}`));
      }
    });

    // Resolve after a short timeout to continue with server startup
    // even if we don't see the "Running on http://" message
    setTimeout(() => {
      console.log("Flask service assumed to be running (timeout)");
      resolve(true);
    }, 5000);
  });
}

/**
 * Stop the Flask service
 */
export function stopFlaskService() {
  return new Promise<void>((resolve) => {
    if (flaskProcess) {
      console.log("Stopping Flask service...");
      
      if (process.platform === "win32") {
        // Windows needs taskkill to kill the process tree
        spawn("taskkill", ["/pid", flaskProcess.pid, "/f", "/t"], { shell: true });
      } else {
        // Unix can just kill the process group
        flaskProcess.kill("SIGINT");
      }
      
      flaskProcess = null;
    }
    
    resolve();
  });
}

/**
 * Ensure Flask service is running
 */
export async function ensureFlaskService() {
  if (!flaskProcess) {
    await startFlaskService();
  }
  return true;
}
