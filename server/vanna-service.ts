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

    // Install the Python requirements if they don't exist
    if (!fs.existsSync(resolve(flaskPath, "venv"))) {
      console.log("Setting up Python environment for Flask...");
      const setupProcess = spawn("python", ["-m", "venv", "venv"], {
        cwd: flaskPath,
        shell: true,
      });

      setupProcess.on("close", (code) => {
        if (code !== 0) {
          console.error(`Failed to create virtual environment: ${code}`);
          return reject(new Error(`Failed to create virtual environment: ${code}`));
        }

        // Determine the pip command based on platform
        const pipCommand = process.platform === "win32" ? ".\\venv\\Scripts\\pip" : "./venv/bin/pip";
        
        const installProcess = spawn(pipCommand, ["install", "-r", "requirements.txt"], {
          cwd: flaskPath,
          shell: true,
        });

        installProcess.stdout.on("data", (data) => {
          console.log(`pip stdout: ${data}`);
        });

        installProcess.stderr.on("data", (data) => {
          console.error(`pip stderr: ${data}`);
        });

        installProcess.on("close", (code) => {
          if (code !== 0) {
            console.error(`Failed to install requirements: ${code}`);
            return reject(new Error(`Failed to install requirements: ${code}`));
          }
          
          startFlaskApp()
            .then(resolve)
            .catch(reject);
        });
      });
    } else {
      startFlaskApp()
        .then(resolve)
        .catch(reject);
    }
  });
}

/**
 * Start the Flask application
 */
function startFlaskApp() {
  return new Promise((resolve, reject) => {
    // Determine the Python command based on platform
    const pythonCommand = process.platform === "win32" ? ".\\venv\\Scripts\\python" : "./venv/bin/python";
    
    console.log("Starting Flask service...");
    flaskProcess = spawn(pythonCommand, [flaskAppPath], {
      cwd: flaskPath,
      shell: true,
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

    // Timeout if Flask doesn't start in 10 seconds
    setTimeout(() => {
      if (flaskProcess) {
        resolve(true);
      } else {
        reject(new Error("Flask service failed to start in time"));
      }
    }, 10000);
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
