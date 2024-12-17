import math
import numpy as np
import cv2
import time

def detect_center(x, y, w, h):
    """Calculate the center of a rectangle."""
    x1 = int(w / 2)
    y1 = int(h / 2)
    cx = x + x1
    cy = y + y1
    return cx, cy

def record_passing(number, time, add_total=False):
    """Saves the passing time in file"""
    if add_total:
        with open('data.txt', 'a') as file:
            file.write(f"Total count is {number}")

    else:
        with open("./data.txt", "a") as file:
            file.write(f"Car {number} crossed the line at {time}\n")

def is_same_car(new_center, tracked_cars, max_distance=30):
    """Determine if the car is the same or new car"""
    for car_id, (old_center, has_crossed_line) in tracked_cars.items():
        distance = math.sqrt((new_center[0] - old_center[0]) ** 2 + (new_center[1] - old_center[1]) ** 2)
        if distance < max_distance:
            return car_id
    return None

def count_cars(video_stream, interval_t=15):

    cap = cv2.VideoCapture(video_stream)

    backgroundObject = cv2.createBackgroundSubtractorMOG2(history=50, detectShadows=False)

    car_count = 0
    tracked_cars = {}  # List of tracked cars (each car is a tuple of (center, has_crossed_line))
    next_car_id = 1
    kernel = np.ones((3, 3), np.uint8) # Structure for doing morphological transformations


    strat_time = time.time()

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        mask = backgroundObject.apply(frame)

        # Apply binary thresholding to the mask, setting pixels with values above 90 to 255
        _, mask = cv2.threshold(mask, 90, 255, cv2.THRESH_BINARY)

        # Apply erosion to the mask to remove small white noise
        mask = cv2.erode(mask, kernel, iterations=2)

        # Apply dilation to the mask to enlarge the remaining white regions (foreground objects) after erosion
        mask = cv2.dilate(mask, kernel, iterations=4)


        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Setting crossing line position, Y-coordinate of the line
        line_position = int(frame.shape[0] * 0.7)

        new_tracked_cars = {}

        for contour in contours:
                # Get bounding box of the contour
                x, y, w, h = cv2.boundingRect(contour)

                area = cv2.contourArea(contour)
                if area > 3500: # Filtering small objects

                    # Getting box center coordinates
                    cx, cy = detect_center(x, y, w, h)

                    # Checking if the car is previously detected
                    car_id = is_same_car((cx, cy), tracked_cars)

                    if car_id is not None:
                        # Update cars position
                        _, has_crossed_line = tracked_cars[car_id]
                        new_tracked_cars[car_id] = ((cx, cy), has_crossed_line)

                        # Check whether car has crossed the line
                        if not has_crossed_line and tracked_cars[car_id][0][1] <= line_position <= cy:
                            car_count += 1
                            cv2.line(frame, (0, line_position), (frame.shape[1], line_position), (0, 255, 0), 2)
                            new_tracked_cars[car_id] = ((cx, cy), True)

                            timestamp = time.time()  # Get current time in seconds since the epoch
                            local_time = time.localtime(timestamp)  # Convert timestamp to local time struct
                            passing_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)

                            # Record the data in the file
                            record_passing(car_count, passing_time)

                    else:
                        # Add the car to detected cars
                        new_tracked_cars[next_car_id] = ((cx, cy), False)
                        next_car_id += 1


                    # Draw bounding box and center point
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

        tracked_cars = new_tracked_cars


        # Draw the counting line
        cv2.line(frame, (0, line_position), (frame.shape[1], line_position), (255, 0, 0), 2)

        # Display car count on the frame
        cv2.putText(frame, f"Car Count: {car_count}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Convert mask to BGR for stacking
        mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        # Stack original frame and mask
        stacked = np.hstack((frame, mask_colored))
        cv2.imshow("Result", cv2.resize(stacked, None, fx=0.55, fy=0.55))

        passed_time = time.time() - strat_time
        if passed_time >= interval_t:
            break

        if cv2.waitKey(1) == 27:
            break

    record_passing(car_count, _, True)

    cv2.destroyAllWindows()
    cap.release()

