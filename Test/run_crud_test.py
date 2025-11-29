import subprocess
import time
import random
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from user_llm_client import UserLLMClient

# Config
# Assuming this script is in ApartmentManager/Test
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(TEST_DIR, "../backend"))
FRONTEND_DIR = os.path.abspath(os.path.join(TEST_DIR, "../frontend"))
HOST = "127.0.0.1"
PORT_BACKEND = 5003
PORT_FRONTEND = 8000

def start_backend():
    print("Starting Backend...")
    env = os.environ.copy()
    # Add project root to PYTHONPATH so imports work
    # We need the parent of ApartmentManager to be in PYTHONPATH
    # TEST_DIR is .../ApartmentManager/Test
    # ../.. is .../ApartmentManager/.. -> .../AI_project (or whatever contains ApartmentManager)
    project_root = os.path.abspath(os.path.join(TEST_DIR, "../.."))
    env["PYTHONPATH"] = project_root
    if "PYTHONPATH" in os.environ:
        env["PYTHONPATH"] += os.pathsep + os.environ["PYTHONPATH"]
        
    cmd = [sys.executable, "main.py"]
    process = subprocess.Popen(cmd, cwd=BACKEND_DIR, env=env)
    return process

def start_frontend():
    print("Starting Frontend...")
    # Using python's built-in http.server
    cmd = [sys.executable, "-m", "http.server", str(PORT_FRONTEND)]
    process = subprocess.Popen(cmd, cwd=FRONTEND_DIR)
    return process

def run_test():
    backend_proc = None
    frontend_proc = None
    driver = None
    
    try:
        backend_proc = start_backend()
        frontend_proc = start_frontend()
        
        print("Waiting for servers to start...")
        time.sleep(10) # Give plenty of time for backend to initialize
        
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless") # Commented out to show the browser as requested
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        user_llm = UserLLMClient()
        
        url = f"http://{HOST}:{PORT_FRONTEND}"
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for chat input
        wait = WebDriverWait(driver, 20)
        textarea = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".chat-input textarea")))
        
        tasks = [
            {
                "goal": "Create a new person named 'Automated Tester' with email 'auto@test.com' and phone '555-0199'.",
                "verify": "Automated Tester"
            },
            {
                "goal": "Show all persons.",
                "verify": "Automated Tester"
            },
            {
                "goal": "Update the person 'Automated Tester' to have phone number '999-9999'.",
                "verify": "999-9999"
            },
            {
                "goal": "Delete the person 'Automated Tester'.",
                "verify": "deleted" 
            }
        ]
        
        for i, task in enumerate(tasks):
            goal = task["goal"]
            verification = task["verify"]
            print(f"\n--- Starting Task {i+1}: {goal} ---")
            
            user_llm.reset_history()
            task_completed = False
            
            # Limit turns to prevent infinite loops
            for turn in range(10):
                # Get last system message
                msgs = driver.find_elements(By.CSS_SELECTOR, ".msg")
                last_system_response = None
                if msgs:
                    last_msg = msgs[-1]
                    # Check if it's from assistant
                    classes = last_msg.get_attribute("class")
                    if "assistant" in classes:
                         try:
                             content_el = last_msg.find_element(By.CSS_SELECTOR, ".msg-content")
                             last_system_response = content_el.text
                         except:
                             pass
                
                print(f"System Response: {last_system_response}")
                
                # Check for rate limit in system response
                if last_system_response and ("429" in last_system_response or "quota" in last_system_response.lower()):
                    print("⚠️ Rate limit detected. Waiting 40 seconds...")
                    time.sleep(40)
                    continue

                # Generate user input
                user_input = user_llm.generate_next_message(goal, last_system_response)
                
                if user_input == "WAIT":
                    print("User LLM requested wait (likely error). Waiting 10 seconds...")
                    time.sleep(10)
                    continue

                if user_input == "DONE":
                    print(f"User LLM indicates task is DONE.")
                    task_completed = True
                    break
                
                print(f"User Input: {user_input}")
                
                # Simulate thinking/typing time (natural behavior)
                typing_delay = random.uniform(5, 10)
                print(f"Simulating user thinking for {typing_delay:.1f}s...")
                time.sleep(typing_delay)

                # Type and send
                textarea.clear()
                textarea.send_keys(user_input)
                textarea.send_keys(Keys.RETURN)
                
                # Wait for new message
                current_count = len(msgs)
                try:
                    # Wait for message count to increase
                    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".msg")) > current_count)
                except:
                    print("Timeout waiting for response.")
                    
                # Reading time
                reading_delay = random.uniform(3, 6)
                print(f"Simulating user reading for {reading_delay:.1f}s...")
                time.sleep(reading_delay)
            
            if task_completed:
                # DOM Verification
                # We wait a bit to ensure the DOM is updated
                time.sleep(2)
                page_source = driver.page_source
                if verification.lower() in page_source.lower():
                    print(f"✅ Verification PASSED: Found '{verification}' in DOM.")
                else:
                    print(f"❌ Verification FAILED: Did not find '{verification}' in DOM.")
            else:
                print("❌ Task failed to complete within turn limit.")
                
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("Cleaning up...")
        if driver:
            driver.quit()
        if backend_proc:
            print("Terminating backend...")
            backend_proc.terminate()
        if frontend_proc:
            print("Terminating frontend...")
            frontend_proc.terminate()

if __name__ == "__main__":
    run_test()
