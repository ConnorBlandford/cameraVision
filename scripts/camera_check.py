import cv2
import time

def list_ports():
    """Checks the first 10 indexes to see if a camera is available."""
    is_working = []
    print("\n[SYSTEM] Scanning for USB cameras...")
    for dev in range(10):
        cap = cv2.VideoCapture(dev, cv2.CAP_DSHOW) # CAP_DSHOW for faster initialization on Windows
        if cap.isOpened():
            is_working.append(dev)
            cap.release()
    return is_working

def run_camera_check():
    available_ports = list_ports()

    if not available_ports:
        print("[ERROR] No USB cameras detected. Check connections.")
        return

    print(f"[INFO] Available Camera Ports: {available_ports}")
    
    try:
        selection = int(input("Select a port index to test: "))
        if selection not in available_ports:
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a valid integer.")
        return

    # Initialize capture
    cap = cv2.VideoCapture(selection)
    
    if not cap.isOpened():
        print(f"[ERROR] Could not open camera on port {selection}.")
        return

    print(f"\n[SUCCESS] Streaming Port {selection} at 10Hz.")
    print("Press 'q' to exit the stream.")

    try:
        while True:
            start_time = time.time()

            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to grab frame.")
                break

            # Display the resulting frame
            cv2.imshow(f"Camera Port {selection} - 10Hz Test", frame)

            # 10Hz Logic: 1 second / 10 = 100ms
            # cv2.waitKey returns the key pressed; we use it to handle the delay
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Precise timing to maintain 10Hz
            elapsed = (time.time() - start_time) * 1000
            delay = max(1, int(100 - elapsed))
            time.sleep(delay / 1000.0)

    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        print("[SYSTEM] Camera released and windows closed.")

if __name__ == "__main__":
    run_camera_check()