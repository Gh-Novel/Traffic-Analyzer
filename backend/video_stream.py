import cv2
import sys

def print_error(e):
    print(f"Error: {e}")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Args: {e.args}")

if len(sys.argv) != 2:
    print("Error: URL argument is missing.")
    sys.exit(1)

url = sys.argv[1]

try:
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print("Error: Could not open video stream.")
        sys.exit(1)

    while True:
        ret, frame = cap.read()
        if ret:
            cv2.imshow('frame', frame)
        else:
            print("Error: Couldn't read frame.")
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print_error(e)

finally:
    if 'cap' in locals():
        cap.release()
    cv2.destroyAllWindows()
